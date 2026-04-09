ALWAYS use the claude-provided tools/agents/skills/... that instruct you how to create claude code configs/prompts

# Development Instructions

## Available Commands

Run `just` to see available commands:

- `just validate` - Validate the flat `skills/` layout and catch legacy references
- `just structure` - Show the skills file tree
- `just test` - Show local testing/sync instructions

## Making Changes

After modifying any skill or supporting file, run `just validate`.

This repository is a source repo for skills only. Do not reintroduce plugin packaging, marketplace metadata, installer scripts, or repo-specific CI/version-bump logic.
