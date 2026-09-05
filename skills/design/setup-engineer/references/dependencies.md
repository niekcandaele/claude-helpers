# The dependency binding

`renovator` sweeps a repository's open dependency PRs unattended — tiering each by risk,
merging the safe ones, researching and verifying the rest. It stays deliberately generic: it
knows that a major runtime bump is riskier than a patch, and nothing at all about which
package broke this repository last spring, or which of its test verbs actually proves a
bundler upgrade.

That knowledge is the repository's, so it is written down once, by `setup-engineer`, as
**`DEPENDENCIES.md` alongside the engineer skill** — the same place `TRACKER.md`,
`TESTING.md`, and `GOTCHAS.md` already live.

`DEPENDENCIES.md` is **optional for golden state**: a repository with no dependency bot needs
no binding, and stays golden without one. It differs from `TRACKER.md` in what absence means
downstream — a skill that finds no `TRACKER.md` resolves the tracker itself and carries on,
while `renovator` refuses to run without `DEPENDENCIES.md` and says so. That is deliberate:
merging someone's dependencies on generic defaults alone is exactly the autonomy nobody
granted. So write this file when the repository has a bot, and leave it out when it does not.

## Drafting it

Read before asking, then ask freely — asking is free during `setup-engineer` and impossible
during an unattended sweep.

- **The bot's own config**, found by pattern rather than by one filename — Renovate reads
  `renovate.json`, `renovate.json5`, `.renovaterc*`, a `.github/` or `.gitlab/` copy of any of
  them, and a `renovate` key in `package.json`; Dependabot reads `.github/dependabot.yml`.
  What it already automerges, groups, or ignores is half the tiering answer, and renovator
  stands back from the sets it automerges.
- **Any ADR or scheduling discipline the repository has written about its bot.** A repository
  that has thought about dependency scheduling has usually written down why, and that
  reasoning outranks any generic default renovator carries.
- **The manifest**, for which packages are runtime and which are only development.
- **`TESTING.md` and `just --list`**, for the verbs each role's verification can name. Every
  command in this file must resolve to a real verb.
- **CI workflows**, for what already runs on every dependency PR — verification CI performs
  is verification renovator inherits.
- **`GOTCHAS.md`**, for the packages this repository has already been burned by.

**Run each verb once** before writing it down, exactly as with `TRACKER.md`: a verb that
resolves but fails is the failure mode this catches.

**Record gaps as "not available" lines.** A repository with no end-to-end suite should say so
rather than leave the row blank — renovator reads a stated absence as a known bound and an
empty row as an oversight worth reporting.

## The file

```markdown
# Dependencies

**Bot:** renovate (`renovate.json`) — groups `@types/*`, automerges its own patch updates
**Manifest:** `package.json` + `package-lock.json` at the root; `apps/docs` has its own

## Tier adjustments

| Package or pattern | Tier | Why |
|---|---|---|
| `playwright`, `@playwright/*` | guarded | browser downloads drift from the pinned image; every past minor needed a Dockerfile change |
| `@types/*` | trivial | types only, and the typecheck verb catches everything they can break |
| `apps/docs/**` | trivial | the docs site does not ship with the product |
| `fastify`, `@fastify/*` | guarded | plugin encapsulation changes have broken routing twice |

## Verification by role

| Role | Command | Notes |
|---|---|---|
| lockfile | `just test-unit` | after `just up`, which reinstalls |
| lint or types | `just lint` | typecheck is inside this verb |
| test-time | `just test` | unit + integration + e2e report as one; a single failure fails the lot |
| build-time | `just build && just test-e2e` | a green build proves nothing on its own here |
| runtime | `just test` then exercise the affected route | see `API.md` for authenticating |
| engine or base image | `just nuke && just up && just test` | the only path that rebuilds the image |
| CI action | not available locally — CI on the PR is the whole proof |

## Fragile areas

- The `just test` report merges unit, integration, and Playwright output into one summary.
  Read the failing suite name from the body, not the exit code.
- Anything touching `@fastify/*` needs the integration suite, not the unit suite: the unit
  tests stub the server.
- The e2e suite needs `ENV_INDEX` set; two of them at once on the same index will interfere.

## Write bound

Default — lockfile regeneration, renamed config options, import path renames, type fixes, and
snapshot updates, one attempt. Leave `apps/docs` snapshots alone; they are reviewed by hand.

## Scheduling

**Rebase:** `serial`, `wide`, or `owned by <name>`. Here: owned by the merge train, which
schedules Renovate branches one at a time — `development` requires up-to-date branches and
the suite runs ~50m on three self-hosted runners, so a blanket rebase costs N(N+1)/2 runs.
See ADR-0014. Renovator requests no rebases in this repo.
**Patience:** 45 minutes; Renovate's `rebaseWhen` is `conflicted`, so a nudge is a body edit
and the branch rebuilds on the bot's own next cycle.
**Bot automerge:** patch and minor, by update type only — no role awareness. Engine and
base-image bumps land unreviewed under it; renovator comments on those rather than merging.
```

Four sections, and each answers a question renovator would otherwise guess at:

- **Tier adjustments** override the generic matrix, and every row carries its reason. The
  reason is what a maintainer reads six months later to decide whether the row still holds.
- **Verification by role** points at `just` verbs rather than repeating them, so the CLI stays
  the single source of truth for what a command does.
- **Fragile areas** is prose, because the useful thing here rarely fits a table — the merged
  test report, the suite that stubs the thing being upgraded, the flake with a known cause.
- **The write bound** says how far renovator may go in fixing a bot branch. "Default" accepts
  the skill's own bound; anything else narrows it.
- **Scheduling** is where a repository's own arithmetic about CI cost lives. Renovator
  serializes rebases by default because strict required checks make blanket rebasing
  quadratic. Three answers are meaningful: `serial` accepts that default, `wide` says the
  target does not gate on up-to-dateness, and `owned by <name>` hands rebasing to a scheduler
  the repository already runs — renovator then requests none and works the PRs as it finds
  them. A repository that has measured this has almost always written down why; cite that
  document here rather than restating it, and renovator follows instead of re-deriving it.

## Keeping it true

This file caches what the environment cannot tell you by looking: which packages have hurt
before, and which verb genuinely proves which kind of change. That is what makes it worth
writing, and what makes it capable of going stale.

A command in it that no longer resolves to a `just` verb is drift — fix the file rather than
route around it. And a verification gap renovator reports in its run table is a row this file
is missing: add it, and the next sweep verifies where this one could only comment.
