#!/usr/bin/env python3
"""Refuse to evaluate before any inference happens.

Every check here runs before a workspace is built and before a model is
contacted, so a misconfigured machine costs nothing. The paid-credential check
is the load-bearing one: this workflow only uses the local Codex subscription,
and it must never silently fall back to billed inference.

Never print a credential's value, length or prefix — only the name of the
setting that has to go.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cases as cases_module  # noqa: E402

ROOT = cases_module.ROOT
ROUTE = "chatgpt-subscription"

# Settings that would route inference through a billed API instead of the
# local subscription.
PAID_ENV_VARS = ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")
PAID_CONFIG_KEYS = ("apiKey", "base_url")


class PreflightError(Exception):
    """One or more reasons not to start. Carries (message, remedy) pairs."""

    def __init__(self, failures: list[tuple[str, str]]):
        self.failures = failures
        super().__init__(f"{len(failures)} preflight failure(s)")


def pinned_promptfoo_version() -> str:
    manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    return manifest["dependencies"]["promptfoo"]


def codex_home(env: dict[str, str]) -> pathlib.Path:
    override = env.get("CODEX_HOME")
    if override:
        return pathlib.Path(override)
    return pathlib.Path(env.get("HOME", str(pathlib.Path.home()))) / ".codex"


def _check_tooling(failures: list[tuple[str, str]]) -> None:
    for binary in ("node", "npx"):
        if shutil.which(binary) is None:
            failures.append(
                (f"'{binary}' is not on PATH", "install Node 22 or newer, then run 'npm ci'")
            )

    installed = ROOT / "node_modules" / "promptfoo" / "package.json"
    if not installed.is_file():
        failures.append(
            ("promptfoo is not installed", "run 'npm ci' from the repository root")
        )
        return

    version = json.loads(installed.read_text(encoding="utf-8")).get("version")
    pinned = pinned_promptfoo_version()
    if version != pinned:
        failures.append(
            (
                f"promptfoo {version} is installed but {pinned} is pinned",
                "run 'npm ci' so the evaluation tooling matches package-lock.json",
            )
        )


def _check_harness_auth(failures: list[tuple[str, str]], env: dict[str, str]) -> None:
    if shutil.which("codex") is None:
        failures.append(
            ("'codex' is not on PATH", "install the Codex CLI, then run 'codex login'")
        )

    auth_path = codex_home(env) / "auth.json"
    if not auth_path.is_file():
        failures.append(
            (
                f"no Codex credentials at {auth_path}",
                "Codex is not logged in with a ChatGPT subscription. Run 'codex login' and retry.",
            )
        )
        return

    try:
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(
            (
                f"{auth_path} cannot be read ({exc.__class__.__name__})",
                "Codex is not logged in with a ChatGPT subscription. Run 'codex login' and retry.",
            )
        )
        return

    if auth.get("auth_mode") != "chatgpt":
        failures.append(
            (
                f"{auth_path} has auth_mode {auth.get('auth_mode')!r}, not 'chatgpt'",
                "Codex is not logged in with a ChatGPT subscription. Run 'codex login' and retry.",
            )
        )

    if auth.get("OPENAI_API_KEY"):
        failures.append(
            (
                f"{auth_path} carries an OPENAI_API_KEY",
                "A paid OpenAI credential is configured. This evaluation only uses the local "
                "Codex subscription and will not fall back to paid inference. Clear OPENAI_API_KEY "
                f"in {auth_path} and retry.",
            )
        )


def _check_paid_credentials(
    failures: list[tuple[str, str]], env: dict[str, str], provider_config: dict | None
) -> None:
    for name in PAID_ENV_VARS:
        if env.get(name):
            failures.append(
                (
                    f"{name} is set in the environment",
                    "A paid OpenAI credential is configured. This evaluation only uses the local "
                    "Codex subscription and will not fall back to paid inference. "
                    f"Unset {name} and retry.",
                )
            )

    for key in PAID_CONFIG_KEYS:
        if provider_config and key in provider_config:
            failures.append(
                (
                    f"the provider config sets '{key}'",
                    "A paid OpenAI credential is configured. This evaluation only uses the local "
                    "Codex subscription and will not fall back to paid inference. "
                    f"Remove '{key}' from evals/config/base.yaml and retry.",
                )
            )


def preflight(
    case: cases_module.Case | None,
    *,
    env: dict[str, str] | None = None,
    provider_config: dict | None = None,
    require_harness_auth: bool = True,
) -> str:
    """Return the auth route, or raise PreflightError listing every problem.

    `require_harness_auth` is false when a provider double is selected: no
    harness is contacted, so demanding a Codex login would be a lie. The
    paid-credential refusal still applies — that promise holds for the whole
    workflow, doubles included.
    """
    env = dict(os.environ if env is None else env)
    failures: list[tuple[str, str]] = []

    _check_tooling(failures)
    if require_harness_auth:
        _check_harness_auth(failures, env)
    _check_paid_credentials(failures, env, provider_config)

    if case is not None:
        for message, remedy in cases_module.validate_all():
            failures.append((message, remedy))

    if failures:
        raise PreflightError(failures)
    return ROUTE


def report(failures: list[tuple[str, str]]) -> None:
    print(f"✗ {len(failures)} preflight failure(s):\n", file=sys.stderr)
    for message, remedy in failures:
        print(f"  {message}\n    → {remedy}\n", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", help="case id to validate")
    parser.add_argument(
        "--no-harness-auth",
        action="store_true",
        help="skip the Codex login checks (used when a provider double stands in for the harness)",
    )
    args = parser.parse_args(argv)

    case = cases_module.load(args.case) if args.case else None
    try:
        route = preflight(case, require_harness_auth=not args.no_harness_auth)
    except PreflightError as exc:
        report(exc.failures)
        return 1
    print(f"✓ preflight passed — auth route: {route}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
