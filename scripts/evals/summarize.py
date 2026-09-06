#!/usr/bin/env python3
"""Turn a finished trial into frozen, self-explaining evidence.

Every trial ends in exactly one status, and the three failure statuses are kept
apart on purpose: a harness that never ran tells you something different from a
harness that ran and got the answer wrong.

    passed             every required assertion passed
    assertion-failed   graded, and at least one required assertion failed
    execution-error    the harness errored, timed out, or never produced output
    ungraded           executed, but there was nothing to grade
    unsupported        the case does not declare this harness; nothing was executed

`unsupported` is a saved trial directory with no results file. It exists so a
harness the case never claimed leaves visible evidence of the gap instead of
silently vanishing from a two-harness comparison — and it never reads as a pass.

The trial directory is made read-only at the end. Viewer ratings and comments
live in Promptfoo's own database; the saved evidence cannot be edited to agree
with them.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cases as cases_module  # noqa: E402
import prepare as prepare_module  # noqa: E402

ROOT = cases_module.ROOT

STATUS_PASSED = "passed"
STATUS_ASSERTION_FAILED = "assertion-failed"
STATUS_EXECUTION_ERROR = "execution-error"
STATUS_UNGRADED = "ungraded"
STATUS_UNSUPPORTED = "unsupported"

# Promptfoo's ResultFailureReason: NONE=0, ASSERT=1, ERROR=2.
RESULT_FAILURE_ERROR = 2

MODEL_RESOLVED_REASONS = {
    "codex": "the Codex SDK does not report the backend-resolved model through Promptfoo",
    "claude-code": "the harness reported no modelUsage for this trial",
}

COST_BASIS = (
    "API-rate estimate. Execution used subscription authentication, so this is "
    "not an invoice and not remaining subscription quota."
)


def _command_version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip().splitlines()[0] if result.stdout.strip() else None


def _git(*args: str) -> str | None:
    return _command_version(["git", "-C", str(ROOT), *args])


def source_provenance() -> dict:
    porcelain = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True
    ).stdout
    diff = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "HEAD"], capture_output=True, text=True
    ).stdout
    import hashlib

    return {
        "revision": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(porcelain.strip()),
        "dirty_fingerprint": hashlib.sha256((porcelain + diff).encode("utf-8")).hexdigest(),
    }


def tool_versions() -> dict:
    manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    return {
        "promptfoo": manifest["dependencies"]["promptfoo"],
        "codex_sdk": manifest["dependencies"]["@openai/codex-sdk"],
        "codex_cli": _command_version(["codex", "--version"]),
        "claude_agent_sdk": manifest["dependencies"]["@anthropic-ai/claude-agent-sdk"],
        "claude_cli": _command_version(["claude", "--version"]),
        "node": _command_version(["node", "--version"]),
        "just": _command_version(["just", "--version"]),
    }


# A skill a person types is recorded by Claude Code as a command, not as a
# Skill tool call, so it never reaches the provider's skillCalls. Reading it
# back out of the saved transcript is how the same `skill-used` assertion gets
# an answer on both harnesses.
SLASH_INVOCATION = re.compile(r"<command-name>/([a-z0-9][a-z0-9-]*)</command-name>")


def skill_evidence(metadata: dict, transcript_dir: pathlib.Path) -> dict:
    """What the harness can show about which skills were loaded.

    The provider's own report is preferred. When it is empty the transcript is
    read instead, and when that is unavailable the answer is an empty list plus
    the reason it is empty — never a confident negative, because the assertion
    that consumes it is evidence rather than a criterion.
    """
    calls = metadata.get("skillCalls")
    if calls:
        return {"calls": calls, "source": "provider", "reason": None}

    files = sorted(transcript_dir.glob("*.jsonl")) if transcript_dir.is_dir() else []
    if not files:
        return {
            "calls": [],
            "source": None,
            "reason": "the harness reported no skill calls and saved no transcript to read them from",
        }

    names: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in SLASH_INVOCATION.findall(text):
            if name not in names:
                names.append(name)
        for entry in re.findall(r'"name"\s*:\s*"Skill"[^\n]*?"skill"\s*:\s*"([^"]+)"', text):
            if entry not in names:
                names.append(entry)
    if not names:
        return {
            "calls": [],
            "source": "transcript",
            "reason": "the transcript records no skill invocation",
        }
    return {
        "calls": [{"name": name, "source": "transcript"} for name in names],
        "source": "transcript",
        "reason": None,
    }


def _resolved_model(harness: str, metadata: dict) -> tuple[object, str | None]:
    """The model the harness says it actually used, and why it is missing.

    Claude Code keys its usage report by resolved model id, so the identity is
    recoverable even though the requested name is a mutable alias. Several keys
    means several models really were used, and collapsing them to one would be
    a lie the manifest cannot afford.
    """
    usage = metadata.get("modelUsage")
    if not isinstance(usage, dict) or not usage:
        return None, MODEL_RESOLVED_REASONS.get(harness, MODEL_RESOLVED_REASONS["codex"])
    names = sorted(usage)
    return (names[0] if len(names) == 1 else names), None


def _group_components(
    case: cases_module.Case, components: list[dict]
) -> list[tuple[dict | None, list[dict]]]:
    """Pair each case assertion with its result and that result's sub-results.

    Promptfoo flattens the sub-results a javascript assertion returns into the
    same list, immediately after their parent, and a sub-result may carry any
    metric name it likes. What it cannot carry is the case assertion's own
    `type` and `value`, so those are what a boundary is recognised by, walked in
    order.
    """
    expected = prepare_module.absolutize_asserts(case)
    groups: list[tuple[dict | None, list[dict]]] = [(None, []) for _ in expected]
    index = -1
    for component in components:
        found = component.get("assertion") or {}
        nxt = index + 1
        if (
            nxt < len(expected)
            and found.get("type") == expected[nxt].get("type")
            and found.get("value") == expected[nxt].get("value")
        ):
            index = nxt
            groups[index] = (component, [])
        elif index >= 0:
            groups[index][1].append(component)
    return groups


def classify(case: cases_module.Case, results: dict | None, execution: dict) -> dict:
    """One status, one sentence of reason, and a row per case assertion."""
    if execution.get("timed_out"):
        return {
            "status": STATUS_EXECUTION_ERROR,
            "reason": (
                f"the harness did not finish within {execution.get('timeout_s')} seconds, "
                "so nothing was graded"
            ),
            "assertions": [],
            "output": "",
        }

    if results is None:
        return {
            "status": STATUS_EXECUTION_ERROR,
            "reason": (
                f"promptfoo exited {execution.get('exit_code')} without writing a result file, "
                "so nothing was graded"
            ),
            "assertions": [],
            "output": "",
        }

    rows = results.get("results", {}).get("results", [])
    if not rows:
        return {
            "status": STATUS_EXECUTION_ERROR,
            "reason": "promptfoo produced no result rows, so nothing was graded",
            "assertions": [],
            "output": "",
        }

    row = rows[0]
    # failureReason 2 is Promptfoo's ERROR; 1 is ASSERT. `error` on the row is
    # also set for a plain assertion failure, so it cannot be the signal.
    error = row.get("response", {}).get("error") or row.get("error")
    if row.get("failureReason") == RESULT_FAILURE_ERROR or (
        row.get("failureReason") is None and error
    ):
        return {
            "status": STATUS_EXECUTION_ERROR,
            "reason": f"the harness failed before grading: {error or 'provider error'}",
            "assertions": [],
            "output": "",
        }

    output = row.get("response", {}).get("output") or ""
    if isinstance(output, str) and not output.strip():
        return {
            "status": STATUS_UNGRADED,
            "reason": "the harness returned no output, so no required assertion could reach a verdict",
            "assertions": [],
            "output": "",
        }

    components = (row.get("gradingResult") or {}).get("componentResults") or []
    groups = _group_components(case, components)
    assertion_rows = []
    for assertion, (component, children) in zip(case.asserts, groups):
        weight = assertion.get("weight", 1)
        assertion_rows.append(
            {
                "metric": assertion.get("metric"),
                "type": assertion.get("type"),
                "weight": weight,
                "required": weight != 0,
                "pass": None if component is None else bool(component.get("pass")),
                "score": None if component is None else component.get("score"),
                "reason": None if component is None else component.get("reason"),
                "components": [
                    {
                        "metric": (child.get("assertion") or {}).get("metric"),
                        "pass": bool(child.get("pass")),
                        "reason": child.get("reason"),
                    }
                    for child in children
                ],
            }
        )

    required = [row_ for row_ in assertion_rows if row_["required"]]
    graded = [row_ for row_ in required if row_["pass"] is not None]
    if not graded:
        return {
            "status": STATUS_UNGRADED,
            "reason": "no required assertion produced a verdict",
            "assertions": assertion_rows,
            "output": output,
        }

    failed = [row_ for row_ in graded if not row_["pass"]]
    if failed:
        names = ", ".join(str(row_["metric"] or row_["type"]) for row_ in failed)
        first = next((row_["reason"] for row_ in failed if row_["reason"]), "")
        return {
            "status": STATUS_ASSERTION_FAILED,
            "reason": f"{len(failed)} required assertion(s) failed ({names}): {first}",
            "assertions": assertion_rows,
            "output": output,
        }

    return {
        "status": STATUS_PASSED,
        "reason": f"all {len(graded)} required assertion(s) passed",
        "assertions": assertion_rows,
        "output": output,
    }


def freeze(directory: pathlib.Path) -> None:
    """Make the saved evidence read-only, deepest entries first."""
    for path in sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        mode = path.stat().st_mode
        os.chmod(path, mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    mode = directory.stat().st_mode
    os.chmod(directory, mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def save_unsupported(
    case: cases_module.Case, run_dir: pathlib.Path, harness: str, trial: dict
) -> dict:
    """Save the trial that did not happen, so the gap is visible.

    It carries no results.json — there is nothing to grade — and a status that
    cannot be mistaken for a pass by anything reading the directory.
    """
    reason = (
        f"case '{case.id}' does not declare the harness '{harness}' "
        f"(it declares: {', '.join(case.harnesses)}), so nothing was executed"
    )
    (run_dir / "outcome.json").write_text(
        json.dumps(
            {"status": STATUS_UNSUPPORTED, "reason": reason, "exit_code": None, "assertions": []},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "evaluation_id": trial["evaluation_id"],
        "case_id": case.id,
        "skill": case.skill,
        "kind": case.kind,
        "harness": harness,
        "arm": trial["arm"],
        "repetition_index": 0,
        "started_at": trial["started_at"],
        "ended_at": trial["ended_at"],
        "duration_ms": 0,
        "declared_harnesses": case.harnesses,
        "versions": tool_versions(),
        "source": source_provenance(),
        "status": STATUS_UNSUPPORTED,
        "reason": reason,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    freeze(run_dir)
    return {"status": STATUS_UNSUPPORTED, "reason": reason, "manifest": manifest}


def summarize(
    case: cases_module.Case,
    run_dir: pathlib.Path,
    paths: dict,
    execution: dict,
    trial: dict,
) -> dict:
    """Write every artifact into run_dir, then freeze it."""
    results = None
    results_path = run_dir / "results.json"
    if results_path.is_file():
        try:
            results = json.loads(results_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            results = None

    verdict = classify(case, results, execution)

    (run_dir / "request").mkdir(exist_ok=True)
    (run_dir / "response").mkdir(exist_ok=True)
    (run_dir / "transcript").mkdir(exist_ok=True)
    transcript_dir = run_dir / "transcript"

    (run_dir / "request" / "prompt.txt").write_text(paths["prompt"], encoding="utf-8")
    shutil.copyfile(paths["config"], run_dir / "request" / "promptfooconfig.yaml")
    (run_dir / "response" / "final.txt").write_text(verdict["output"], encoding="utf-8")

    copied = 0
    transcripts = paths.get("transcripts")
    if transcripts and transcripts.is_dir():
        for jsonl in sorted(transcripts.rglob("*.jsonl")):
            shutil.copyfile(jsonl, transcript_dir / jsonl.name)
            copied += 1

    row = {}
    if results:
        rows = results.get("results", {}).get("results", [])
        row = rows[0] if rows else {}
    metadata = (row.get("response") or {}).get("metadata") or row.get("metadata") or {}

    # Promptfoo grades `skill-used` from the provider's own report, which on a
    # typed invocation is empty. The verdict it reached stays exactly as it is —
    # this only attaches what the trial can actually show, so an unavailable
    # answer never reads as a confident negative.
    evidence = skill_evidence(metadata, transcript_dir)
    for assertion_row in verdict["assertions"]:
        if assertion_row.get("type") == "skill-used":
            assertion_row["evidence"] = evidence["calls"]
            assertion_row["evidence_source"] = evidence["source"]
            assertion_row["evidence_reason"] = evidence["reason"]

    (run_dir / "assertions.json").write_text(
        json.dumps(verdict["assertions"], indent=2) + "\n", encoding="utf-8"
    )
    (run_dir / "outcome.json").write_text(
        json.dumps(
            {
                "status": verdict["status"],
                "reason": verdict["reason"],
                "exit_code": execution.get("exit_code"),
                "assertions": verdict["assertions"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    token_usage = None
    token_usage_reason = None
    usage = row.get("tokenUsage")
    if usage:
        token_usage = {
            "total": usage.get("total"),
            "prompt": usage.get("prompt"),
            "completion": usage.get("completion"),
            # Each harness counts differently — Claude Code splits cache reads
            # and cache creation out of the prompt total. The normalised three
            # are comparable; the raw shape is what makes them auditable.
            "raw": usage,
        }
    else:
        token_usage_reason = "the harness reported no token usage for this trial"

    harness = trial["harness"]
    resolved_model, resolved_reason = _resolved_model(harness, metadata)

    transcript_reason = None
    if copied != 1:
        transcript_reason = (
            f"{copied} session transcript(s) were found where exactly one was expected"
        )

    auth = dict(trial["auth"])
    manifest = {
        "evaluation_id": trial["evaluation_id"],
        "case_id": case.id,
        "skill": case.skill,
        "kind": case.kind,
        "harness": trial["harness"],
        "arm": trial["arm"],
        "repetition_index": 0,
        "started_at": trial["started_at"],
        "ended_at": trial["ended_at"],
        "duration_ms": trial["duration_ms"],
        "auth": auth,
        "model": {
            "requested": prepare_module.requested_model(harness),
            "resolved": resolved_model,
            "resolved_reason": resolved_reason,
        },
        "cost_estimate": {"value": row.get("cost"), "basis": COST_BASIS},
        "versions": tool_versions(),
        "source": source_provenance(),
        "fingerprints": {
            "case": prepare_module.sha256_file(case.path),
            "skill": prepare_module.sha256_file(paths["staged_skill"]),
            "fixture": f"{paths['fixture_head']}+{prepare_module.sha256_file(case.fixture_build())}",
        },
        "harness_provided_skills": trial.get("harness_provided_skills", []),
        "skill_evidence": evidence,
        "harness_context": {
            "session_id": (row.get("response") or {}).get("sessionId") or paths.get("session_id"),
            "config_dir": str(paths["harness_home"]),
            "setting_sources": prepare_module.provider_config(paths["config_data"]).get(
                "setting_sources"
            ),
            "conversation": "fresh",
            "instruction_files": sorted(
                str(path.relative_to(paths["harness_home"]))
                for path in paths["harness_home"].rglob("*")
                if path.name in ("SKILL.md", "settings.json", "config.toml")
            ),
            "transcript_reason": transcript_reason,
        },
        "token_usage": token_usage,
        "token_usage_reason": token_usage_reason,
        "paths": {
            "workspace": str(paths["workspace"]),
            "transcript": str(run_dir / "transcript"),
            "results_json": str(run_dir / "results.json"),
            "results_html": str(run_dir / "results.html"),
        },
        "status": verdict["status"],
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    freeze(run_dir)
    return {"status": verdict["status"], "reason": verdict["reason"], "manifest": manifest}
