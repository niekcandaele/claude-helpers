#!/usr/bin/env python3
"""Build the isolated working state for one trial.

Isolation is the part that is easy to get wrong, so it is all in one place, and
the two harnesses are isolated the same way:

* the workspace is built from scratch by the fixture's build.sh and is the only
  directory the harness can see. Two harnesses mean two work directories and
  two workspace builds — nothing is reused, and the fixture's determinism is
  what makes them comparable;
* HOME is overridden alongside the harness's own config directory. Overriding
  CODEX_HOME alone still lets Codex discover skills installed under the real
  ~/.agents/skills, which would put skills the case never staged in front of
  the harness;
* the harness config is generated, never copied, so the maintainer's model,
  reasoning effort, trusted-project list and synced skill catalog cannot leak
  in;
* the credential file is symlinked, never copied, so no credential material is
  ever written under the evaluation state directory;
* grader answers — the case's expected_behavior, the expectations/ files and
  the fixture manifest — are kept out of the workspace, and a leak check
  refuses to continue if any of them turns up there.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import uuid

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cases as cases_module  # noqa: E402
import preflight as preflight_module  # noqa: E402

ROOT = cases_module.ROOT
CONFIG_DIR = ROOT / "evals" / "config"
BASE_CONFIG = CONFIG_DIR / "base.yaml"
PROVIDERS_DIR = CONFIG_DIR / "providers"
DOUBLE_PROVIDER = ROOT / "evals" / "providers" / "double.mjs"

# `sonnet` is a mutable alias: it names a tier, not a build. That is precisely
# why the manifest records the requested name verbatim *and* the resolved model
# ids the harness reports back.
DEFAULT_MODELS = {"codex": "gpt-6-astra", "claude-code": "sonnet"}
MODEL_ENV_VARS = {
    "codex": "SKILL_EVAL_CODEX_MODEL",
    "claude-code": "SKILL_EVAL_CLAUDE_MODEL",
}


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


def new_evaluation_id(
    case_id: str, harness: str, now: dt.datetime | None = None, *, distinguish: bool = False
) -> str:
    """The trial directory name, which is also the trial's identity.

    SKILL_EVAL_EVALUATION_ID pins it; the tests use that to prove a second
    trial refuses to overwrite the first. When more than one harness is
    selected the harness is appended even to a pinned id, so two harnesses can
    never write into one directory.
    """
    pinned = os.environ.get("SKILL_EVAL_EVALUATION_ID")
    if pinned:
        return f"{pinned}-{harness}" if distinguish else pinned
    now = now or dt.datetime.now(dt.timezone.utc)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{case_id}-{harness}"


def requested_model(harness: str = "codex") -> str:
    return os.environ.get(MODEL_ENV_VARS[harness]) or DEFAULT_MODELS[harness]


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


CLAUDE_SETTINGS = {
    # A claude.ai-synced catalog is remote, personal and non-deterministic. It
    # would silently put the maintainer's skills in front of the harness, and
    # nothing downstream could tell that it had.
    "syncClaudeAiSkills": False,
    # The harness must not attribute anything it does in the workspace.
    "includeCoAuthoredBy": False,
    # The config directory is thrown away with the work directory anyway.
    "cleanupPeriodDays": 1,
}


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
        # A test seam, beside SKILL_EVAL_CASES_DIR and SKILL_EVAL_EVALUATION_ID:
        # it makes the double report a resolved model identity, so both halves
        # of the manifest's model contract can be checked without credentials.
        resolved = os.environ.get("SKILL_EVAL_DOUBLE_MODEL_USAGE")
        if resolved:
            config["modelUsage"] = {name: {} for name in resolved.split(",")}
    elif mode == "error":
        config["message"] = argument or "harness failed"
    elif mode != "empty":
        raise PrepareError(f"unknown provider double mode '{mode}'; use respond, error or empty")
    return {"id": f"file://{DOUBLE_PROVIDER}", "label": "double", "config": config}


def provider_block(
    case: cases_module.Case,
    harness: str,
    work: pathlib.Path,
    workspace: pathlib.Path,
    session_id: str,
) -> dict:
    """The one provider entry for this harness, with placeholders filled in."""
    template = PROVIDERS_DIR / f"{harness}.yaml"
    if not template.is_file():
        raise PrepareError(f"no provider template for harness '{harness}' at {template}")
    rendered = (
        template.read_text(encoding="utf-8")
        .replace("${SKILL_EVAL_CODEX_MODEL}", requested_model("codex"))
        .replace("${SKILL_EVAL_CLAUDE_MODEL}", requested_model("claude-code"))
        .replace("${WORKSPACE}", str(workspace))
        .replace("${WORK}", str(work))
        .replace("${ROOT}", str(ROOT))
        .replace("${SKILL}", case.skill)
        .replace("${SESSION_ID}", session_id)
    )
    blocks = yaml.safe_load(rendered)
    if not isinstance(blocks, list) or len(blocks) != 1:
        raise PrepareError(f"{template} must hold exactly one provider block")
    return blocks[0]


def render_config(
    case: cases_module.Case,
    work: pathlib.Path,
    workspace: pathlib.Path,
    *,
    arm: str = "candidate",
    harness: str = "codex",
    session_id: str = "00000000-0000-0000-0000-000000000000",
    provider_double: str | None = None,
    prompt_override: str | None = None,
    description: str | None = None,
    include_asserts: bool = True,
) -> dict:
    config = yaml.safe_load(BASE_CONFIG.read_text(encoding="utf-8"))
    config["providers"] = [
        _double_provider_block(case, provider_double)
        if provider_double
        else provider_block(case, harness, work, workspace, session_id)
    ]

    config["tests"] = [
        {
            "description": description or case.id,
            "vars": {
                "request": prompt_override
                or cases_module.compose_prompt(case, arm, harness=harness),
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


def provider_configs(case: cases_module.Case, harnesses: list[str]) -> dict[str, dict]:
    """Each selected harness's provider config, for preflight to inspect.

    Rendered against a throwaway path: preflight only reads the keys, and it
    has to answer before a work directory exists.
    """
    placeholder = pathlib.Path(tempfile.gettempdir()) / "skill-eval-unrendered"
    configs = {}
    for harness in harnesses:
        block = provider_block(case, harness, placeholder, placeholder / "workspace", "preflight")
        configs[harness] = block.get("config") or {}
    return configs


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


INJECTED_INSTRUCTION_NAMES = ("AGENTS.md", "CLAUDE.md", ".claude", ".codex")


def instruction_leaks(directory: pathlib.Path) -> list[str]:
    """Instruction files the case never intended, anywhere under a directory."""
    return [
        str(path.relative_to(directory))
        for path in sorted(directory.rglob("*"))
        if path.name in INJECTED_INSTRUCTION_NAMES
    ]


def _stage_codex(work: pathlib.Path, workspace: pathlib.Path, skill: pathlib.Path) -> dict:
    codex_dir = work / "codex-home"
    for directory in (codex_dir / "skills", codex_dir / "sessions"):
        directory.mkdir(parents=True)

    shutil.copytree(skill, codex_dir / "skills" / skill.name)

    real_auth = preflight_module.codex_home(dict(os.environ)) / "auth.json"
    if real_auth.is_file():
        (codex_dir / "auth.json").symlink_to(real_auth)

    (codex_dir / "config.toml").write_text(
        _render_config_toml(workspace, requested_model("codex")), encoding="utf-8"
    )
    return {"harness_home": codex_dir, "transcripts": codex_dir / "sessions"}


def _stage_claude_code(
    work: pathlib.Path, workspace: pathlib.Path, skill: pathlib.Path, *, verify_auth: bool
) -> dict:
    claude_dir = work / "claude-home"
    # An empty projects/ is the concrete "fresh conversation" check: the
    # transcript this trial writes is the only one that can be in there.
    for directory in (claude_dir / "skills", claude_dir / "projects"):
        directory.mkdir(parents=True)

    shutil.copytree(skill, claude_dir / "skills" / skill.name)

    # Always a symlink, even when the target does not exist: the shape of the
    # trial's config directory must not depend on whether this machine happens
    # to be logged in, and a dangling link fails loudly at the authentication
    # proof below rather than quietly looking like a copy.
    real_config = preflight_module.claude_config_dir(dict(os.environ))
    (claude_dir / ".credentials.json").symlink_to(real_config / ".credentials.json")

    (claude_dir / "settings.json").write_text(
        json.dumps(CLAUDE_SETTINGS, indent=2) + "\n", encoding="utf-8"
    )

    if verify_auth:
        env = dict(os.environ)
        env["CLAUDE_CONFIG_DIR"] = str(claude_dir)
        env["HOME"] = str(work / "home")
        status, reason = preflight_module.claude_auth_status(env)
        if status is None or not status.get("loggedIn") or status.get("authMethod") != "claude.ai":
            raise PrepareError(
                "the isolated Claude Code config dir is not authenticated — the credential "
                f"symlink did not take effect ({reason or 'authMethod ' + repr((status or {}).get('authMethod'))})"
            )

    return {"harness_home": claude_dir, "transcripts": claude_dir / "projects"}


STAGERS = {"codex": _stage_codex, "claude-code": _stage_claude_code}


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
    if harness not in STAGERS:
        raise PrepareError(f"harness '{harness}' cannot be prepared")

    work = work_dir() / evaluation_id
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    workspace = work / "workspace"
    home = work / "home"
    home.mkdir(parents=True)
    results_db = promptfoo_home()
    results_db.mkdir(parents=True, exist_ok=True)

    # Promptfoo resolves an optional provider SDK from the directory holding
    # the config, and the config has to live beside the trial it configures.
    # A link back to the repository's install is what keeps both true.
    (work / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)

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

    session_id = str(uuid.uuid4())
    staged = STAGERS[harness](
        work,
        workspace,
        source_skill,
        **({"verify_auth": not provider_double} if harness == "claude-code" else {}),
    )

    config = render_config(
        case,
        work,
        workspace,
        arm=arm,
        harness=harness,
        session_id=session_id,
        provider_double=provider_double,
        prompt_override=prompt_override,
        description=description,
        include_asserts=include_asserts,
    )
    config_path = work / "promptfooconfig.generated.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    leaks = leak_check(case, workspace)
    injected = instruction_leaks(workspace) + instruction_leaks(staged["harness_home"])
    if leaks or injected:
        raise PrepareError(
            "grader answers or unintended instructions leaked into the trial:\n  - "
            + "\n  - ".join(leaks + [f"{name} was staged into the harness's view" for name in injected])
        )

    return {
        "work": work,
        "workspace": workspace,
        "home": home,
        "harness": harness,
        "harness_home": staged["harness_home"],
        "transcripts": staged["transcripts"],
        "session_id": session_id,
        "promptfoo_home": results_db,
        "config": config_path,
        "config_data": config,
        "staged_skill": staged["harness_home"] / "skills" / case.skill / "SKILL.md",
        "fixture_head": fixture_head,
        "prompt": config["tests"][0]["vars"]["request"],
    }


def check_config() -> int:
    """Render every case's config, per declared harness, and let Promptfoo
    validate the real thing.

    evals/config/base.yaml is a template — validating it directly would only
    tell you that `${SKILL_EVAL_CODEX_MODEL}` is an unknown model. What has to
    be valid is what the generator produces, for every harness the case claims,
    so a broken provider block is caught with no model call.
    """
    failures = 0
    checked = 0
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases_module.discover():
            for harness in case.harnesses:
                if harness not in STAGERS:
                    continue
                checked += 1
                work = pathlib.Path(tmp) / f"{case.id}-{harness}"
                config = render_config(case, work, work / "workspace", harness=harness)
                rendered = pathlib.Path(tmp) / f"{case.id}-{harness}.yaml"
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
                        f"✗ {case.path} ({harness}): the generated Promptfoo config is invalid\n"
                        f"    → {result.stdout.strip() or result.stderr.strip()}",
                        file=sys.stderr,
                    )
    if failures:
        return 1
    print(f"✓ {checked} generated Promptfoo config(s) valid")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case")
    parser.add_argument("--harness", default="codex")
    parser.add_argument("--provider-double")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="render every case's config, per harness, and validate it with the pinned CLI",
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
    try:
        paths = prepare(
            case,
            new_evaluation_id(case.id, args.harness),
            harness=args.harness,
            provider_double=args.provider_double,
        )
    except PrepareError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    print(paths["config"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
