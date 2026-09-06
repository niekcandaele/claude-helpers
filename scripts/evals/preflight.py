#!/usr/bin/env python3
"""Refuse to evaluate before any inference happens.

Every check here runs before a workspace is built and before a model is
contacted, so a misconfigured machine costs nothing. The paid-credential check
is the load-bearing one: this workflow only uses the local subscription of each
harness, and it must never silently fall back to billed inference.

Every failure names the harness it affects, because a two-harness selection can
be blocked by a setting that concerns only one of them.

Never print a credential's value, length or prefix — only the name of the
setting that has to go.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cases as cases_module  # noqa: E402

ROOT = cases_module.ROOT

ROUTES = {
    "codex": "chatgpt-subscription",
    "claude-code": "claude-subscription",
}

# Settings that would route inference through a billed API instead of the local
# subscription, and the harness each one affects. The refusal is global — it
# fires whatever harness is selected and whether or not a provider double
# stands in — because that promise holds for the whole workflow.
PAID_ENV_VARS = {
    "OPENAI_API_KEY": "codex",
    "CODEX_API_KEY": "codex",
    "OPENAI_BASE_URL": "codex",
    "ANTHROPIC_API_KEY": "claude-code",
    "ANTHROPIC_AUTH_TOKEN": "claude-code",
    "ANTHROPIC_BASE_URL": "claude-code",
    "ANTHROPIC_CUSTOM_HEADERS": "claude-code",
    "CLAUDE_CODE_USE_BEDROCK": "claude-code",
    "CLAUDE_CODE_USE_VERTEX": "claude-code",
}

PAID_CONFIG_KEYS = {
    "codex": ("apiKey", "base_url"),
    "claude-code": ("apiKey", "apiKeyHelper", "forceLoginMethod"),
}

CLAUDE_AGENT_SDK = "@anthropic-ai/claude-agent-sdk"


class PreflightError(Exception):
    """One or more reasons not to start. Carries (message, remedy) pairs."""

    def __init__(self, failures: list[tuple[str, str]]):
        self.failures = failures
        super().__init__(f"{len(failures)} preflight failure(s)")


def _pinned(name: str) -> str:
    manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    return manifest["dependencies"][name]


def pinned_promptfoo_version() -> str:
    return _pinned("promptfoo")


def codex_home(env: dict[str, str]) -> pathlib.Path:
    override = env.get("CODEX_HOME")
    if override:
        return pathlib.Path(override)
    return pathlib.Path(env.get("HOME", str(pathlib.Path.home()))) / ".codex"


def claude_config_dir(env: dict[str, str]) -> pathlib.Path:
    """Where the real Claude Code credentials live.

    CLAUDE_CONFIG_DIR replaces $HOME/.claude wholesale, so an operator who has
    moved their config must be followed there — the credential we symlink into
    the trial has to be the one the machine is actually logged in with.
    """
    override = env.get("CLAUDE_CONFIG_DIR")
    if override:
        return pathlib.Path(override)
    return pathlib.Path(env.get("HOME", str(pathlib.Path.home()))) / ".claude"


def affects(harness: str) -> str:
    return f"(affects harness: {harness})"


def _check_tooling(
    failures: list[tuple[str, str]], harnesses: list[str]
) -> None:
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

    if "claude-code" not in harnesses:
        return
    sdk = ROOT / "node_modules" / CLAUDE_AGENT_SDK / "package.json"
    if not sdk.is_file():
        failures.append(
            (
                f"{CLAUDE_AGENT_SDK} is not installed {affects('claude-code')}",
                "run 'npm ci' from the repository root",
            )
        )
        return
    sdk_version = json.loads(sdk.read_text(encoding="utf-8")).get("version")
    sdk_pinned = _pinned(CLAUDE_AGENT_SDK)
    if sdk_version != sdk_pinned:
        failures.append(
            (
                f"{CLAUDE_AGENT_SDK} {sdk_version} is installed but {sdk_pinned} is pinned "
                f"{affects('claude-code')}",
                "run 'npm ci' so the evaluation tooling matches package-lock.json",
            )
        )


def _check_codex_auth(failures: list[tuple[str, str]], env: dict[str, str]) -> None:
    login = "Codex is not logged in with a ChatGPT subscription. Run 'codex login' and retry."
    if shutil.which("codex") is None:
        failures.append(
            (
                f"'codex' is not on PATH {affects('codex')}",
                "install the Codex CLI, then run 'codex login'",
            )
        )

    auth_path = codex_home(env) / "auth.json"
    if not auth_path.is_file():
        failures.append((f"no Codex credentials at {auth_path} {affects('codex')}", login))
        return

    try:
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(
            (f"{auth_path} cannot be read ({exc.__class__.__name__}) {affects('codex')}", login)
        )
        return

    if auth.get("auth_mode") != "chatgpt":
        failures.append(
            (
                f"{auth_path} has auth_mode {auth.get('auth_mode')!r}, not 'chatgpt' "
                f"{affects('codex')}",
                login,
            )
        )

    if auth.get("OPENAI_API_KEY"):
        failures.append(
            (
                f"{auth_path} carries an OPENAI_API_KEY {affects('codex')}",
                "A paid OpenAI credential is configured. This evaluation only uses the local "
                "Codex subscription and will not fall back to paid inference. Clear OPENAI_API_KEY "
                f"in {auth_path} and retry.",
            )
        )


def claude_auth_status(env: dict[str, str]) -> tuple[dict | None, str | None]:
    """`claude auth status --json`, which makes no model call.

    Returns the parsed payload, or None and the reason it is unavailable.
    """
    try:
        result = subprocess.run(
            ["claude", "auth", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return None, "'claude auth status' did not answer within 30 seconds"
    except OSError as exc:
        return None, f"'claude auth status' could not be started ({exc.__class__.__name__})"
    if result.returncode != 0:
        return None, "'claude auth status' exited non-zero"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, "'claude auth status --json' did not print a JSON object"


def _check_claude_auth(failures: list[tuple[str, str]], env: dict[str, str]) -> None:
    login = (
        "Claude Code is not logged in with a Claude subscription. Run 'claude auth login' "
        "and retry."
    )
    if shutil.which("claude") is None:
        failures.append(
            (
                f"'claude' is not on PATH {affects('claude-code')}",
                "install Claude Code, then run 'claude auth login'",
            )
        )
        return

    status, reason = claude_auth_status(env)
    if status is None:
        failures.append((f"{reason} {affects('claude-code')}", login))
        return

    if not status.get("loggedIn") or status.get("authMethod") != "claude.ai":
        failures.append(
            (
                f"Claude Code reports authMethod {status.get('authMethod')!r} "
                f"{affects('claude-code')}",
                login,
            )
        )

    # The name only. An operator who has this set already knows the value, and
    # anyone reading the saved log must not learn it.
    source = status.get("apiKeySource")
    if source:
        failures.append(
            (
                f"Claude Code is using an API key from {source} {affects('claude-code')}",
                f"A paid Anthropic credential is configured ({source}). This evaluation only "
                "uses the local Claude subscription and will not fall back to paid inference. "
                "Unset it and retry.",
            )
        )

    provider = status.get("apiProvider")
    if provider is not None and provider != "firstParty":
        failures.append(
            (
                f"Claude Code is routed through a third-party provider ({provider}) "
                f"{affects('claude-code')}",
                "This evaluation only uses the local Claude subscription. Unset "
                "CLAUDE_CODE_USE_BEDROCK / CLAUDE_CODE_USE_VERTEX and retry.",
            )
        )


HARNESS_AUTH_CHECKS = {"codex": _check_codex_auth, "claude-code": _check_claude_auth}


def _check_paid_credentials(
    failures: list[tuple[str, str]],
    env: dict[str, str],
    provider_configs: dict[str, dict] | None,
) -> None:
    for name, harness in PAID_ENV_VARS.items():
        if env.get(name):
            failures.append(
                (
                    f"{name} is set in the environment {affects(harness)}",
                    "A paid credential is configured. This evaluation only uses the local "
                    "subscription and will not fall back to paid inference. "
                    f"Unset {name} and retry.",
                )
            )

    for harness, config in (provider_configs or {}).items():
        for key in PAID_CONFIG_KEYS.get(harness, ()):
            if key in (config or {}):
                failures.append(
                    (
                        f"the provider config sets '{key}' {affects(harness)}",
                        "A paid credential is configured. This evaluation only uses the local "
                        "subscription and will not fall back to paid inference. "
                        f"Remove '{key}' from evals/config/providers/{harness}.yaml and retry.",
                    )
                )


def preflight(
    case: cases_module.Case | None,
    *,
    harnesses: list[str] | None = None,
    env: dict[str, str] | None = None,
    provider_configs: dict[str, dict] | None = None,
    require_harness_auth: bool = True,
) -> dict[str, str]:
    """Return {harness: auth route}, or raise PreflightError listing every problem.

    `require_harness_auth` is false when a provider double is selected: no
    harness is contacted, so demanding a login would be a lie. The
    paid-credential refusal still applies — that promise holds for the whole
    workflow, doubles included.
    """
    env = dict(os.environ if env is None else env)
    harnesses = harnesses or ["codex"]
    failures: list[tuple[str, str]] = []

    _check_tooling(failures, harnesses)
    if require_harness_auth:
        for harness in harnesses:
            HARNESS_AUTH_CHECKS[harness](failures, env)
    _check_paid_credentials(failures, env, provider_configs)

    if case is not None:
        for message, remedy in cases_module.validate_all():
            failures.append((message, remedy))

    if failures:
        raise PreflightError(failures)
    return {harness: ROUTES[harness] for harness in harnesses}


def report(failures: list[tuple[str, str]]) -> None:
    print(f"✗ {len(failures)} preflight failure(s):\n", file=sys.stderr)
    for message, remedy in failures:
        print(f"  {message}\n    → {remedy}\n", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", help="case id to validate")
    parser.add_argument(
        "--harness",
        default="codex",
        help="harness selection: a name, a comma-separated list, or 'both'/'all'",
    )
    parser.add_argument(
        "--no-harness-auth",
        action="store_true",
        help="skip the login checks (used when a provider double stands in for the harness)",
    )
    args = parser.parse_args(argv)

    harnesses = cases_module.resolve_harnesses(args.harness)
    case = cases_module.load(args.case) if args.case else None
    try:
        routes = preflight(
            case, harnesses=harnesses, require_harness_auth=not args.no_harness_auth
        )
    except PreflightError as exc:
        report(exc.failures)
        return 1
    for harness, route in routes.items():
        print(f"✓ preflight passed — {harness} auth route: {route}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
