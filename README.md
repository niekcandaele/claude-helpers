# Skills Repository

This repository is a source repo for reusable skills.

It keeps a flat `skills/` tree, with one directory per skill and `SKILL.md` as the entrypoint. Some skills also ship supporting files alongside the main prompt.

## Layout

```text
skills/
  <skill-name>/
    SKILL.md
    ...optional support files...
```

## Consumption

The expected workflow is to sync or copy `skills/*` into whatever environment should consume them. This repo stays agnostic about how that sync happens.

Compatibility note:
- Claude-compatible skill directories typically use `~/.claude/skills/` for personal skills and `.claude/skills/` for project-local skills.

## Development

```bash
just validate
just structure
just test
```

`just validate` checks the flat skill layout and catches leftover legacy references.
