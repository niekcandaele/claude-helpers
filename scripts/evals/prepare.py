#!/usr/bin/env python3
"""Build the isolated working state for one trial.

Isolation is the part that is easy to get wrong, so it is all in one place:

* the workspace is built from scratch by the fixture's build.sh and is the only
  directory the harness can see;
* HOME **and** CODEX_HOME are both overridden — overriding CODEX_HOME alone
  still lets Codex discover skills installed under the real ~/.agents/skills,
  which would put skills the case never staged in front of the harness;
* the Codex config is generated, never copied, so the maintainer's model,
  reasoning effort and trusted-project list cannot leak in;
* auth.json is symlinked, never copied, so no credential material is ever
  written under the evaluation state directory;
* grader answers — the case's expected_behavior, the expectations/ files and
  the fixture manifest — are kept out of the workspace, and a leak check
  refuses to continue if any of them turns up there.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cases as cases_module  # noqa: E402

ROOT = cases_module.ROOT
BASE_CONFIG = ROOT / "evals" / "config" / "base.yaml"
DOUBLE_PROVIDER = ROOT / "evals" / "providers" / "double.mjs"

DEFAULT_MODEL = "gpt-6-astra"


class PrepareError(Exception):
    """Preparation failed before any inference could happen."""


def state_dir() -> pathlib.Path:
    override = os.environ.get("SKILL_EVAL_STATE_DIR")
    if override:
        return pathlib.Path(override)
    xdg = os.environ.get("XDG_STATE_HOME")
    base = pathlib.Path(xdg) if xdg else pathlib.Path.home() / ".local" / "state"
    return base / "skills-evals"


def runs_dir() -> pathlib.Path:
    return state_dir() / "runs"


def work_dir() -> pathlib.Path:
    return state_dir() / "work"


def promptfoo_home() -> pathlib.Path:
    """Where Promptfoo keeps its results database.

    Shared by every trial in one state directory, and never the maintainer's
    personal ~/.promptfoo: `just eval-view` has to find the trials it just
    saved, and a per-trial database dies with the ephemeral work directory.
    """
    return state_dir() / "promptfoo-home"


def new_evaluation_id(case_id: str, harness: str, now: dt.datetime | None = None) -> str:
    # SKILL_EVAL_EVALUATION_ID pins the trial directory name; the tests use it
    # to prove that a second trial refuses to overwrite the first.
    pinned = os.environ.get("SKILL_EVAL_EVALUATION_ID")
    if pinned:
        return pinned
    now = now or dt.datetime.now(dt.timezone.utc)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{case_id}-{harness}"


def requested_model() -> str:
    return os.environ.get("SKILL_EVAL_CODEX_MODEL") or DEFAULT_MODEL


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render_config_toml(workspace: pathlib.Path, model: str) -> str:
    return (
        "# Generated for one evaluation trial. Never copied from the maintainer's\n"
        "# ~/.codex/config.toml — that file carries a different model, reasoning\n"
        "# effort and dozens of trusted-project entries.\n"
        f'model = "{model}"\n'
        'model_reasoning_effort = "medium"\n'
        'approval_policy = "never"\n'
        'sandbox_mode = "read-only"\n'
        "\n"
        f'[projects."{workspace}"]\n'
        'trust_level = "trusted"\n'
    )


def absolutize_asserts(case: cases_module.Case) -> list[dict]:
    """Copy the case's assertions with file:// module paths made absolute.

    The generated config lives in the work directory, so a path relative to the
    case directory would resolve against the wrong root.
    """
    resolved = []
    for entry in case.asserts:
        entry = dict(entry)
        value = entry.get("value")
        if isinstance(value, str) and value.startswith("file://"):
            target = (case.dir / value[len("file://") :]).resolve()
            entry["value"] = f"file://{target}"
        resolved.append(entry)
    return resolved


def _double_provider_block(case: cases_module.Case, spec: str) -> dict:
    mode, _, argument = spec.partition(":")
    config: dict = {"mode": mode, "id": f"double:{mode}"}
    if mode == "respond":
        if not argument:
            raise PrepareError(
                "--provider-double respond needs a file: respond:<path to a response file>"
            )
        config["responseFile"] = str(pathlib.Path(argument).resolve())
        # Promptfoo's skill-used assertion reads objects with a `name`.
        config["skillCalls"] = [{"name": case.skill, "source": "provider-double"}]
    elif mode == "error":
        config["message"] = argument or "harness failed"
    elif mode != "empty":
        raise PrepareError(f"unknown provider double mode '{mode}'; use respond, error or empty")
    return {"id": f"file://{DOUBLE_PROVIDER}", "label": "double", "config": config}


def render_config(
    case: cases_module.Case,
    work: pathlib.Path,
    workspace: pathlib.Path,
    *,
    arm: str = "candidate",
    harness: str = "codex",
    provider_double: str | None = None,
    prompt_override: str | None = None,
    description: str | None = None,
    include_asserts: bool = True,
) -> dict:
    template = BASE_CONFIG.read_text(encoding="utf-8")
    rendered = (
        template.replace("${SKILL_EVAL_CODEX_MODEL}", requested_model())
        .replace("${WORKSPACE}", str(workspace))
        .replace("${WORK}", str(work))
    )
    config = yaml.safe_load(rendered)

    if provider_double:
        config["providers"] = [_double_provider_block(case, provider_double)]

    config["tests"] = [
        {
            "description": description or case.id,
            "vars": {
                "request": prompt_override or cases_module.compose_prompt(case, arm),
                "fixtureManifest": str(case.fixture_manifest()),
            },
            # Assertions recorded with weight 0 are evidence, not criteria; the
            # threshold makes Promptfoo's verdict agree with that.
            "threshold": 1,
            "metadata": {
                "case_id": case.id,
                "skill": case.skill,
                "kind": case.kind,
                "harness": harness,
                "arm": arm,
                "repetition_index": 0,
            },
            "assert": absolutize_asserts(case) if include_asserts else [],
        }
    ]
    return config


def provider_config(config: dict) -> dict:
    providers = config.get("providers") or []
    if not providers:
        return {}
    return providers[0].get("config") or {}


LEAK_SKIP_DIRS = {".git"}


def leak_check(case: cases_module.Case, workspace: pathlib.Path) -> list[str]:
    """Anything in the workspace that would hand the answer to the harness."""
    expected = " ".join(str(case.data.get("expected_behavior", "")).split())
    needles = {
        case.id: "the case id",
        "manifest.json": "the fixture manifest filename",
        "expected_behavior": "the case's expected_behavior key",
    }
    if len(expected) >= 40:
        needles[expected[:40]] = "the case's expected_behavior text"
    for name in ("acceptable.md", "unacceptable.md"):
        needles[name] = f"the grader calibration file {name}"

    found = []
    for path in workspace.rglob("*"):
        if not path.is_file() or any(part in LEAK_SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for needle, what in needles.items():
            if needle in text or needle in path.name:
                found.append(f"{path.relative_to(workspace)} contains {what}")
    return found


def prepare(
    case: cases_module.Case,
    evaluation_id: str,
    *,
    harness: str = "codex",
    arm: str = "candidate",
    provider_double: str | None = None,
    prompt_override: str | None = None,
    description: str | None = None,
    include_asserts: bool = True,
) -> dict:
    """Build work/<evaluation-id>/ and return the paths the rest of the trial uses."""
    work = work_dir() / evaluation_id
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    workspace = work / "workspace"
    home = work / "home"
    codex_dir = work / "codex-home"
    results_db = promptfoo_home()
    results_db.mkdir(parents=True, exist_ok=True)
    for directory in (home, codex_dir / "skills", codex_dir / "sessions"):
        directory.mkdir(parents=True)

    build = case.fixture_build()
    result = subprocess.run(
        ["bash", str(build), str(workspace)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        raise PrepareError(
            f"fixture '{case.fixture}' failed to build (exit {result.returncode})\n{result.stderr.strip()}"
        )
    fixture_head = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""

    source_skill = cases_module.skill_dir(case.skill)
    if source_skill is None:
        raise PrepareError(f"skill '{case.skill}' does not exist on disk")
    staged_skill = codex_dir / "skills" / case.skill
    shutil.copytree(source_skill, staged_skill)

    real_auth = pathlib.Path.home() / ".codex" / "auth.json"
    if real_auth.is_file():
        (codex_dir / "auth.json").symlink_to(real_auth)

    (codex_dir / "config.toml").write_text(
        _render_config_toml(workspace, requested_model()), encoding="utf-8"
    )

    config = render_config(
        case,
        work,
        workspace,
        arm=arm,
        harness=harness,
        provider_double=provider_double,
        prompt_override=prompt_override,
        description=description,
        include_asserts=include_asserts,
    )
    config_path = work / "promptfooconfig.generated.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    leaks = leak_check(case, workspace)
    if leaks:
        raise PrepareError(
            "grader answers leaked into the trial workspace:\n  - " + "\n  - ".join(leaks)
        )

    return {
        "work": work,
        "workspace": workspace,
        "home": home,
        "codex_home": codex_dir,
        "promptfoo_home": results_db,
        "config": config_path,
        "config_data": config,
        "staged_skill": staged_skill / "SKILL.md",
        "fixture_head": fixture_head,
        "prompt": config["tests"][0]["vars"]["request"],
    }


def check_config() -> int:
    """Render every case's config and let Promptfoo validate the real thing.

    evals/config/base.yaml is a template — validating it directly would only
    tell you that `${SKILL_EVAL_CODEX_MODEL}` is an unknown model. What has to
    be valid is what the generator produces.
    """
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases_module.discover():
            work = pathlib.Path(tmp) / case.id
            config = render_config(case, work, work / "workspace")
            rendered = pathlib.Path(tmp) / f"{case.id}.yaml"
            rendered.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            result = subprocess.run(
                ["npx", "--no-install", "promptfoo", "validate", "config", "-c", str(rendered)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failures += 1
                print(
                    f"✗ {case.path}: the generated Promptfoo config is invalid\n"
                    f"    → {result.stdout.strip() or result.stderr.strip()}",
                    file=sys.stderr,
                )
    if failures:
        return 1
    print(f"✓ {len(cases_module.discover())} generated Promptfoo config(s) valid")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case")
    parser.add_argument("--harness", default="codex")
    parser.add_argument("--provider-double")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="render every case's config and validate it with the pinned Promptfoo CLI",
    )
    parser.add_argument(
        "--promptfoo-home",
        action="store_true",
        help="print the results database directory the viewer must read",
    )
    args = parser.parse_args(argv)

    if args.promptfoo_home:
        print(promptfoo_home())
        return 0
    if args.check_config:
        return check_config()
    if not args.case:
        parser.error("--case is required unless --check-config is given")

    case = cases_module.load(args.case)
    paths = prepare(
        case,
        new_evaluation_id(case.id, args.harness),
        harness=args.harness,
        provider_double=args.provider_double,
    )
    print(paths["config"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
