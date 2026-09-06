#!/usr/bin/env python3
"""Model-free checks for the evaluation tooling.

Everything here runs through the public command surface — cases.py, preflight.py,
prepare.py, run.py — and a provider double stands in for the harness, so the
suite needs Promptfoo but no credentials, no network and no subscription
allowance. CI runs it exactly as written.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "scripts" / "evals"
CASE_DIR = ROOT / "evals" / "cases" / "catchup-branch-state"
FIXTURE_BUILD = ROOT / "evals" / "fixtures" / "git-branch-state" / "build.sh"
EXPECTATIONS = CASE_DIR / "expectations"

SECRET = "sk-doesnotmatter-9f3c1d"


def rmtree(path: pathlib.Path) -> None:
    """Remove a tree that summarize.py has frozen read-only."""

    def unlock(func, target, _exc):
        os.chmod(pathlib.Path(target).parent, 0o700)
        os.chmod(target, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
        func(target)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=unlock)
    else:
        shutil.rmtree(path, onerror=unlock)


def cli(args: list[str], env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    for name in (
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
        "OPENAI_BASE_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_CUSTOM_HEADERS",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
    ):
        env.pop(name, None)
    env["NO_COLOR"] = "1"
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, *args], cwd=str(ROOT), env=env, capture_output=True, text=True
    )


class StateDirTest(unittest.TestCase):
    """A test that gets its own evaluation state directory."""

    def setUp(self) -> None:
        self.state = pathlib.Path(tempfile.mkdtemp(prefix="skills-evals-test-"))
        self.addCleanup(rmtree, self.state)
        self.env = {"SKILL_EVAL_STATE_DIR": str(self.state)}

    @property
    def runs(self) -> pathlib.Path:
        return self.state / "runs"

    def trial_dirs(self) -> list[pathlib.Path]:
        return sorted(p for p in self.runs.glob("*") if p.is_dir()) if self.runs.is_dir() else []

    def double_trial(
        self, spec: str, harness: str = "codex", **env_extra: str
    ) -> tuple[subprocess.CompletedProcess, dict]:
        result = self.run_cli(spec, harness, **env_extra)
        trials = self.trial_dirs()
        self.assertEqual(len(trials), 1, result.stdout + result.stderr)
        outcome = json.loads((trials[0] / "outcome.json").read_text(encoding="utf-8"))
        return result, {"dir": trials[0], "outcome": outcome}

    def run_cli(
        self, spec: str, harness: str = "codex", **env_extra: str
    ) -> subprocess.CompletedProcess:
        return cli(
            [
                str(SCRIPTS / "run.py"),
                "--case",
                "catchup-branch-state",
                "--harness",
                harness,
                "--provider-double",
                spec,
            ],
            {**self.env, **env_extra},
        )

    def trial(self, path: pathlib.Path) -> dict:
        return {
            "manifest": json.loads((path / "manifest.json").read_text(encoding="utf-8")),
            "outcome": json.loads((path / "outcome.json").read_text(encoding="utf-8")),
        }


class DiscoveryTest(unittest.TestCase):
    def test_lists_the_case_with_its_metadata(self) -> None:
        result = cli([str(SCRIPTS / "cases.py"), "--list"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("catchup-branch-state", result.stdout)
        self.assertIn("skill=catchup", result.stdout)
        self.assertIn("kind=behavior", result.stdout)
        self.assertIn("harnesses=codex,claude-code", result.stdout)

    def test_the_repository_case_validates(self) -> None:
        result = cli([str(SCRIPTS / "cases.py"), "--validate"])
        self.assertEqual(result.returncode, 0, result.stderr)


class InvalidCaseTest(StateDirTest):
    """Every one of these must be refused before any inference happens."""

    MUTATIONS = {
        "missing id": lambda case: case.pop("id"),
        "id does not match the directory": lambda case: case.update({"id": "somethingelse"}),
        "unknown skill": lambda case: case.update({"skill": "no-such-skill"}),
        "missing fixture": lambda case: case.pop("fixture"),
        "fixture does not exist": lambda case: case.update({"fixture": "no-such-fixture"}),
        "empty assert": lambda case: case.update({"assert": []}),
        "every assertion weighted zero": lambda case: case.update(
            {"assert": [dict(entry, weight=0) for entry in case["assert"]]}
        ),
        "invocation embedded in task": lambda case: case.update(
            {"task": case["invocation"] + " " + case["task"]}
        ),
        "unknown top-level key": lambda case: case.update({"harnes": ["codex"]}),
        "duplicate harness": lambda case: case.update({"harnesses": ["codex", "codex"]}),
        "task names a harness": lambda case: case.update(
            {"task": "Using Codex, " + case["task"]}
        ),
        "expected_behavior names a harness directory": lambda case: case.update(
            {"expected_behavior": case["expected_behavior"] + " Read it from .claude/ first."}
        ),
    }

    def _broken_case_dir(self, mutate) -> pathlib.Path:
        cases_dir = self.state / "cases"
        target = cases_dir / "catchup-branch-state"
        target.mkdir(parents=True)
        data = yaml.safe_load((CASE_DIR / "case.yaml").read_text(encoding="utf-8"))
        mutate(data)
        (target / "case.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        shutil.copytree(EXPECTATIONS, target / "expectations")
        shutil.copytree(ROOT / "evals" / "asserts", cases_dir.parent / "asserts", dirs_exist_ok=True)
        return cases_dir

    def test_each_broken_case_is_refused_with_a_remedy(self) -> None:
        for label, mutate in self.MUTATIONS.items():
            with self.subTest(label):
                if (self.state / "cases").exists():
                    rmtree(self.state / "cases")
                cases_dir = self._broken_case_dir(mutate)
                case_id = yaml.safe_load(
                    (cases_dir / "catchup-branch-state" / "case.yaml").read_text(encoding="utf-8")
                ).get("id", "catchup-branch-state")
                result = cli(
                    [str(SCRIPTS / "run.py"), "--case", str(case_id), "--provider-double", "empty"],
                    {**self.env, "SKILL_EVAL_CASES_DIR": str(cases_dir)},
                )
                combined = result.stdout + result.stderr
                self.assertNotEqual(result.returncode, 0, combined)
                self.assertIn("case.yaml", combined)
                self.assertIn("→", combined)
                self.assertEqual(self.trial_dirs(), [], f"{label} started a trial anyway")


class GraderCalibrationTest(StateDirTest):
    def test_a_good_summary_passes_every_required_assertion(self) -> None:
        result, trial = self.double_trial(f"respond:{EXPECTATIONS / 'acceptable.md'}")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(trial["outcome"]["status"], "passed")
        required = [row for row in trial["outcome"]["assertions"] if row["required"]]
        self.assertTrue(required)
        for row in required:
            self.assertTrue(row["pass"], row)

        # Each observable fact has to arrive with its own evidence string, not
        # be collapsed into one verdict.
        facts = next(row for row in required if row["metric"] == "git-facts")
        self.assertGreaterEqual(len(facts["components"]), 10, facts)
        for fact in facts["components"]:
            self.assertTrue(fact["metric"])
            self.assertTrue(fact["reason"])

    def test_a_plausible_but_wrong_summary_fails_and_says_which_fact(self) -> None:
        _, trial = self.double_trial(f"respond:{EXPECTATIONS / 'unacceptable.md'}")
        self.assertEqual(trial["outcome"]["status"], "assertion-failed")
        failed = [
            row
            for row in trial["outcome"]["assertions"]
            if row["required"] and row["pass"] is False
        ]
        self.assertTrue(failed, trial["outcome"])
        self.assertIn("git-facts", [row["metric"] for row in failed])
        reason = " ".join(row["reason"] or "" for row in failed)
        self.assertIn("3 commits ahead", reason)
        self.assertIn("legacy_coupon.js", reason)


class ExecutionErrorTest(StateDirTest):
    def test_a_harness_error_is_not_an_assertion_failure(self) -> None:
        _, trial = self.double_trial("error:the harness fell over")
        self.assertEqual(trial["outcome"]["status"], "execution-error")
        self.assertEqual(trial["outcome"]["assertions"], [])
        results = json.loads((trial["dir"] / "results.json").read_text(encoding="utf-8"))
        row = results["results"]["results"][0]
        self.assertEqual(row["failureReason"], 2, "promptfoo recorded it as a failure, not an error")


class UngradedTest(StateDirTest):
    def test_no_output_is_ungraded_rather_than_passed(self) -> None:
        result, trial = self.double_trial("empty")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(trial["outcome"]["status"], "ungraded")


class PaidCredentialTest(StateDirTest):
    def test_a_paid_credential_stops_the_trial_without_disclosing_it(self) -> None:
        for name in ("OPENAI_API_KEY", "CODEX_API_KEY"):
            with self.subTest(name):
                result = cli(
                    [
                        str(SCRIPTS / "run.py"),
                        "--case",
                        "catchup-branch-state",
                        "--provider-double",
                        "empty",
                    ],
                    {**self.env, name: SECRET},
                )
                combined = result.stdout + result.stderr
                self.assertNotEqual(result.returncode, 0, combined)
                self.assertIn(name, combined)
                self.assertNotIn(SECRET, combined)
                self.assertEqual(self.trial_dirs(), [])
                for path in self.state.rglob("*"):
                    if path.is_file():
                        self.assertNotIn(
                            SECRET, path.read_text(encoding="utf-8", errors="ignore"), str(path)
                        )


class MissingLoginTest(unittest.TestCase):
    def _preflight(self, codex_home: pathlib.Path) -> subprocess.CompletedProcess:
        return cli(
            [str(SCRIPTS / "preflight.py"), "--case", "catchup-branch-state"],
            {"CODEX_HOME": str(codex_home)},
        )

    def test_no_credentials_at_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self._preflight(pathlib.Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("codex login", result.stderr)

    def test_an_api_key_login_is_not_the_subscription_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp)
            (home / "auth.json").write_text(json.dumps({"auth_mode": "apikey"}), encoding="utf-8")
            result = self._preflight(home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("codex login", result.stderr)


class IsolationTest(StateDirTest):
    def _prepare(self, evaluation_id: str) -> pathlib.Path:
        result = cli(
            [str(SCRIPTS / "prepare.py"), "--case", "catchup-branch-state"],
            {**self.env, "SKILL_EVAL_EVALUATION_ID": evaluation_id},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.state / "work" / evaluation_id

    def test_a_rebuilt_workspace_is_identical_and_carries_no_answers(self) -> None:
        first = self._prepare("first") / "workspace"
        second = self._prepare("second") / "workspace"

        def tree(root: pathlib.Path) -> dict[str, bytes]:
            return {
                str(path.relative_to(root)): path.read_bytes()
                for path in sorted(root.rglob("*"))
                if path.is_file() and ".git" not in path.parts
            }

        self.assertEqual(tree(first), tree(second))

        for forbidden in ("AGENTS.md", "CLAUDE.md", ".claude", ".codex"):
            self.assertFalse((first / forbidden).exists(), forbidden)

        expected_behavior = yaml.safe_load((CASE_DIR / "case.yaml").read_text(encoding="utf-8"))[
            "expected_behavior"
        ]
        for path in first.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("catchup-branch-state", text, str(path))
            self.assertNotIn("manifest.json", text, str(path))
            self.assertNotIn(expected_behavior[:40], text, str(path))

    def test_only_the_target_skill_is_staged(self) -> None:
        work = self._prepare("staging")
        staged = sorted(p.name for p in (work / "codex-home" / "skills").iterdir())
        self.assertEqual(staged, ["catchup"])


class EvidenceTest(StateDirTest):
    REQUIRED_FIELDS = [
        "evaluation_id",
        "case_id",
        "skill",
        "kind",
        "harness",
        "arm",
        "repetition_index",
        "started_at",
        "ended_at",
        "duration_ms",
        "auth",
        "model",
        "versions",
        "source",
        "fingerprints",
        "harness_provided_skills",
        "token_usage",
        "paths",
    ]

    def test_a_saved_trial_is_complete_frozen_and_never_overwritten(self) -> None:
        pinned = {"SKILL_EVAL_EVALUATION_ID": "pinned-trial"}
        result, trial = self.double_trial(f"respond:{EXPECTATIONS / 'acceptable.md'}", **pinned)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        manifest = json.loads((trial["dir"] / "manifest.json").read_text(encoding="utf-8"))
        for field in self.REQUIRED_FIELDS:
            self.assertIn(field, manifest)
        self.assertIsNone(manifest["model"]["resolved"])
        self.assertTrue(manifest["model"]["resolved_reason"])
        for name in ("results.json", "results.html", "assertions.json", "outcome.json"):
            self.assertGreater((trial["dir"] / name).stat().st_size, 0, name)
        self.assertTrue((trial["dir"] / "request" / "prompt.txt").is_file())
        self.assertTrue((trial["dir"] / "request" / "promptfooconfig.yaml").is_file())
        self.assertTrue((trial["dir"] / "response" / "final.txt").is_file())

        self.assertEqual(list(self.runs.rglob("auth.json")), [])

        second = cli(
            [
                str(SCRIPTS / "run.py"),
                "--case",
                "catchup-branch-state",
                "--provider-double",
                f"respond:{EXPECTATIONS / 'acceptable.md'}",
            ],
            {**self.env, **pinned},
        )
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("already exists", second.stderr)
        self.assertEqual(len(self.trial_dirs()), 1)


class SecondHarnessTest(StateDirTest):
    """The same case, the other harness — shared expectations, not duplicated ones."""

    def test_a_good_summary_passes_on_claude_code_too(self) -> None:
        result, trial = self.double_trial(
            f"respond:{EXPECTATIONS / 'acceptable.md'}", "claude-code"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(trial["outcome"]["status"], "passed")

        manifest = json.loads((trial["dir"] / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["harness"], "claude-code")

        required = [row for row in trial["outcome"]["assertions"] if row["required"]]
        self.assertEqual(
            sorted(row["metric"] for row in required),
            ["git-facts", "names-base-branch", "names-branch"],
        )
        for row in required:
            self.assertTrue(row["pass"], row)

    def test_a_wrong_summary_fails_the_same_named_assertion(self) -> None:
        _, trial = self.double_trial(
            f"respond:{EXPECTATIONS / 'unacceptable.md'}", "claude-code"
        )
        self.assertEqual(trial["outcome"]["status"], "assertion-failed")
        failed = [
            row
            for row in trial["outcome"]["assertions"]
            if row["required"] and row["pass"] is False
        ]
        self.assertIn("git-facts", [row["metric"] for row in failed])


class BothHarnessesTest(StateDirTest):
    def test_two_trials_with_distinct_identities_and_one_shared_request(self) -> None:
        result = self.run_cli(f"respond:{EXPECTATIONS / 'acceptable.md'}", "both")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined)

        trials = self.trial_dirs()
        self.assertEqual(len(trials), 2, combined)
        self.assertEqual(len({path.name for path in trials}), 2)

        by_harness = {}
        for path in trials:
            saved = self.trial(path)
            by_harness[saved["manifest"]["harness"]] = (path, saved)
        self.assertEqual(sorted(by_harness), ["claude-code", "codex"])

        for path, _ in by_harness.values():
            for name in ("results.json", "results.html", "assertions.json"):
                self.assertGreater((path / name).stat().st_size, 0, f"{path.name}/{name}")

        # The same task reaches both harnesses byte for byte. Only the sentence
        # that summons the skill is translated, because Claude Code refuses
        # prose invocation of a skill whose own frontmatter disables it.
        case = yaml.safe_load((CASE_DIR / "case.yaml").read_text(encoding="utf-8"))
        task = " ".join(case["task"].split())
        prompts = {
            harness: (path / "request" / "prompt.txt").read_text(encoding="utf-8")
            for harness, (path, _) in by_harness.items()
        }
        for harness, prompt in prompts.items():
            invocation, _, sent_task = prompt.partition("\n\n")
            self.assertEqual(" ".join(sent_task.split()), task, harness)
            self.assertTrue(invocation.strip(), harness)
        self.assertEqual(prompts["codex"].split("\n\n")[0], case["invocation"])
        self.assertEqual(prompts["claude-code"].split("\n\n")[0], "/catchup")

        self.assertIn("trials              2", result.stdout)
        self.assertIn("[1] harness         codex", result.stdout)
        self.assertIn("[2] harness         claude-code", result.stdout)
        self.assertIn("says nothing about the other", result.stdout)

    def test_one_harness_result_cannot_satisfy_the_other(self) -> None:
        result = self.run_cli(
            f"codex=respond:{EXPECTATIONS / 'acceptable.md'},claude-code=empty", "both"
        )
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, combined)

        saved = {
            self.trial(path)["manifest"]["harness"]: (path, self.trial(path))
            for path in self.trial_dirs()
        }
        self.assertEqual(saved["codex"][1]["outcome"]["status"], "passed")
        self.assertEqual(saved["claude-code"][1]["outcome"]["status"], "ungraded")

        # Neither trial's own record carries the other's verdict.
        self.assertNotIn("ungraded", json.dumps(saved["codex"][1]["outcome"]))
        self.assertNotEqual(saved["claude-code"][1]["outcome"]["status"], "passed")

        # And they are genuinely separate directories.
        rmtree(saved["claude-code"][0])
        self.assertTrue((saved["codex"][0] / "manifest.json").is_file())


class UnsupportedHarnessTest(StateDirTest):
    def _codex_only_case(self) -> pathlib.Path:
        cases_dir = self.state / "cases"
        target = cases_dir / "catchup-branch-state"
        target.mkdir(parents=True)
        data = yaml.safe_load((CASE_DIR / "case.yaml").read_text(encoding="utf-8"))
        data["harnesses"] = ["codex"]
        (target / "case.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        shutil.copytree(EXPECTATIONS, target / "expectations")
        shutil.copytree(ROOT / "evals" / "asserts", cases_dir.parent / "asserts", dirs_exist_ok=True)
        return cases_dir

    def test_a_harness_the_case_never_declared_is_saved_as_unsupported(self) -> None:
        cases_dir = self._codex_only_case()
        result = self.run_cli(
            f"respond:{EXPECTATIONS / 'acceptable.md'}",
            "both",
            SKILL_EVAL_CASES_DIR=str(cases_dir),
        )
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, combined)

        saved = {
            self.trial(path)["manifest"]["harness"]: self.trial(path)
            for path in self.trial_dirs()
        }
        self.assertEqual(saved["codex"]["outcome"]["status"], "passed")
        self.assertEqual(saved["claude-code"]["outcome"]["status"], "unsupported")
        self.assertFalse((self.runs / saved["claude-code"]["manifest"]["evaluation_id"]
                          / "results.json").exists())

        reason = saved["claude-code"]["outcome"]["reason"]
        self.assertIn("catchup-branch-state", reason)
        self.assertIn("claude-code", reason)
        self.assertEqual(saved["claude-code"]["manifest"]["status"], "unsupported")


class ClaudePaidCredentialTest(StateDirTest):
    def test_each_paid_anthropic_setting_stops_every_trial(self) -> None:
        for name in (
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_BASE_URL",
            "CLAUDE_CODE_USE_BEDROCK",
            "CLAUDE_CODE_USE_VERTEX",
        ):
            with self.subTest(name):
                result = self.run_cli("empty", "both", **{name: SECRET})
                combined = result.stdout + result.stderr
                self.assertNotEqual(result.returncode, 0, combined)
                self.assertIn(name, combined)
                self.assertIn("affects harness: claude-code", combined)
                self.assertNotIn(SECRET, combined)
                self.assertEqual(self.trial_dirs(), [])
                for path in self.state.rglob("*"):
                    if path.is_file():
                        self.assertNotIn(
                            SECRET, path.read_text(encoding="utf-8", errors="ignore"), str(path)
                        )


def _claude_stub(directory: str, payload: dict) -> None:
    """A `claude` on PATH that answers one fixed auth status and nothing else.

    A stub rather than a mocking seam, so the real subprocess call is what the
    test exercises.
    """
    stub = pathlib.Path(directory) / "claude"
    stub.write_text(
        "#!/bin/sh\nprintf '%s' " + json.dumps(json.dumps(payload)) + "\n", encoding="utf-8"
    )
    stub.chmod(0o755)


class ClaudeLoginTest(unittest.TestCase):
    PAYLOADS = {
        "not logged in": {"loggedIn": False, "authMethod": "none"},
        "a paid API key is configured": {
            "loggedIn": True,
            "authMethod": "claude.ai",
            "apiProvider": "firstParty",
            "apiKeySource": "ANTHROPIC_API_KEY",
        },
        "routed through a third party": {
            "loggedIn": True,
            "authMethod": "claude.ai",
            "apiProvider": "bedrock",
        },
    }

    def _preflight(self, tmp: str) -> subprocess.CompletedProcess:
        return cli(
            [
                str(SCRIPTS / "preflight.py"),
                "--case",
                "catchup-branch-state",
                "--harness",
                "claude-code",
            ],
            {"PATH": f"{tmp}:{os.environ['PATH']}"},
        )

    def test_each_broken_login_is_refused_with_a_remedy(self) -> None:
        for label, payload in self.PAYLOADS.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                _claude_stub(tmp, payload)
                result = self._preflight(tmp)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("affects harness: claude-code", result.stderr)
                self.assertIn("→", result.stderr)

    def test_a_healthy_login_names_the_subscription_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _claude_stub(
                tmp, {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty"}
            )
            result = self._preflight(tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("claude-subscription", result.stdout)


class ClaudeIsolationTest(StateDirTest):
    def _prepare(self, evaluation_id: str) -> pathlib.Path:
        result = cli(
            [
                str(SCRIPTS / "prepare.py"),
                "--case",
                "catchup-branch-state",
                "--harness",
                "claude-code",
                # No harness is contacted, so the post-stage authentication
                # proof is skipped and this needs no `claude` on PATH.
                "--provider-double",
                "empty",
            ],
            {**self.env, "SKILL_EVAL_EVALUATION_ID": evaluation_id},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.state / "work" / evaluation_id

    def _codex_workspace(self) -> pathlib.Path:
        result = cli(
            [str(SCRIPTS / "prepare.py"), "--case", "catchup-branch-state"],
            {**self.env, "SKILL_EVAL_EVALUATION_ID": "codex-side"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.state / "work" / "codex-side" / "workspace"

    def test_the_trial_config_dir_holds_only_what_the_case_staged(self) -> None:
        work = self._prepare("claude-first")
        claude_home = work / "claude-home"

        self.assertEqual(sorted(p.name for p in (claude_home / "skills").iterdir()), ["catchup"])
        self.assertTrue((claude_home / ".credentials.json").is_symlink())
        self.assertTrue((claude_home / "projects").is_dir())
        self.assertEqual(list((claude_home / "projects").iterdir()), [])

        settings = json.loads((claude_home / "settings.json").read_text(encoding="utf-8"))
        self.assertIs(settings["syncClaudeAiSkills"], False)
        for forbidden in ("apiKey", "apiKeyHelper", "forceLoginMethod"):
            self.assertNotIn(forbidden, settings)

        for root in (claude_home, work / "workspace"):
            for forbidden in ("AGENTS.md", "CLAUDE.md", ".claude", ".codex"):
                self.assertEqual(list(root.rglob(forbidden)), [], f"{root.name}/{forbidden}")

    def test_both_harnesses_are_given_byte_identical_workspaces(self) -> None:
        claude = self._prepare("claude-second") / "workspace"
        codex = self._codex_workspace()

        def tree(root: pathlib.Path) -> dict[str, bytes]:
            return {
                str(path.relative_to(root)): path.read_bytes()
                for path in sorted(root.rglob("*"))
                if path.is_file() and ".git" not in path.parts
            }

        self.assertEqual(tree(claude), tree(codex))

    def test_no_credential_file_is_written_under_the_saved_evidence(self) -> None:
        self.double_trial(f"respond:{EXPECTATIONS / 'acceptable.md'}", "claude-code")
        self.assertEqual(list(self.runs.rglob("auth.json")), [])
        self.assertEqual(list(self.runs.rglob(".credentials.json")), [])


class ResourceIdentityTest(StateDirTest):
    def test_a_reported_model_identity_is_recorded_verbatim(self) -> None:
        _, trial = self.double_trial(
            f"respond:{EXPECTATIONS / 'acceptable.md'}",
            "claude-code",
            SKILL_EVAL_DOUBLE_MODEL_USAGE="claude-sonnet-5",
        )
        manifest = json.loads((trial["dir"] / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["model"]["resolved"], "claude-sonnet-5")
        self.assertIsNone(manifest["model"]["resolved_reason"])
        self.assertEqual(manifest["model"]["requested"], "sonnet")

    def test_a_missing_model_identity_is_admitted_rather_than_invented(self) -> None:
        _, trial = self.double_trial(f"respond:{EXPECTATIONS / 'acceptable.md'}", "claude-code")
        manifest = json.loads((trial["dir"] / "manifest.json").read_text(encoding="utf-8"))
        self.assertIsNone(manifest["model"]["resolved"])
        self.assertTrue(manifest["model"]["resolved_reason"])

    def test_skill_evidence_comes_from_the_provider_when_it_reports_any(self) -> None:
        _, trial = self.double_trial(f"respond:{EXPECTATIONS / 'acceptable.md'}", "claude-code")
        manifest = json.loads((trial["dir"] / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["skill_evidence"]["source"], "provider")
        self.assertEqual(
            [call["name"] for call in manifest["skill_evidence"]["calls"]], ["catchup"]
        )
        self.assertIsNone(manifest["skill_evidence"]["reason"])

        recorded = next(
            row for row in trial["outcome"]["assertions"] if row["type"] == "skill-used"
        )
        self.assertEqual([call["name"] for call in recorded["evidence"]], ["catchup"])

    def test_unavailable_skill_evidence_is_admitted_rather_than_denied(self) -> None:
        _, trial = self.double_trial("error:the harness fell over", "claude-code")
        manifest = json.loads((trial["dir"] / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["skill_evidence"]["calls"], [])
        self.assertTrue(manifest["skill_evidence"]["reason"])

    def test_cost_is_recorded_as_an_estimate_and_never_as_a_charge(self) -> None:
        _, trial = self.double_trial(f"respond:{EXPECTATIONS / 'acceptable.md'}", "claude-code")
        manifest = json.loads((trial["dir"] / "manifest.json").read_text(encoding="utf-8"))
        basis = manifest["cost_estimate"]["basis"]
        self.assertIn("estimate", basis)
        self.assertIn("not an invoice", basis)
        self.assertIn("quota", basis)

        for key in ("claude_cli", "claude_agent_sdk", "codex_cli", "codex_sdk"):
            self.assertIn(key, manifest["versions"])
        self.assertEqual(manifest["harness_context"]["conversation"], "fresh")


class FixtureDeterminismTest(unittest.TestCase):
    def test_two_builds_produce_the_same_head(self) -> None:
        heads = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                built = pathlib.Path(tmp) / "workspace"
                result = subprocess.run(
                    ["bash", str(FIXTURE_BUILD), str(built)],
                    capture_output=True,
                    text=True,
                    cwd=str(ROOT),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                heads.append(result.stdout.strip())
        self.assertEqual(heads[0], heads[1])
        self.assertTrue(heads[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
