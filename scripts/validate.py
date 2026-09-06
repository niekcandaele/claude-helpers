#!/usr/bin/env python3
"""Validate the skills tree.

Every check runs even when an earlier one fails, so a single pass reports every
problem at once. Each failure states what to do about it, not just what is wrong.

The frontmatter check parses YAML for real. A grep for `description:` cannot tell
a valid document from one the skills CLI will silently skip on install, and a
silently skipped skill is the failure mode this repo has actually shipped.
"""

import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
CONFIG = ROOT / "skills.sh.json"
LEGACY = re.compile(r"/plugin|/cata-helpers:|\.claude-plugin|plugins/|cata-")
# An upstream repo that happens to be named "plugins" is a credit, not packaging.
UPSTREAM = re.compile(r"https://github\.com/[\w.-]+/plugins\b")

errors: list[str] = []


def fail(message: str, remedy: str) -> None:
    errors.append(f"{message}\n    → {remedy}")


def parse_frontmatter(path: pathlib.Path):
    """Return the frontmatter mapping, or None after recording why it failed."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(
            f"{path}: no frontmatter at line 1",
            "the file must begin with a --- delimiter on its very first line",
        )
        return None
    end = text.find("\n---\n", 3)
    if end == -1:
        fail(
            f"{path}: frontmatter is never closed",
            "add a closing --- delimiter on its own line",
        )
        return None
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        detail = str(exc).splitlines()[0]
        fail(
            f"{path}: frontmatter is not valid YAML ({detail})",
            "quote any value containing ': ' or use a >- block scalar; "
            "the skills CLI silently skips a skill it cannot parse",
        )
        return None
    if not isinstance(data, dict):
        fail(f"{path}: frontmatter is not a mapping", "write it as key: value pairs")
        return None
    return data


def main() -> int:
    if not SKILLS.is_dir():
        fail("skills/ directory is missing", "create it")
        return report()

    groups = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    if not groups:
        fail("skills/ has no group directories", "create one, e.g. skills/quality/")
        return report()

    for stray in sorted(SKILLS.glob("*/SKILL.md")):
        fail(
            f"{stray}: skill sits at the top level",
            "move it into a group directory: skills/<group>/<name>/SKILL.md",
        )
    for stray in sorted(p for p in SKILLS.iterdir() if p.is_file()):
        fail(f"{stray}: stray file in skills/", "skills/ holds only group directories")

    skill_dirs = sorted(p for p in SKILLS.glob("*/*") if p.is_dir())
    seen: dict[str, pathlib.Path] = {}
    on_disk: set[str] = set()
    declared_deps: list[tuple[pathlib.Path, str, str]] = []

    for skill_dir in skill_dirs:
        name = skill_dir.name
        group = skill_dir.parent.name
        on_disk.add(f"{group}/{name}")

        # Installation flattens group directories, so two skills sharing a
        # basename would overwrite each other for every consumer.
        if name in seen:
            fail(
                f"{skill_dir}: duplicate skill name, also at {seen[name]}",
                "rename one — installation flattens groups, so identical "
                "basenames silently overwrite each other",
            )
        seen[name] = skill_dir

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            fail(f"{skill_dir}: no SKILL.md", "every skill directory needs one")
            continue

        data = parse_frontmatter(skill_md)
        if data is None:
            continue

        for key in ("name", "description"):
            value = data.get(key)
            if not isinstance(value, str) or not value.strip():
                fail(
                    f"{skill_md}: frontmatter '{key}' missing or not a string",
                    f"add a non-empty {key}: — the skills CLI requires it",
                )

        if isinstance(data.get("name"), str) and data["name"] != name:
            fail(
                f"{skill_md}: frontmatter name '{data['name']}' != directory '{name}'",
                "make them identical — the CLI installs by frontmatter name, "
                "while groupings and dependencies key off the directory",
            )

        metadata = data.get("metadata")
        if not isinstance(metadata, dict) or "group" not in metadata:
            fail(
                f"{skill_md}: no metadata.group",
                f"add:\n        metadata:\n          group: {group}",
            )
        elif metadata["group"] != group:
            fail(
                f"{skill_md}: metadata.group '{metadata['group']}' != directory '{group}'",
                f"change it to {group}, or move the skill to skills/{metadata['group']}/",
            )

        if isinstance(metadata, dict):
            for key in ("requires", "optional"):
                deps = metadata.get(key, [])
                if deps and not isinstance(deps, list):
                    fail(
                        f"{skill_md}: metadata.{key} is not a list",
                        "write it as [a, b] or a YAML block list",
                    )
                    continue
                for dep in deps:
                    declared_deps.append((skill_md, key, str(dep)))

    known = set(seen)
    for skill_md, key, dep in declared_deps:
        if dep not in known:
            fail(
                f"{skill_md}: metadata.{key} names unknown skill '{dep}'",
                "fix the typo, create the skill, or drop the dependency",
            )

    # skills.sh.json drives the published page, so it must match the tree exactly.
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{CONFIG}: {exc}", "fix the JSON")
    else:
        listed: set[str] = set()
        for grouping in config.get("groupings", []):
            title = grouping.get("title", "").lower()
            for skill in grouping.get("skills", []):
                listed.add(f"{title}/{skill}")
        for entry in sorted(on_disk - listed):
            group, _, name = entry.partition("/")
            fail(
                f"{entry}: on disk but not in skills.sh.json",
                f"add '{name}' to the '{group}' grouping in skills.sh.json",
            )
        for entry in sorted(listed - on_disk):
            group, _, name = entry.partition("/")
            fail(
                f"{entry}: in skills.sh.json but not on disk",
                f"create skills/{group}/{name}/, or remove the entry "
                "(a rename shows up as one of these plus one of the above)",
            )

    for path in sorted(list(ROOT.glob("*.md")) + list(SKILLS.rglob("*"))):
        if not path.is_file() or path.suffix not in {".md", ".json", ".sh"}:
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if LEGACY.search(line) and not UPSTREAM.search(line):
                fail(
                    f"{path}:{lineno}: plugin-era reference",
                    "this repo is a source repo for skills only — remove it",
                )

    validate_evaluation_cases()

    return report()


def validate_evaluation_cases() -> None:
    """Fold the evaluation cases' own checks into this gate.

    Skipped silently when evals/ is absent, so the validator keeps working if
    the directory is ever removed. Pure python and pyyaml — CI needs no harness
    to run the gate.
    """
    if not (ROOT / "evals" / "cases").is_dir():
        return
    sys.path.insert(0, str(ROOT / "scripts" / "evals"))
    import cases as evaluation_cases

    for message, remedy in evaluation_cases.validate_all():
        fail(message, remedy)


def report() -> int:
    if errors:
        print(f"✗ {len(errors)} problem(s):\n", file=sys.stderr)
        for error in errors:
            print(f"  {error}\n", file=sys.stderr)
        return 1

    skills = sorted(p for p in SKILLS.glob("*/*") if p.is_dir())
    groups = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    print(f"✓ {len(skills)} skills in {len(groups)} groups")
    print("✓ Every skill has a SKILL.md whose frontmatter parses as YAML")
    print("✓ Every skill's name matches its directory, and all names are unique")
    print("✓ Every metadata.group matches its directory")
    print("✓ Every declared dependency names a skill that exists")
    print("✓ skills.sh.json matches the tree in both directions")
    print("✓ No plugin-era references")

    if (ROOT / "evals" / "cases").is_dir():
        sys.path.insert(0, str(ROOT / "scripts" / "evals"))
        import cases as evaluation_cases

        count = len(evaluation_cases.discover())
        print(
            f"✓ {count} evaluation case(s), each with a stable id, a real skill, "
            "a built fixture, and a graded assertion"
        )

    print("\n✓ Skill validation passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
