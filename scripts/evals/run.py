#!/usr/bin/env python3
"""Evaluate one case on one harness and save the report.

preflight → prepare → preview → execute → summarize. The preview prints the
whole planned cost on one screen and then proceeds: it is there so the
maintainer can see what a trial will spend, not to ask permission twice.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cases as cases_module  # noqa: E402
import execute as execute_module  # noqa: E402
import prepare as prepare_module  # noqa: E402
import preflight as preflight_module  # noqa: E402
import summarize as summarize_module  # noqa: E402

# Measured on an isolated HOME and CODEX_HOME: whatever the case stages, Codex
# also offers these. They are unavoidable harness-provided context, not a
# defect — but anything else appearing beside them means isolation regressed.
HARNESS_PROVIDED_SKILLS = [
    "imagegen",
    "openai-docs",
    "plugin-creator",
    "skill-creator",
    "skill-installer",
    "deep-research-work:deep-research",
    "plugin-management:plugin-management",
]

# Asking for JSON rather than prose: a line-by-line reading of an English
# answer turns stray words into phantom skills, and a phantom skill reads as an
# isolation failure that never happened.
PROBE_PROMPT = (
    "Reply with a single JSON object and no other text, of the form "
    '{"skills": [...], "instruction_files": [...]}. "skills" holds the exact '
    'name of every skill available to you. "instruction_files" holds the path '
    "of every instruction file you were given."
)


def preview(case: cases_module.Case, harness: str, paths: dict, run_dir: pathlib.Path, double: str | None) -> None:
    lines = [
        "",
        "── planned evaluation ─────────────────────────────────────────",
        f"  case                {case.id}",
        f"  skill               {case.skill}",
        f"  kind                {case.kind}",
        f"  harness             {harness}" + (f" (provider double: {double})" if double else ""),
        f"  requested model     {prepare_module.requested_model()}",
        "  arms                1 (candidate)",
        "  repetitions         1",
        "  concurrency         1",
        "  model-judge passes  0",
        "  caching             disabled",
        f"  trial timeout       {execute_module.timeout_seconds()}s",
        f"  workspace           {paths['workspace']}",
        f"  results             {run_dir}",
        "───────────────────────────────────────────────────────────────",
        "",
    ]
    print("\n".join(lines))


def _auth_record(route: str, double: str | None) -> dict:
    if double:
        return {
            "route": "provider-double",
            "auth_mode": None,
            "auth_mode_reason": "a provider double stood in for the harness; no credentials were used",
            "source": None,
        }
    return {
        "route": route,
        "auth_mode": "chatgpt",
        "source": str(preflight_module.codex_home(dict(os.environ)) / "auth.json"),
    }


def trial(
    case: cases_module.Case,
    *,
    harness: str,
    provider_double: str | None,
    probe: bool = False,
) -> int:
    try:
        route = preflight_module.preflight(
            case, require_harness_auth=not provider_double
        )
    except preflight_module.PreflightError as exc:
        preflight_module.report(exc.failures)
        return 1

    suffix = "-probe" if probe else ""
    evaluation_id = prepare_module.new_evaluation_id(case.id, harness) + suffix
    run_dir = prepare_module.runs_dir() / evaluation_id
    if run_dir.exists():
        print(
            f"✗ {run_dir} already exists\n"
            "    → saved evidence is never overwritten; delete that trial directory "
            "or wait a second and evaluate again",
            file=sys.stderr,
        )
        return 1

    try:
        paths = prepare_module.prepare(
            case,
            evaluation_id,
            harness=harness,
            provider_double=provider_double,
            prompt_override=PROBE_PROMPT if probe else None,
            description=f"{case.id}-probe" if probe else None,
            include_asserts=not probe,
        )
    except prepare_module.PrepareError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1

    run_dir.mkdir(parents=True)
    preview(case, harness, paths, run_dir, provider_double)

    started = dt.datetime.now(dt.timezone.utc)
    monotonic = time.monotonic()
    execution = execute_module.execute(paths, run_dir)
    execution["timeout_s"] = execute_module.timeout_seconds()
    ended = dt.datetime.now(dt.timezone.utc)

    harness_skills = []
    isolation_intact = True
    if probe:
        harness_skills, isolation_intact = _write_probe_context(run_dir, case, paths)

    result = summarize_module.summarize(
        case,
        run_dir,
        paths,
        execution,
        {
            "evaluation_id": evaluation_id,
            "harness": harness,
            "arm": "candidate",
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "duration_ms": int((time.monotonic() - monotonic) * 1000),
            "auth": _auth_record(route, provider_double),
            "harness_provided_skills": harness_skills or HARNESS_PROVIDED_SKILLS,
        },
    )

    print(f"{result['status']}: {result['reason']}")
    print(f"  evidence   {run_dir}")
    print(f"  report     {run_dir / 'results.html'}")
    print("  viewer     just eval-view")

    if probe:
        # A probe grades nothing; what it can fail at is isolation.
        return 0 if isolation_intact and result["status"] != summarize_module.STATUS_EXECUTION_ERROR else 1
    return 0 if result["status"] == summarize_module.STATUS_PASSED else 1


def _write_probe_context(
    run_dir: pathlib.Path, case: cases_module.Case, paths: dict
) -> tuple[list[str], bool]:
    """Record what the harness actually had in front of it, and shout if a skill
    the case never staged turns up.

    Returns the harness-provided skills observed, and whether isolation held.
    """
    results_path = run_dir / "results.json"
    output = ""
    if results_path.is_file():
        data = json.loads(results_path.read_text(encoding="utf-8"))
        rows = data.get("results", {}).get("results", [])
        if rows:
            output = rows[0].get("response", {}).get("output") or ""

    catalog, instruction_files, parse_error = _parse_probe(output)

    expected = set(HARNESS_PROVIDED_SKILLS) | {case.skill}
    unexpected = sorted(set(catalog or []) - expected)
    context = {
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model_requested": prepare_module.requested_model(),
        "staged_skill": case.skill,
        "expected_harness_provided_skills": HARNESS_PROVIDED_SKILLS,
        "observed_catalog": catalog,
        "observed_catalog_reason": parse_error,
        "observed_instruction_files": instruction_files,
        "unexpected_entries": unexpected,
        "raw_response": output,
        "workspace": str(paths["workspace"]),
    }
    (run_dir / "harness-context.json").write_text(
        json.dumps(context, indent=2) + "\n", encoding="utf-8"
    )

    if unexpected:
        print(
            "⚠ the harness offered skills this case never staged: "
            + ", ".join(unexpected)
            + "\n    → isolation has regressed; check the HOME and CODEX_HOME overrides "
            "before trusting any result",
            file=sys.stderr,
        )
    return sorted(set(catalog or []) & set(HARNESS_PROVIDED_SKILLS)), not unexpected


def _parse_probe(output: str) -> tuple[list[str] | None, list[str] | None, str | None]:
    """The probe's catalog, its instruction files, and why they are missing."""
    text = output.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None, None, "the harness did not answer with a JSON object"
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        return None, None, f"the harness's JSON could not be parsed ({exc.msg})"
    skills = data.get("skills")
    files = data.get("instruction_files")
    if not isinstance(skills, list):
        return None, None, "the harness's answer carried no 'skills' list"
    return (
        [str(entry) for entry in skills],
        [str(entry) for entry in files] if isinstance(files, list) else None,
        None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", help="case id; the probe defaults to the first case")
    parser.add_argument("--harness", default="codex", choices=sorted(cases_module.SUPPORTED_HARNESSES))
    parser.add_argument(
        "--probe",
        action="store_true",
        help="one cheap call that records the effective skill catalog instead of grading",
    )
    parser.add_argument(
        "--provider-double",
        help="stand in for the harness: respond:<file>, error[:<message>], or empty",
    )
    args = parser.parse_args(argv)

    if args.case:
        case = cases_module.load(args.case)
    else:
        discovered = cases_module.discover()
        if not discovered:
            print("✗ no evaluation cases found\n    → add one under evals/cases/", file=sys.stderr)
            return 1
        case = discovered[0]

    return trial(
        case,
        harness=args.harness,
        provider_double=args.provider_double,
        probe=args.probe,
    )


if __name__ == "__main__":
    sys.exit(main())
