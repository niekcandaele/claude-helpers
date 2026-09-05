# Tiering a dependency PR

The tier is a **ceiling**, not a verdict: it says what the sweep may do to this PR without a
human, and the verdict says what it did. Decide it once per PR in Phase 1, from the generic
matrix, then let `DEPENDENCIES.md` and invocation steering move it.

## The matrix

Read the bump kind down, the dependency's role across. Role derivation lives in
[verification.md](verification.md).

| Bump kind | lint, types, docs | test-time, build-time | runtime | engine, base image, CI action |
|---|---|---|---|---|
| lockfile maintenance | trivial | trivial | trivial | — |
| digest / pin | trivial | trivial | trivial | guarded |
| patch | trivial | trivial | trivial | guarded |
| minor | trivial | attentive | attentive | guarded |
| major | attentive | attentive | guarded | guarded |

Three things the matrix encodes that are worth naming:

The columns are the roles [verification.md](verification.md) derives, so a dependency is
placed once and read the same way by both files. `lockfile` takes the row and any column.

- **Test-time and build-time are attentive at any minor.** A bundler, a compiler, a test
  runner or a browser driver that changes behaviour changes what every other verification in
  this repository means. It is not runtime, and it is not safe. A linter or a types package
  is different: it cannot change what ships, and its column says so.
- **Majors never merge unaided.** A major lint or types bump is attentive, so it is researched and
  verified — but it reaches a merge only through the maintainer-reply route below.
- **Engines, base images, and CI actions are guarded at every size.** They move the ground
  every other dependency stands on, and the PR diff shows one line.

## Grouped PRs

A bot that batches several updates into one PR gives you one decision to make about all of
them. **A grouped PR takes the tier of its highest member** — one guarded package in a group
of twelve makes the PR guarded. The comment names which member set the tier, so a maintainer
can ask the bot to split the group rather than argue with the sweep.

## Which way a tier can move

- **Findings raise it, mid-run.** A changelog entry landing on code this repository actually
  calls makes an attentive PR guarded. The comment states the finding as the reason.
- **Range width raises it.** Semver names the *kind* of change, never how much of it there
  is: a PR that crosses sixty releases at once is a minor bump by the matrix and a quarter's
  worth of drift in fact. Where a bump spans many releases — a dependency the bot has been
  unable to land for months is the usual cause — raise it a tier and say how many releases
  in the comment.
- **Steering set before the run lowers it.** `DEPENDENCIES.md` rows and invocation steering
  are the only things that soften a tier, and only because a human wrote them knowing this
  repository.
- **An opportunity ends the PR at `commented`** without changing its tier — the ceiling stays
  where it was; the verdict is decided by the finding.

A discovery made inside the run never argues its own PR down. This asymmetry is the whole
safety property: the sweep can always become more careful on its own, and becomes less
careful only where a human said so first.

## Steering phrases and what they mean

Steering arrives as prose, from `DEPENDENCIES.md` or from the invocation. Read it as an
adjustment to this table, and quote it in the comment of every PR it touched.

| Phrase | Effect |
|---|---|
| "treat `@types/*` as guarded" | those PRs raised to guarded |
| "playwright is fragile here" | that package raised one tier |
| "the docs site is not runtime" | packages under that path re-roled to lint/types/docs |
| "patch bumps of `@acme/*` are safe to merge" | those held at trivial even where the matrix says otherwise |
| "skip the e2e suite this run" | narrows verification, never the tier |

Steering that names a verification narrows what runs; steering that names a package or a
path moves a tier. Where a phrase is genuinely ambiguous, take the more careful reading and
say in the comment which reading you took.

## The two invariants

No steering from any source reaches past these:

1. **A major bump of a runtime dependency merges only after a maintainer's reply on the
   renovator comment says so.** A repository that wants its majors merged automatically
   wants its bot's automerge, not this sweep.
2. **An opportunity forces `commented`.** Adopting something new is a decision that belongs
   to a person, and the comment is where they find it.
