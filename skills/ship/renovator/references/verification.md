# Role and verification

A dependency's **role** — what it does for this repository — decides both its tier and what
would actually prove the bump safe. Derive it from the repository, not from the package's
reputation: the same library is a runtime dependency in one repository and a test fixture in
the next.

## Deriving the role

Work through these in order and take the first that fits. Where two fit, take the more
consequential one — a package used at build time *and* at runtime is runtime.

| Evidence | Role |
|---|---|
| A `FROM` line in a Dockerfile, or an `engines` / `.tool-versions` / `.nvmrc` constraint | engine or base image |
| A `uses:` in a CI workflow, or a pinned action digest | CI action |
| The runtime dependency section of the manifest (`dependencies`, `[project.dependencies]`, `require`, Maven `compile`/`runtime` scope, `Gemfile`) | runtime |
| A dependency the platform supplies at run time (Maven `provided`, a peer dependency, an unshaded jar) | runtime, and unverifiable here — say so |
| A bundler, compiler, transpiler, or codegen tool in the dev section | build-time |
| A test runner, assertion library, fixture, or browser driver | test-time |
| A linter, formatter, or type-only package | lint or types |
| Only a lockfile hash moved | lockfile |

**A monorepo has more than one manifest, and more than one ecosystem.** Derive the role
against the manifest the bumped package actually lives in — a `pom.xml` under `containers/`
and the root `package.json` answer to different rules — and name that manifest in the
comment, because "which one" is the first thing a maintainer checks.

**A PR can straddle roles.** One version constraint often lands in an `engines` field, a
Dockerfile `FROM`, and a workflow pin at once. Tier it by the most consequential role, and
**verify by all of them**: the tier is a single ceiling, but verification is a menu, and the
role you skip is the one that breaks.

Then confirm against usage, because manifest sections lie:

```bash
git grep -n "from ['\"]<package>" -- '*.ts' '*.js'    # adapt to the language
git grep -rn "<package>" -- Dockerfile '*.yml' justfile
```

The same grep answers a second question worth asking on every tool-constraint bump: **which
other places pin this version that the PR left alone.** A bot updates only what its managers
cover, so a version pinned in a workflow step, a Dockerfile line, or a shell script commonly
survives the bump and drifts silently — and it will drift again on every future bump until a
manager covers it. Name those sites in the comment; the fix is a line of bot config, and
nobody finds it without looking.

A package the runtime section declares but nothing imports is dead weight, not runtime — say
so in the comment. A repository that declares everything in one section has told you nothing,
and usage is then the only signal rather than the second opinion. A dev-section package imported by shipped code is runtime, and the tier
follows the usage.

## What proves each role

Pick from what this repository *has*. `just --list` is the source of truth for which
commands exist; `TESTING.md` says what each one means; `DEPENDENCIES.md` says which of them
this repository trusts for which role. Nothing here names a command — a command written down
in this file would be a command that goes stale in every repository at once.

| Role | What would prove the bump |
|---|---|
| lockfile | install from the lockfile cleanly, then the fast test verb |
| lint or types | the lint and typecheck verbs; a diff of what the new rules now flag |
| test-time | the affected suites, plus one deliberate failure to prove the runner still reports |
| build-time | a clean build from scratch, then the built artifact exercised — not just built |
| runtime | the unit and integration suites, then `exerciser` through the paths that import it |
| engine or base image | full environment up on the new engine, then the integration suite and one end-to-end path |
| CI action | the workflow itself on this PR — CI is both the subject and the proof |

**Build-time bumps hide behind a green build.** A bundler that emits subtly different output
compiles fine and breaks at runtime, so a build-time bump is proved by running what it
produced.

**A test-time bump makes every other verification suspect** while it is in flight. Where a
test runner or assertion library is what moved, the suite passing proves less than usual —
say in the comment that the suite ran under the new runner and what that does and does not
establish.

## Where verification runs

In a git worktree on a fresh branch off the PR head, so the sweep's other agents and the
repository's own working tree stay untouched:

```bash
git worktree add <path> -b renovator/pr-<n> <pr-head-sha>
```

An agent that starts the application needs its own `ENV_INDEX` under the engineer skill's
port contract. The worktree is removed in Phase 5 on every path, including failure.

## Gaps

Where the verification a tier needs has no command in this repository, that is the finding:
the PR ends `commented`, the comment names the gap in one line, and the run table proposes
the `DEPENDENCIES.md` row that would close it. A sweep that quietly skips a check it could
not run teaches nobody anything; a sweep that reports the missing check gets it built.
