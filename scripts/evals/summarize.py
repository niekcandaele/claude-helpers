#!/usr/bin/env python3
"""Turn a finished trial into frozen, self-explaining evidence.

Every trial ends in exactly one status, and the three failure statuses are kept
apart on purpose: a harness that never ran tells you something different from a
harness that ran and got the answer wrong.

    passed             every required assertion passed
    assertion-failed   graded, and at least one required assertion failed
    execution-error    the harness errored, timed out, or never produced output
    ungraded           executed, but there was nothing to grade

The trial directory is made read-only at the end. Viewer ratings and comments
live in Promptfoo's own database; the saved evidence cannot be edited to agree
with them.
"""

from __future__ import annotations

import json
import os
import pathlib
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

# Promptfoo's ResultFailureReason: NONE=0, ASSERT=1, ERROR=2.
RESULT_FAILURE_ERROR = 2

MODEL_RESOLVED_REASON = (
    "the Codex SDK does not report the backend-resolved model through Promptfoo"
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
        "node": _command_version(["node", "--version"]),
        "just": _command_version(["just", "--version"]),
    }


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

    (run_dir / "request" / "prompt.txt").write_text(paths["prompt"], encoding="utf-8")
    shutil.copyfile(paths["config"], run_dir / "request" / "promptfooconfig.yaml")
    (run_dir / "response" / "final.txt").write_text(verdict["output"], encoding="utf-8")
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

    sessions = paths["codex_home"] / "sessions"
    if sessions.is_dir():
        for jsonl in sessions.rglob("*.jsonl"):
            shutil.copyfile(jsonl, run_dir / "transcript" / jsonl.name)

    token_usage = None
    token_usage_reason = None
    if results:
        rows = results.get("results", {}).get("results", [])
        usage = rows[0].get("tokenUsage") if rows else None
        if usage:
            token_usage = {
                "total": usage.get("total"),
                "prompt": usage.get("prompt"),
                "completion": usage.get("completion"),
            }
    if token_usage is None:
        token_usage_reason = "the harness reported no token usage for this trial"

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
            "requested": prepare_module.requested_model(),
            "resolved": None,
            "resolved_reason": MODEL_RESOLVED_REASON,
        },
        "versions": tool_versions(),
        "source": source_provenance(),
        "fingerprints": {
            "case": prepare_module.sha256_file(case.path),
            "skill": prepare_module.sha256_file(paths["staged_skill"]),
            "fixture": f"{paths['fixture_head']}+{prepare_module.sha256_file(case.fixture_build())}",
        },
        "harness_provided_skills": trial.get("harness_provided_skills", []),
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
