# The Dev CLI and the just Surface

The CLI is the **deep module** that holds all local-dev logic. The justfile is a **thin,
language-agnostic skin** over it. CI is a third thin client. The whole point: the *verbs* are
identical in every repo and every language, so the agent, the human, and CI all speak one
dialect — while the implementation underneath is free to be JS in a JS repo and Python in a
Python one.

## The canonical verb surface

Group by axis so names don't collide. These names are the contract — keep them exact.

```
LIFECYCLE
  up [index]        generate env → build if stale → start → wait until healthy
  down              stop & remove containers, keep data    ← the "I'm done" hygiene reflex
  restart
  status            this instance: are services healthy? which ports?
  logs [svc]
  shell [svc]       exec a shell into a container (default: the main app service)
  db                open a DB debug shell / run quick debug queries

ENVIRONMENT
  env [index]       (re)generate .env from the single INDEX var (usually auto on `up`)
  doctor [--fix]    validate golden-state invariants for THIS repo; --fix repairs the safe subset

DATA
  seed              create dev data, idempotent
  reset-data        wipe data + re-seed — fully autonomous, zero manual steps
  nuke              down + destroy all volumes for this instance (full data wipe)

BUILD
  rebuild           clean deps/artifacts → install → build images (the "clean build")

TESTS
  test              the whole suite — the correct default
  test-unit
  test-integration
  test-e2e
  test-file <path>
  test-one <pattern>
```

Scope boundary: this CLI owns **environment + data + tests** only. Pure code-quality
(lint/typecheck/format) stays with the existing `/verify` pipeline. `rebuild` includes a build
step, but the CLI is not where linting lives.

## What makes it a "deep module"

The takaro e2e harness is the model: a verb like `up` hides "generate env → start containers in
dependency order → poll each healthcheck → run migrations → return only when truly ready." The
caller says `just up` and waits. All the ordering, retries, and health logic is *inside*. A
shallow version that just runs `docker compose up -d` and returns is wrong — the value is in the
hidden orchestration.

Concretely, the CLI should be organized around these internal concerns (names illustrative):

- `ports` — the slot table + `BASE + INDEX*100 + slot` math (see env-and-ports.md). Single
  source of truth for every host port.
- `env` — render `.env`: rewrite managed keys, preserve secrets/developer values, derive all
  host-crossing URLs.
- `compose` — bring services up/down, wait on healthchecks, stream logs, exec shells.
- `data` — seed / reset-data / nuke, each idempotent and non-interactive.
- `tests` — dispatch the test verbs to the repo's real runners.
- `doctor` — the invariant checks from golden-state.md, runnable and `--fix`-able.

## doctor: the in-repo enforcer

`doctor` is a CLI verb, not a separate tool. It encodes the `[doctor]`-marked invariants from
[golden-state.md](golden-state.md). Each check is small, named, and prints a clear pass/fail
line. `--fix` applies only the safe, deterministic repairs (regenerate `.env`, re-derive
boundary URLs); anything risky is reported, not auto-applied.

This is the layer that makes the infra-change law real: parse the compose file(s), cross-check
every service against the slot table, healthchecks, and `nuke`'s volume list, and fail on the
first gap. CI runs `just doctor`, so drift can't merge.

## The justfile

Drop in [../templates/justfile](../templates/justfile) and adjust only the one line that names
the CLI invocation for this repo's language. Every recipe stays a one-liner. If you ever feel
the urge to put a loop or a conditional in the justfile, that logic belongs in the CLI instead.

## Scaffolding vs migrating

- **Greenfield:** generate the CLI skeleton with every verb stubbed, wire `doctor` first (so you
  have a target to verify against), then fill verbs in dependency order: `env` → `up`/`down` →
  `seed` → `test*`.
- **Partial (akari/takaro):** the loose scripts already contain the logic. Stand up the CLI
  skeleton so each verb initially *delegates to the existing script*, then pull the logic inside
  one verb at a time, deleting each script only once its verb is green under `just doctor` +
  `just test`. The repo keeps working the whole way.

Do not hand-author a full CLI in a language you can't run here without a target repo to verify
against — scaffold the structure and the verb contract, then implement and verify inside the
real repo.
