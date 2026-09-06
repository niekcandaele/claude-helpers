#!/usr/bin/env python3
"""Discover and validate evaluation cases.

A case is, in substance, a Promptfoo test: prompt vars plus an `assert` list.
This module is the deterministic half of the evaluation workflow — it never
calls a model, never reads credentials and needs nothing but python3 and pyyaml,
so `just validate` and CI can run it with no harness installed.

Failures follow scripts/validate.py's idiom: collect every one, then report,
and state a remedy for each.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
# SKILL_EVAL_CASES_DIR lets the test suite point discovery at a throwaway tree
# of deliberately broken cases without writing them into the repository.
CASES_DIR = pathlib.Path(os.environ.get("SKILL_EVAL_CASES_DIR") or ROOT / "evals" / "cases")
FIXTURES_DIR = ROOT / "evals" / "fixtures"
SKILLS_DIR = ROOT / "skills"

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

KNOWN_KEYS = {
    "id",
    "skill",
    "kind",
    "harnesses",
    "fixture",
    "task",
    "invocation",
    "expected_behavior",
    "assert",
}

# Widened by later tickets; today one kind is implemented, and a case that
# claims more would be silently mis-executed.
SUPPORTED_KINDS = {"behavior"}
SUPPORTED_HARNESSES = {"codex", "claude-code"}

# Convenience words the CLI accepts for --harness. A case file must name its
# harnesses literally: an alias in a case would silently widen as harnesses are
# added, changing what an old case measures.
HARNESS_ALIASES = {
    "both": ("codex", "claude-code"),
    "all": ("codex", "claude-code"),
}

# A case's prose is sent verbatim to every selected harness, so naming one
# harness in it makes the comparison unfair in a way nothing downstream can
# detect. Matched case-insensitively against task, invocation and
# expected_behavior.
HARNESS_VOCABULARY = (
    "codex",
    "claude code",
    "claude-code",
    "chatgpt",
    "anthropic",
    "openai",
    ".codex/",
    ".claude/",
    "codex_home",
    "claude_config_dir",
)

# The arms an evaluation can send. Only `candidate` is executed today; the
# baseline arms are what compose_prompt() exists to keep separable.
ARMS = {"candidate", "no-skill"}


class Case:
    """One evaluation case, as read from disk."""

    def __init__(self, path: pathlib.Path, data: dict):
        self.path = path
        self.dir = path.parent
        self.data = data

    @property
    def id(self) -> str:
        return str(self.data.get("id", self.dir.name))

    @property
    def skill(self) -> str:
        return str(self.data.get("skill", ""))

    @property
    def kind(self) -> str:
        return str(self.data.get("kind", ""))

    @property
    def harnesses(self) -> list[str]:
        value = self.data.get("harnesses", [])
        return [str(h) for h in value] if isinstance(value, list) else []

    @property
    def fixture(self) -> str:
        return str(self.data.get("fixture", ""))

    @property
    def asserts(self) -> list[dict]:
        value = self.data.get("assert", [])
        return [a for a in value if isinstance(a, dict)] if isinstance(value, list) else []

    def fixture_build(self) -> pathlib.Path:
        return FIXTURES_DIR / self.fixture / "build.sh"

    def fixture_manifest(self) -> pathlib.Path:
        return FIXTURES_DIR / self.fixture / "manifest.json"


def skill_dir(name: str) -> pathlib.Path | None:
    for candidate in sorted(SKILLS_DIR.glob(f"*/{name}")):
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def discover() -> list[Case]:
    """Every case on disk, ordered by path. Unparseable files are skipped here
    and reported by validate_all()."""
    cases = []
    for path in sorted(CASES_DIR.glob("*/case.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        if isinstance(data, dict):
            cases.append(Case(path, data))
    return cases


def load(case_id: str) -> Case:
    """The one case with this id, or SystemExit naming what is available."""
    for case in discover():
        if case.id == case_id:
            return case
    known = ", ".join(sorted(c.id for c in discover())) or "none"
    raise SystemExit(
        f"✗ no evaluation case with id '{case_id}'\n"
        f"    → run 'just eval-list' to see the cases that exist ({known})"
    )


def resolve_harnesses(spec: str) -> list[str]:
    """Turn a --harness argument into the ordered harness list it selects.

    Accepts one name, a comma-separated list, or an alias. Order is stable and
    de-duplicated, because it decides the order the trials execute in.
    """
    selected: list[str] = []
    for token in (part.strip() for part in spec.split(",")):
        if not token:
            continue
        for name in HARNESS_ALIASES.get(token, (token,)):
            if name not in selected:
                selected.append(name)
    unknown = [name for name in selected if name not in SUPPORTED_HARNESSES]
    if unknown or not selected:
        known = ", ".join(sorted(SUPPORTED_HARNESSES) + sorted(HARNESS_ALIASES))
        raise SystemExit(
            f"✗ unknown harness selection '{spec}'\n"
            f"    → use one or more of: {known}"
        )
    return selected


# How each harness is asked to load a skill. The case states its invocation
# once, in neutral prose; this is the only place it is translated, and the
# translation is confined to *how the skill is summoned* — the task itself is
# byte-identical on every harness, which is what makes the results comparable.
#
# Claude Code honours a skill's own `disable-model-invocation: true`
# frontmatter, so prose asking it to use such a skill is refused outright,
# while the slash form a person would type still loads it. Codex ignores that
# frontmatter and takes the prose. Translating here is what keeps the case from
# having to know either fact.
INVOCATION_FORMS = {"codex": "{invocation}", "claude-code": "/{skill}"}


def compose_invocation(case: Case, harness: str = "codex") -> str:
    """The sentence that summons the skill, in the form this harness accepts."""
    invocation = str(case.data.get("invocation", "")).strip()
    if not invocation:
        return ""
    form = INVOCATION_FORMS.get(harness, "{invocation}")
    return form.format(invocation=invocation, skill=case.skill)


def compose_prompt(case: Case, arm: str = "candidate", *, harness: str = "codex") -> str:
    """The exact request text for one arm.

    This is the only place the invocation and the task are joined, so a
    baseline arm that must send the task alone stays one argument away.
    """
    if arm not in ARMS:
        raise ValueError(f"unknown arm '{arm}'; expected one of {sorted(ARMS)}")
    task = str(case.data.get("task", "")).strip()
    if arm == "no-skill":
        return task
    invocation = compose_invocation(case, harness)
    return f"{invocation}\n\n{task}" if invocation else task


def _validate_case(case: Case, seen_ids: dict[str, pathlib.Path]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    path = case.path
    data = case.data

    def fail(message: str, remedy: str) -> None:
        failures.append((f"{path}: {message}", remedy))

    unknown = sorted(set(data) - KNOWN_KEYS)
    if unknown:
        fail(
            f"unknown top-level key(s): {', '.join(unknown)}",
            f"remove them or fix the typo — the schema is {', '.join(sorted(KNOWN_KEYS))}",
        )

    case_id = data.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        fail("'id' is missing or not a non-empty string", "add an id: matching the directory name")
    else:
        if not ID_PATTERN.match(case_id):
            fail(
                f"id '{case_id}' is not lowercase-kebab",
                "use lowercase letters, digits and hyphens, starting with a letter or digit",
            )
        if case_id != case.dir.name:
            fail(
                f"id '{case_id}' != directory '{case.dir.name}'",
                "make them identical — saved results are keyed on the id",
            )
        if case_id in seen_ids:
            fail(
                f"duplicate case id '{case_id}', also at {seen_ids[case_id]}",
                "rename one — results from two cases would collide",
            )
        else:
            seen_ids[case_id] = path

    skill = data.get("skill")
    if not isinstance(skill, str) or not skill.strip():
        fail("'skill' is missing or not a non-empty string", "name the skill under evaluation")
    elif skill_dir(skill) is None:
        fail(
            f"skill '{skill}' does not exist",
            f"point it at a skill directory: skills/<group>/{skill}/SKILL.md",
        )

    kind = data.get("kind")
    if kind not in SUPPORTED_KINDS:
        fail(
            f"kind {kind!r} is not supported",
            f"use one of {', '.join(sorted(SUPPORTED_KINDS))}",
        )

    harnesses = data.get("harnesses")
    if not isinstance(harnesses, list) or not harnesses:
        fail("'harnesses' is missing or not a non-empty list", "write it as [codex, claude-code]")
    else:
        names = [str(h) for h in harnesses]
        unsupported = sorted(set(names) - SUPPORTED_HARNESSES)
        if unsupported:
            fail(
                f"harness(es) not supported yet: {', '.join(unsupported)}",
                f"use only {', '.join(sorted(SUPPORTED_HARNESSES))}",
            )
        for name in sorted({n for n in names if names.count(n) > 1}):
            fail(f"duplicate harness '{name}'", "list each harness once")

    task = data.get("task")
    if not isinstance(task, str) or not task.strip():
        fail("'task' is missing or not a non-empty string", "describe the underlying request")

    invocation = data.get("invocation")
    if kind == "behavior":
        if not isinstance(invocation, str) or not invocation.strip():
            fail(
                "'invocation' is missing or not a non-empty string",
                "a behavior case names the skill explicitly, e.g. 'Use the catchup skill.'",
            )
        elif isinstance(task, str) and invocation.strip() and invocation.strip() in task:
            fail(
                "'invocation' text is contained in 'task'",
                "keep them separate — a baseline arm sends the task without the invocation",
            )

    expected = data.get("expected_behavior")
    if not isinstance(expected, str) or not expected.strip():
        fail(
            "'expected_behavior' is missing or not a non-empty string",
            "state what a good response reports, in prose",
        )

    fixture = data.get("fixture")
    if not isinstance(fixture, str) or not fixture.strip():
        fail("'fixture' is missing or not a non-empty string", "name a directory under evals/fixtures/")
    elif not case.fixture_build().is_file():
        fail(
            f"fixture '{fixture}' has no builder",
            f"create {case.fixture_build().relative_to(ROOT)}",
        )

    for field in ("task", "invocation", "expected_behavior"):
        text = data.get(field)
        if not isinstance(text, str):
            continue
        lowered = text.lower()
        named = sorted({word for word in HARNESS_VOCABULARY if word in lowered})
        if named:
            fail(
                f"'{field}' names a harness: {', '.join(named)}",
                "state the behaviour, not the harness — the same text is sent to every "
                "selected harness",
            )

    asserts = data.get("assert")
    if not isinstance(asserts, list) or not asserts:
        fail("'assert' is missing or empty", "add at least one Promptfoo assertion")
    else:
        weighted = 0
        for index, entry in enumerate(asserts):
            where = f"assert[{index}]"
            if not isinstance(entry, dict):
                fail(f"{where} is not a mapping", "write each assertion as key: value pairs")
                continue
            atype = entry.get("type")
            if not isinstance(atype, str) or not atype.strip():
                fail(f"{where} has no 'type'", "every Promptfoo assertion needs a type")
            if entry.get("weight", 1) != 0:
                weighted += 1
            value = entry.get("value")
            if atype == "javascript" and isinstance(value, str) and value.startswith("file://"):
                target = (case.dir / value[len("file://") :]).resolve()
                if not target.is_file():
                    fail(
                        f"{where} points at a missing module: {value}",
                        f"create {target}, or fix the path (it resolves from {case.dir})",
                    )
        if weighted == 0:
            fail(
                "every assertion has weight 0",
                "give at least one assertion a non-zero weight — a case that cannot fail cannot pass",
            )

    return failures


def validate_all() -> list[tuple[str, str]]:
    """Every problem across every case, as (message, remedy) pairs."""
    failures: list[tuple[str, str]] = []
    if not CASES_DIR.is_dir():
        return failures

    for path in sorted(CASES_DIR.glob("*/case.yaml")):
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append((f"{path}: cannot be read ({exc})", "fix the permissions or the path"))
            continue
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            detail = str(exc).splitlines()[0]
            failures.append(
                (f"{path}: not valid YAML ({detail})", "quote any value containing ': ' or use a >- block scalar")
            )
            continue
        if not isinstance(data, dict):
            failures.append((f"{path}: is not a mapping", "write the case as key: value pairs"))
            continue

    seen_ids: dict[str, pathlib.Path] = {}
    for case in discover():
        failures.extend(_validate_case(case, seen_ids))

    for case_dir in sorted(p for p in CASES_DIR.glob("*") if p.is_dir()):
        if not (case_dir / "case.yaml").is_file():
            failures.append(
                (f"{case_dir}: no case.yaml", "every case directory needs one, or remove the directory")
            )

    return failures


def _cmd_list() -> int:
    cases = discover()
    if not cases:
        print("no evaluation cases found")
        return 0
    width = max(len(c.id) for c in cases)
    for case in cases:
        print(f"{case.id.ljust(width)}  skill={case.skill}  kind={case.kind}  harnesses={','.join(case.harnesses)}")
    return 0


def _cmd_validate() -> int:
    failures = validate_all()
    if failures:
        print(f"✗ {len(failures)} problem(s) in evaluation cases:\n", file=sys.stderr)
        for message, remedy in failures:
            print(f"  {message}\n    → {remedy}\n", file=sys.stderr)
        return 1
    print(f"✓ {len(discover())} evaluation case(s) valid")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="list every case")
    group.add_argument("--validate", action="store_true", help="validate every case")
    args = parser.parse_args(argv)
    return _cmd_list() if args.list else _cmd_validate()


if __name__ == "__main__":
    sys.exit(main())
