#!/usr/bin/env python3
"""Evaluate one case on one or more harnesses and save the reports.

preflight → prepare → preview → execute → summarize, once per selected harness,
serially. The preview prints the whole planned cost on one screen — every trial
it is about to run — and then proceeds: it is there so the maintainer can see
what an evaluation will spend, not to ask permission twice.

Results are kept per harness and are never combined. One harness passing says
nothing about the other, so this prints no aggregate figure and stores none.
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

# Measured on an isolated HOME and harness config directory: whatever the case
# stages, the harness also offers these. They are unavoidable harness-provided
# context, not a defect — and they vary by machine, so treat every list as a
# superset and never assert equality. What *is* a regression is a repository
# skill other than the staged one appearing beside them.
HARNESS_PROVIDED_SKILLS = {
    "codex": [
        "imagegen",
        "openai-docs",
        "plugin-creator",
        "skill-creator",
        "skill-installer",
        "deep-research-work:deep-research",
        "plugin-management:plugin-management",
    ],
    # Claude Code's own bundled catalog. What the pilot's probe reported is
    # narrower than what the harness actually ships: the harness enumerates its
    # skills poorly when asked, so this list is the observed answer and not a
    # promise. `disableBundledSkills` is the lever if it ever matters.
    "claude-code": ["code-review"],
}

# Asking for JSON rather than prose: a line-by-line reading of an English
# answer turns stray words into phantom skills, and a phantom skill reads as an
# isolation failure that never happened.
PROBE_PROMPT = (
    "Reply with a single JSON object and no other text, of the form "
    '{"skills": [...], "instruction_files": [...]}. "skills" holds the exact '
    'name of every skill available to you. "instruction_files" holds the path '
    "of every instruction file you were given."
)


class Planned:
    """One trial this invocation intends to run."""

    def __init__(self, harness: str, evaluation_id: str, double: str | None):
        self.harness = harness
        self.evaluation_id = evaluation_id
        self.double = double
        self.supported = True

    @property
    def run_dir(self) -> pathlib.Path:
        return prepare_module.runs_dir() / self.evaluation_id

    @property
    def work_dir(self) -> pathlib.Path:
        return prepare_module.work_dir() / self.evaluation_id


def preview(case: cases_module.Case, plans: list[Planned]) -> None:
    lines = [
        "",
        "── planned evaluation ─────────────────────────────────────────",
        f"  case                {case.id}",
        f"  skill               {case.skill}",
        f"  kind                {case.kind}",
        f"  trials              {len(plans)} (one per harness, run serially)",
        "",
    ]
    for index, plan in enumerate(plans, start=1):
        suffix = f" (provider double: {plan.double})" if plan.double else ""
        lines.append(f"  [{index}] harness         {plan.harness}{suffix}")
        if not plan.supported:
            lines.append("      not executed    the case does not declare this harness")
        else:
            lines.append(
                f"      requested model {prepare_module.requested_model(plan.harness)}"
            )
            lines.append(f"      workspace       {plan.work_dir / 'workspace'}")
        lines.append(f"      results         {plan.run_dir}")
    lines += [
        "",
        "  arms                1 (candidate)      repetitions   1",
        "  concurrency         1                  judge passes  0",
        f"  caching             disabled           trial timeout {execute_module.timeout_seconds()}s",
        "───────────────────────────────────────────────────────────────",
        "",
    ]
    print("\n".join(lines))


def _auth_record(harness: str, route: str, double: str | None) -> dict:
    if double:
        return {
            "route": "provider-double",
            "auth_method": None,
            "auth_method_reason": "a provider double stood in for the harness; no credentials were used",
            "api_provider": None,
            "subscription_type": None,
            "source": None,
        }
    env = dict(os.environ)
    if harness == "codex":
        return {
            "route": route,
            "auth_method": "chatgpt",
            "api_provider": "openai",
            "subscription_type": None,
            "source": str(preflight_module.codex_home(env) / "auth.json"),
        }
    # Deliberately not email, orgId or orgName: the trial's identity is the
    # subscription route, not the person holding it.
    status, _ = preflight_module.claude_auth_status(env)
    status = status or {}
    return {
        "route": route,
        "auth_method": status.get("authMethod"),
        "api_provider": status.get("apiProvider"),
        "subscription_type": status.get("subscriptionType"),
        "source": str(preflight_module.claude_config_dir(env) / ".credentials.json"),
    }


def parse_doubles(spec: str | None, harnesses: list[str]) -> dict[str, str | None]:
    """One double spec applied to every harness, or per-harness pairs.

    `respond:<file>` stands in for all of them; `codex=respond:<file>,
    claude-code=empty` gives each its own, which is how a mixed outcome can be
    reproduced without credentials.
    """
    if not spec:
        return {harness: None for harness in harnesses}
    pairs: dict[str, str | None] = {}
    per_harness = all(
        "=" in part and part.split("=", 1)[0] in cases_module.SUPPORTED_HARNESSES
        for part in spec.split(",")
        if part
    )
    if not per_harness:
        return {harness: spec for harness in harnesses}
    for part in spec.split(","):
        if not part:
            continue
        name, _, value = part.partition("=")
        pairs[name] = value
    missing = [harness for harness in harnesses if harness not in pairs]
    if missing:
        raise SystemExit(
            f"✗ --provider-double names no double for: {', '.join(missing)}\n"
            "    → give every selected harness one, or pass a single bare spec for all of them"
        )
    return {harness: pairs[harness] for harness in harnesses}


def run(
    case: cases_module.Case,
    *,
    harnesses: list[str],
    provider_double: str | None,
    probe: bool = False,
) -> int:
    doubles = parse_doubles(provider_double, harnesses)
    live = [harness for harness in harnesses if not doubles[harness]]

    try:
        routes = preflight_module.preflight(
            case,
            harnesses=harnesses,
            provider_configs=prepare_module.provider_configs(case, live),
            require_harness_auth=bool(live),
        )
    except preflight_module.PreflightError as exc:
        preflight_module.report(exc.failures)
        return 1
    except prepare_module.PrepareError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1

    suffix = "-probe" if probe else ""
    plans = []
    for harness in harnesses:
        evaluation_id = (
            prepare_module.new_evaluation_id(case.id, harness, distinguish=len(harnesses) > 1)
            + suffix
        )
        plan = Planned(harness, evaluation_id, doubles[harness])
        # A probe asks the harness what it can see; whether the case claims the
        # harness is beside the point.
        plan.supported = probe or harness in case.harnesses
        plans.append(plan)

    for plan in plans:
        if plan.run_dir.exists():
            print(
                f"✗ {plan.run_dir} already exists\n"
                "    → saved evidence is never overwritten; delete that trial directory "
                "or wait a second and evaluate again",
                file=sys.stderr,
            )
            return 1

    preview(case, plans)

    outcomes: list[tuple[Planned, dict]] = []
    for plan in plans:
        outcome = _one_trial(case, plan, routes[plan.harness], probe)
        if outcome is None:
            return 1
        outcomes.append((plan, outcome))

    return _report(outcomes, probe)


def _one_trial(
    case: cases_module.Case, plan: Planned, route: str, probe: bool
) -> dict | None:
    started = dt.datetime.now(dt.timezone.utc)
    plan.run_dir.mkdir(parents=True)

    trial = {
        "evaluation_id": plan.evaluation_id,
        "harness": plan.harness,
        "arm": "candidate",
        "started_at": started.isoformat(),
        "ended_at": started.isoformat(),
    }

    if not plan.supported:
        return summarize_module.save_unsupported(case, plan.run_dir, plan.harness, trial)

    try:
        paths = prepare_module.prepare(
            case,
            plan.evaluation_id,
            harness=plan.harness,
            provider_double=plan.double,
            prompt_override=PROBE_PROMPT if probe else None,
            description=f"{case.id}-probe" if probe else None,
            include_asserts=not probe,
        )
    except prepare_module.PrepareError as exc:
        print(f"✗ {plan.harness}: {exc}", file=sys.stderr)
        return None

    monotonic = time.monotonic()
    execution = execute_module.execute(paths, plan.run_dir)
    execution["timeout_s"] = execute_module.timeout_seconds()

    harness_skills: list[str] = []
    isolation_intact = True
    if probe:
        harness_skills, isolation_intact = _write_probe_context(plan, case, paths)

    trial["ended_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    trial["duration_ms"] = int((time.monotonic() - monotonic) * 1000)
    trial["auth"] = _auth_record(plan.harness, route, plan.double)
    trial["harness_provided_skills"] = harness_skills or HARNESS_PROVIDED_SKILLS[plan.harness]

    result = summarize_module.summarize(case, plan.run_dir, paths, execution, trial)
    result["isolation_intact"] = isolation_intact
    return result


def _report(outcomes: list[tuple[Planned, dict]], probe: bool) -> int:
    print("")
    width = max(len(plan.harness) for plan, _ in outcomes)
    for plan, result in outcomes:
        print(f"{plan.harness.ljust(width)}  {result['status']}: {result['reason']}")
        print(f"{' ' * width}  evidence   {plan.run_dir}")
    print(f"{' ' * width}  viewer     just eval-view")
    print(
        "\nResults are per harness. A result on one harness says nothing about the other.\n"
    )

    if probe:
        # A probe grades nothing; what it can fail at is isolation.
        return (
            0
            if all(
                result.get("isolation_intact")
                and result["status"] != summarize_module.STATUS_EXECUTION_ERROR
                for _, result in outcomes
            )
            else 1
        )
    return 0 if all(result["status"] == summarize_module.STATUS_PASSED for _, result in outcomes) else 1


def _write_probe_context(
    plan: Planned, case: cases_module.Case, paths: dict
) -> tuple[list[str], bool]:
    """Record what the harness actually had in front of it, and shout if a skill
    the case never staged turns up.

    Returns the harness-provided skills observed, and whether isolation held.
    """
    results_path = plan.run_dir / "results.json"
    output = ""
    if results_path.is_file():
        data = json.loads(results_path.read_text(encoding="utf-8"))
        rows = data.get("results", {}).get("results", [])
        if rows:
            output = rows[0].get("response", {}).get("output") or ""

    catalog, instruction_files, parse_error = _parse_probe(output)

    known = HARNESS_PROVIDED_SKILLS[plan.harness]
    expected = set(known) | {case.skill}
    unexpected = sorted(set(catalog or []) - expected)
    context = {
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "harness": plan.harness,
        "model_requested": prepare_module.requested_model(plan.harness),
        "staged_skill": case.skill,
        "expected_harness_provided_skills": known,
        "observed_catalog": catalog,
        "observed_catalog_reason": parse_error,
        "observed_instruction_files": instruction_files,
        "unexpected_entries": unexpected,
        "raw_response": output,
        "workspace": str(paths["workspace"]),
        "harness_home": str(paths["harness_home"]),
    }
    (plan.run_dir / "harness-context.json").write_text(
        json.dumps(context, indent=2) + "\n", encoding="utf-8"
    )

    if unexpected:
        print(
            f"⚠ {plan.harness} offered skills this case never staged: "
            + ", ".join(unexpected)
            + "\n    → the recorded catalog varies by machine, so add genuinely "
            "harness-provided entries to HARNESS_PROVIDED_SKILLS; a *repository* "
            "skill here means isolation has regressed",
            file=sys.stderr,
        )
    return sorted(set(catalog or []) & set(known)), not unexpected


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
    parser.add_argument(
        "--harness",
        default="codex",
        help="a harness name, a comma-separated list, or 'both'/'all'",
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="one cheap call per harness that records the effective skill catalog "
        "instead of grading",
    )
    parser.add_argument(
        "--provider-double",
        help="stand in for the harness: respond:<file>, error[:<message>] or empty, "
        "either bare for every harness or as <harness>=<spec> pairs",
    )
    args = parser.parse_args(argv)

    harnesses = cases_module.resolve_harnesses(args.harness)

    if args.case:
        case = cases_module.load(args.case)
    else:
        discovered = cases_module.discover()
        if not discovered:
            print("✗ no evaluation cases found\n    → add one under evals/cases/", file=sys.stderr)
            return 1
        case = discovered[0]

    return run(
        case,
        harnesses=harnesses,
        provider_double=args.provider_double,
        probe=args.probe,
    )


if __name__ == "__main__":
    sys.exit(main())
