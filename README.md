# Skills

[![skills.sh](https://skills.sh/b/niekcandaele/skills)](https://skills.sh/niekcandaele/skills)

One engineer's development flow, written down as agent skills. Reviewing code,
driving a ticket to a merged PR, chasing down a root cause, arguing with a plan
before writing any of it.

```bash
npx skills add niekcandaele/skills
```

That lists everything and lets you pick. Take one skill, take the lot, or copy
the files straight into your own repo and edit them — that last one is
encouraged. This is shared, not published-and-defended.

## What's in here

**Quality** — reviewing code and proving it works.
`verify` `reviewer` `codex-reviewer` `comment-review` `qa` `ux-reviewer`
`visual-verify` `static-analysis` `tester` `exerciser`

**Ship** — getting work from a ticket to a merged pull request.
`epic-runner` `player-coach` `player` `create-pr` `review-pr` `check-ci`

**Investigate** — finding out what is actually going on, before changing anything.
`debugger` `root-cause-analysis` `root-cause-coach` `research` `wait-what`

**Design** — sharpening a plan, a domain language, or a repo's shape.
`grill-me` `ubiquitous-language` `improve-codebase-architecture` `setup-engineer`

**Session** — carrying context between sessions and between agents.
`catchup` `handoff`

**Write** — turning work into something a human wants to read.
`technical-writer` `writing-for-agents` `release-notes` `rich-page` `wizard`

## These are opinionated, and some of them are coupled

The groups above are for browsing. They are **not** install bundles.

Plenty of these stand alone — `reviewer`, `debugger`, `technical-writer` and
`wizard` need nothing else. But several are deliberately built to work together:
`verify` fans out to nine reviewer skills, and `player-coach` drives `player`,
`verify`, `create-pr` and `check-ci` in a loop. Installing one half of that gets
you a skill that calls something that isn't there.

Every skill that depends on another declares it in its frontmatter, so you can
check before installing:

```yaml
metadata:
  group: ship
  requires: [player, verify, create-pr, check-ci]
```

They also encode a particular way of working — adversarial review, evidence
before conclusions, a real end-to-end exercise before calling something done. If
that doesn't match how you work, edit them. They're prompts.

## Harnesses

Nothing here assumes a specific agent runtime. Where a skill needs a real
capability — spawning sub-agents, running background commands — it says so and
names a concrete binding as an example.

Some skills ask more of a harness than others. `verify` and `epic-runner` are
much faster somewhere that runs sub-agents in parallel, though both document
what to do when that isn't available. `codex-reviewer` shells out to the Codex
CLI and needs it installed. The rest are files and shell commands.

## Development

```bash
just validate    # layout, frontmatter, groupings, declared dependencies
just structure   # show the tree
just test        # local testing instructions
```

See [AGENTS.md](./AGENTS.md) for the house rules, [CONTEXT.md](./CONTEXT.md) for
what the words mean, and [NOTICE.md](./NOTICE.md) for what came from where.

MIT licensed.
