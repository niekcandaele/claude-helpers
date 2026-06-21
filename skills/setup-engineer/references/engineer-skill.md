# The Per-Repo Engineer Skill

Every golden repo carries a `<repo>-engineer` skill at `.claude/skills/<repo>-engineer/`. Its
job is **orientation**, not command storage. Now that commands live in the CLI and `just`, the
skill gets thinner and sharper: it explains *why* the repo is shaped the way it is and *where*
the sharp edges are, then points at the executable surface for the *how*.

This is the shape akari (one 33 KB monolith) and takaro (eleven files + helper scripts) are both
migrated toward.

## The four-file floor

Every repo gets at least these four. A repo may add detail files (e.g. a `MODULES.md`) but never
drop below the floor.

```
.claude/skills/<repo>-engineer/
  SKILL.md         entry: what this repo is (1 paragraph) · the verb surface (→ `just --list`)
                   · golden-state invariants summary · the two behavioral laws
                   · a quick-reference table linking to the detail docs
  ARCHITECTURE.md  the WHY: services, the port/boundary model, auth flow, the multi-instance model
  TESTING.md       what each test type MEANS and when to reach for it (commands → `just test-*`)
  GOTCHAS.md       hard-won failure modes + debugging recipes (db queries → `just db`)
```

## Three rules that keep it from rotting

1. **Commands never live in the skill.** It points at `just --list` and the CLI `--help`. There
   is nothing to drift because the executable surface is the source of truth. If you catch
   yourself pasting a command block into the skill, that command belongs in the CLI instead.
2. **Domain language stays out.** The repo already has a `CONTEXT.md` glossary (the
   ubiquitous-language doc). The engineer skill is *operational*; it links to `CONTEXT.md` for
   *what the words mean* and never duplicates it.
3. **Zero scripts ship in the skill dir.** takaro's old skill bundled `psql-debug.sh`,
   `find-test.sh`, `ci-logs.sh` — those are redundant with `just db`, `just test-file`, and the
   CLI. Everything executable lives in the repo's CLI/justfile so there's one place to maintain.

## The two behavioral laws (installed into SKILL.md)

These live in the engineer skill's `SKILL.md` so **every** agent that later works in the repo
follows them ambiently, without anyone re-running setup-engineer. Write them in the agent's
voice, with the reasoning, not as bare commandments.

### Law 1 — Lifecycle hygiene

> You brought the environment up; you tear it down when you're finished. `just down` is the
> reflex when you stop working (it keeps your data and frees RAM). Use `just nuke` only when you
> actually want the data gone.
>
> **Why:** development happens across many headless instances at once. An environment left
> running after you've moved on eats RAM that another instance needs — leave enough of them up
> and the box runs out and everything suffers. Cleaning up after yourself is what makes running
> many instances in parallel possible. This applies to *every* task that starts the stack:
> tests, debugging, exercising a feature, a one-off check. Up means a later down.

### Law 2 — Self-improvement (executable-encoding-first)

> When you fight through friction in this repo, leave the tooling better than you found it — and
> push the fix to the most permanent layer that can hold it:
>
> | What you hit | Where the fix goes |
> |---|---|
> | A command was missing / wrong / a one-off incantation worked | add or fix a `just`/CLI verb |
> | You found an invariant that must never regress | add a `doctor` check |
> | A genuinely judgment-based failure mode / non-obvious gotcha | append to `GOTCHAS.md` |
> | Structural drift (a new service, etc.) | wire it correctly so `doctor` passes |
>
> Prefer executable encoding over prose: a verb or a `doctor` check is permanent and
> discoverable; a note is the fallback for things that truly can't be encoded. A fix that only
> lives in your memory of this session is a fix that's already lost.
>
> **Infra-change law:** when you add or change a service (datastore, queue, cache, IdP), in the
> *same* change you must add its port slot, its healthcheck, `nuke` coverage for its volume, and
> regenerate `.env`. `doctor` fails until all four are true — that's deliberate; it's how a whole
> class of "works on my machine, rots on the next" bugs is prevented.

## When restructuring an existing skill

Treat the old skill as source material, not garbage. The monolith already contains real,
verified knowledge — sort each section into the four-file floor (architecture → `ARCHITECTURE.md`,
test meaning → `TESTING.md`, sharp edges → `GOTCHAS.md`), move every command into the CLI/just,
move every bundled script into the CLI, link domain terms out to `CONTEXT.md`, and drop nothing
that's still true. Verify the engineer skill still answers "how do I run X" — the answer should
now be "`just …`".
