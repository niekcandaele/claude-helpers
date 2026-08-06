When creating or editing a skill, use the `writing-for-agents` skill in this repo.

# Development Instructions

## Available Commands

Run `just` to see available commands:

- `just validate` - Validate the grouped `skills/` layout, the skills.sh.json
  mirror, declared dependencies, and legacy references
- `just structure` - Show the skills file tree
- `just test` - Show local testing instructions

## Making Changes

After modifying any skill or supporting file, run `just validate`.

Adding a skill means three things, and `just validate` fails if you miss one:

1. `skills/<group>/<name>/SKILL.md`, with `name` and `description` frontmatter
2. `metadata.group` in that frontmatter matching the parent directory
3. The skill listed under the matching grouping in `skills.sh.json`

If the skill invokes other skills in this repo, declare them in
`metadata.requires` — every name there must resolve to a real skill.

## House rules

Skills here are **harness-neutral**. They do not assume a specific agent
runtime's directory layout, tool names, or built-in agent types. Where a skill
genuinely needs a runtime capability, it states the capability first and names a
specific harness only as an example binding.

Do not pin models in frontmatter. State a cost tier in prose instead — the
orchestrator picks the model, because only it knows how hard the task is.

This repository is a source repo for skills only. Do not reintroduce plugin
packaging, marketplace metadata, installer scripts, or repo-specific CI /
version-bump logic.
