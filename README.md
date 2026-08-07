# Skills

[![skills.sh](https://skills.sh/b/niekcandaele/skills)](https://skills.sh/niekcandaele/skills)

One engineer's development flow, written down as agent skills. Reviewing code,
driving a ticket to a merged PR, chasing down a root cause, arguing with a plan
before writing any of it.

```bash
npx skills add niekcandaele/skills --list   # see what's here
npx skills add niekcandaele/skills          # pick what you want
```

Take one skill, take the lot, or copy the files straight into your own repo and
edit them — that last one is encouraged. This is shared, not published-and-defended.

## What using one looks like

Skills are invoked by name. Once installed, ask for one directly:

```
/verify --scope=branch
```

`verify` then works out what changed, hands each reviewer the files it cares
about, runs them, and hands back one deduplicated report with severities — rather
than eight separate opinions you have to reconcile yourself. Most skills are that
shape: one command, a lot of machinery behind it, one answer.

Others are conversational. `/grill-me` interrogates a plan until it stops being
vague. `/wait-what` just tells you the last thing you said didn't land.

## What's in here

**Quality** — reviewing code and proving it works.
`verify` `reviewer` `codex-reviewer` `comment-review` `qa` `ux-reviewer`
`visual-verify` `static-analysis` `tester` `exerciser`

**Ship** — getting work from a ticket to a merged pull request.
`epic-runner` `player-coach` `player` `create-pr` `review-pr` `check-ci`
`resolving-merge-conflicts`

**Investigate** — finding out what is actually going on, before changing anything.
`debugger` `root-cause-analysis` `root-cause-coach` `research` `wait-what`

**Design** — sharpening a plan, a domain language, or a repo's shape.
`grill-me` `ubiquitous-language` `codebase-design` `improve-codebase-architecture`
`setup-engineer`

**Plan** — turning a loose idea into decisions, a spec, and tickets an agent can pick up.
`wayfinder` `prototype` `to-spec` `to-tickets`

**Session** — carrying context between sessions and between agents.
`catchup` `handoff`

**Write** — turning work into something a human wants to read.
`technical-writer` `writing-for-agents` `release-notes` `rich-page` `wizard`

## Some of these only work together

The groups above are for browsing. They are **not** install bundles — coupling
crosses group boundaries.

Nine skills call others and will not work alone:

| Skill | Needs |
|---|---|
| `verify` | `reviewer` `codex-reviewer` `comment-review` `qa` `tester` `ux-reviewer` `visual-verify` `static-analysis` `exerciser` `debugger` |
| `player-coach` | `player` `verify` `create-pr` `check-ci` (and everything `verify` needs) |
| `review-pr` | `reviewer` `tester` `ux-reviewer` `exerciser` |
| `epic-runner` | `player-coach` `check-ci` (and everything they need) |
| `check-ci` | `debugger` |
| `root-cause-analysis` | `root-cause-coach` |
| `research` | `rich-page`, but only in `--deep` mode |
| `improve-codebase-architecture` | `codebase-design`; `rich-page` and `grill-me` improve it |
| `wayfinder` | `grill-me`; `research` and `prototype` improve it |

Note `check-ci` — it looks self-contained sitting in the Ship list, and it isn't.
Everything not in that table stands alone: `reviewer`, `debugger`,
`technical-writer`, `wizard`, `prototype`, `to-spec`, `to-tickets`, `catchup` and
the rest need nothing else.

They form a flow all the same, even where nothing is declared: `wayfinder` charts a
big effort, `to-spec` writes up what was decided, `to-tickets` cuts it into slices
and leaves you one handle, and `epic-runner` takes that handle and works them. Each
step is yours to invoke — none of them fires the next.

Four skills also read a `TRACKER.md` beside the repo's engineer skill — `wayfinder`,
`to-spec`, `to-tickets`, `epic-runner`. `setup-engineer` writes it. None of them
require it: without one they resolve the tracker themselves for that run.

Each of these declares its dependencies in frontmatter, so you can check any skill
before installing it:

```yaml
metadata:
  group: ship
  requires: [player, verify, create-pr, check-ci]
```

They also encode a particular way of working — adversarial review, evidence before
conclusions, a real end-to-end exercise before calling something done. If that
doesn't match how you work, edit them. They're prompts.

## Harnesses

The prose in these skills assumes no specific agent runtime. Where a skill needs a
real capability — spawning sub-agents, running background commands — it says so
and names a concrete binding as an example rather than depending on it.

Frontmatter is a different matter: keys like `allowed-tools`, `context` and
`argument-hint` are each harness's own interface, and the tool names inside them
are specific. Harnesses ignore keys they don't recognize, so this costs you
nothing, but it does mean the files aren't runtime-agnostic all the way down.

Some skills also ask more than others. `verify` and `epic-runner` are much faster
where sub-agents run in parallel, though both document what to do when they can't.
`codex-reviewer` shells out to the Codex CLI and needs it installed.

## Development

```bash
just validate    # layout, frontmatter, groupings, declared dependencies
just structure   # show the tree
just try --list  # install from this checkout to try it
```

`just validate` needs `python3` with `pyyaml`, plus `jq`. It runs in CI on every
pull request.

See [AGENTS.md](./AGENTS.md) for the house rules, [CONTEXT.md](./CONTEXT.md) for
what the words mean, and [NOTICE.md](./NOTICE.md) for what came from where.

[MIT licensed](./LICENSE) — including the parts that came from elsewhere.
