# Golden-State Invariant Checklist

This is the canonical definition of "golden." Two consumers share it:

- **`setup-engineer`** diffs a repo against it (the existence/shape questions, §A–§F).
- **`doctor`** enforces the runtime invariants in it (the checkable rules, marked `[doctor]`).

When you add a new invariant during self-improvement, add it here **and** as a `doctor` check,
so the rule is both written down and mechanically enforced.

## A. Per-repo dev CLI

- [ ] A single CLI entrypoint exists in the repo's native language (e.g. `scripts/dev/` with a
      `devctl` bin, or `python -m devctl`). One front door, not a pile of loose scripts.
- [ ] It is a *deep module*: the verb surface is small and obvious; orchestration (ordering,
      health-waits, retries) is hidden inside.
- [ ] It implements the full canonical verb surface (see cli-and-just.md): `up down restart
      status logs shell db env doctor seed reset-data nuke rebuild test test-unit
      test-integration test-e2e test-file test-one`.
- [ ] `--help` lists every verb with a one-line description. The CLI's help is the source of
      truth for "what commands exist" — nothing duplicates it.

## B. Thin just surface

- [ ] A `justfile` exists at repo root.
- [ ] Every recipe is a thin shell into the CLI — no logic, no orchestration in the justfile.
- [ ] The recipe names match the canonical verbs exactly, so they are identical across repos.

## C. Generated env / port contract

- [ ] `[doctor]` Exactly one identity var, `<PROJECT>_ENV_INDEX` (default 0), drives the whole
      instance. `COMPOSE_PROJECT_NAME` derives from it.
- [ ] `[doctor]` Host ports follow `BASE + INDEX*100 + slot`, with a **slot table inside the
      CLI as the single source of truth**.
- [ ] `[doctor]` No service in any compose file hardcodes a host port that isn't drawn from the
      slot table.
- [ ] `[doctor]` No two slots collide, and every slot is `< 100` (stride ceiling).
- [ ] `[doctor]` `.env` is consistent with the current `ENV_INDEX` (regenerating it is a no-op).
- [ ] `[doctor]` The boundary law holds: nothing inside a container points at a host-offset
      port; only host-crossing URLs use `HOST:offset-port` (see env-and-ports.md).
- [ ] `[doctor]` Every host-crossing URL (auth issuer, redirect/post-logout URIs, CORS origins,
      frontend API URL, public base URL) is *derived* by the CLI from `HOST:port`, not
      hand-authored in committed config or realm JSON.
- [ ] `.env` is generated (managed keys rewritten, secrets + developer-owned values preserved),
      and regeneration auto-runs on `up`.

## D. Four-file engineer skill

- [ ] `.agents/skills/<repo>-engineer/` exists (or the repo's established skills
      directory) with the four-file floor: `SKILL.md`,
      `ARCHITECTURE.md`, `TESTING.md`, `GOTCHAS.md`.
- [ ] No command lists in the skill — it points at `just --list` / the CLI `--help`.
- [ ] No domain glossary in the skill — it links to `CONTEXT.md`.
- [ ] **Zero scripts** ship inside the skill dir; everything executable lives in the CLI.
- [ ] `SKILL.md` carries the two behavioral laws (lifecycle hygiene + self-improvement,
      including the infra-change law).

## E. Thin CI

- [ ] `[doctor]` CI workflows call `just`/the CLI for setup, test, and teardown rather than
      reimplementing orchestration inline.
- [ ] CI runs `just doctor` so invariant drift fails the build.

## F. Doctor wired and green

- [ ] `just doctor` exists and passes.
- [ ] `just doctor --fix` auto-repairs the cheap, safe subset (regenerate `.env`, re-derive
      boundary URLs) without a human round-trip.

## G. Tracker binding

Optional — a repo with no issue tracker worth binding is still golden. When one exists:

- [ ] `TRACKER.md` sits beside the engineer skill's `SKILL.md`.
- [ ] It names the tracker and gives `list` and `read` as runnable commands (the two required
      operations); write operations are recorded where they exist and their absence is stated
      where they don't.
- [ ] Every command in it has been run once and returned real data — a resolved-but-
      unauthenticated CLI is the failure mode this catches.
- [ ] Its label table maps *meanings* to this repo's actual label strings, with no invented
      labels for meanings the repo doesn't use.

## The infra-change law (why several invariants above exist together)

When a service is added or changed, four things must move together or the local environment
silently rots. `doctor` checks all four so the class of bug dies structurally:

1. **Port slot** — the service's host port comes from the slot table (invariant C).
2. **Healthcheck** — the service declares one, so `up` can wait on it.
3. **Nuke coverage** — `nuke` destroys the service's named volume; no orphan data survives a wipe.
4. **Regenerated `.env`** — any new host-crossing URL is derived, not hand-typed.

This is the generalization of the real failure that motivated the rewrite: a datastore was
added to compose without an offset port and without a clean-delete path, and nobody noticed
until it broke at runtime. Now it can't merge past `doctor`.
