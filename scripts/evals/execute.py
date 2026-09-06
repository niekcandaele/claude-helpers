#!/usr/bin/env python3
"""Execute one prepared trial through the pinned Promptfoo CLI.

One serial trial, caching disabled, bounded by an OS-level timeout — the
Promptfoo Codex provider documents no timeout of its own, so the bound has to
come from outside. A timeout is an execution error, never an assertion failure.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cases as cases_module  # noqa: E402

ROOT = cases_module.ROOT
DEFAULT_TIMEOUT_S = 900
TIMEOUT_EXIT = 124


def timeout_seconds() -> int:
    return int(os.environ.get("SKILL_EVAL_TIMEOUT_S", DEFAULT_TIMEOUT_S))


def execute(paths: dict, run_dir: pathlib.Path) -> dict:
    """Run the trial, tee its output to logs/promptfoo.log, return the outcome."""
    log_path = run_dir / "logs" / "promptfoo.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    results_json = run_dir / "results.json"
    results_html = run_dir / "results.html"

    command = [
        "timeout",
        "--signal=TERM",
        str(timeout_seconds()),
        "npx",
        "--no-install",
        "promptfoo",
        "eval",
        "-c",
        str(paths["config"]),
        "--no-cache",
        "-j",
        "1",
        "--repeat",
        "1",
        "-o",
        str(results_json),
        "-o",
        str(results_html),
    ]

    env = dict(os.environ)
    env["PROMPTFOO_CONFIG_DIR"] = str(paths["promptfoo_home"])
    env["NO_COLOR"] = "1"
    # The Codex provider carries its own per-trial `cli_env`; the Claude Agent
    # SDK provider carries `env` in the generated config, which is layered over
    # this process's environment. Setting the same two variables here as well
    # means the harness cannot see the maintainer's config even if the provider
    # block is ever rendered without them. PATH, npm_config_cache and NODE_PATH
    # are untouched, so `npx --no-install` still resolves the repo's install.
    if paths.get("harness") == "claude-code":
        real_home = env.get("HOME")
        if real_home and "npm_config_cache" not in env:
            env["npm_config_cache"] = str(pathlib.Path(real_home) / ".npm")
        env["CLAUDE_CONFIG_DIR"] = str(paths["harness_home"])
        env["HOME"] = str(paths["home"])

    completed = subprocess.run(
        command, cwd=str(ROOT), env=env, capture_output=True, text=True
    )
    log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")

    return {
        "command": command,
        "exit_code": completed.returncode,
        "timed_out": completed.returncode == TIMEOUT_EXIT,
        "results_json": results_json,
        "results_html": results_html,
        "log": log_path,
    }
