# Claude Code Skills

This repository is a plain source repository for Claude Code skills.

It is no longer a plugin marketplace or installer repository. The canonical layout is a flat `skills/` tree that you can sync into `~/.claude/skills/` or `.claude/skills/` with your own dotfiles or tooling.

## Layout

```text
skills/
  <skill-name>/
    SKILL.md
    ...optional support files...
```

Former commands are now regular skills. Former agents are now helper skills, usually with `context: fork` and `user-invocable: false`.

## Included Skills

Core workflows:
- `verify`
- `create-pr`
- `check-ci`
- `commit-and-push`
- `rebase`
- `review-pr`
- `create-issue`
- `write-docs`
- `setup-engineer`
- `handoff`
- `catchup`
- `ralph-execute`
- `release-notes`
- `grill-me`

Long-running orchestration:
- `player-coach`
- `root-cause-analysis`

Helper skills used by other skills:
- `reviewer`
- `codex-reviewer`
- `debugger`
- `exerciser`
- `qa`
- `researcher`
- `static-analysis`
- `tester`
- `ux-reviewer`
- `technical-writer`
- `player`
- `root-cause-coach`

Bundled-data skill:
- `kubecon-schedule`

## Using This Repo

This repo is intended to be consumed by copying or syncing `skills/*` into Claude Code's skill directories.

Common targets:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`

The repository itself intentionally stays agnostic about how that sync happens.

## Permissions

Several skills expect shell, git, GitHub CLI, and optional MCP access. The exact permission set depends on which skills you use.

Examples:
- `create-pr`, `commit-and-push`, `rebase`, and `check-ci` need git and `gh` access.
- `codex-reviewer` needs the local `codex` CLI.
- `debugger`, `tester`, `ux-reviewer`, and `exerciser` can benefit from Playwright MCP.

## Development

```bash
just validate
just structure
just test
```

`just validate` checks the flat skill layout and rejects leftover plugin-era references.
