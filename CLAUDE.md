ALWAYS use the claude-provided tools/agents/skills/... that instruct you how to create claude code configs/prompts

# Development Instructions

## Available Commands

Run `just` to see available commands:

- `just validate` - Validate plugin structure and JSON syntax
- `just structure` - Show the plugin file tree
- `just test` - Show local testing instructions

## Making Changes

After modifying commands or agents, run `just validate` to ensure the plugin structure is correct.

Version bumping happens automatically via GitHub Actions on push to main.
