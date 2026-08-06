---
name: setup-engineer
description: >-
  Reconcile this repository toward the opinionated "golden state" for agentic
  local development — a per-repo dev CLI, a thin justfile surface, a generated
  port-offset env contract, a four-file engineer skill, thin CI, and a doctor
  invariant-enforcer. Run /setup-engineer whenever you want to set up, audit, or
  repair a repo's local-dev tooling: a fresh repo with nothing, a half-built repo
  with organic scripts that needs consolidating, or a finished repo you just want
  to verify still conforms.
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
  - Task
metadata:
  group: design
---

# /setup-engineer — Golden-State Reconciler

This command does not "generate documentation." It **reconciles a repository toward a fixed,
opinionated golden state** for agentic local development, then hands ongoing enforcement to a
`doctor` command that lives in the repo. Think of it as `terraform apply` for a repo's dev
tooling: it reads the current world, diffs against the desired world, and closes the gap in
verified phases.

You are the **guardian** of this golden state. Every time it runs, the repo should end up the
same shape — predictable, parallel-instance-safe, self-healing.

## What "golden state" means

A repo is golden when all six of these are true. The full invariant checklist (the thing
`doctor` enforces) lives in [references/golden-state.md](references/golden-state.md) — read it
before you diff anything.

1. **A per-repo dev CLI** — a *deep module* in the repo's native language (JS repo → JS,
   Python repo → Python). Simple verb surface, all the messy orchestration hidden inside. It
   owns the entire local-dev lifecycle. Spec: [references/cli-and-just.md](references/cli-and-just.md).
2. **A thin `just` surface** — identical verbs across every repo and language, zero logic, each
   line shells into the CLI. This is what makes your muscle memory and the engineer skill
   portable. Template: [templates/justfile](templates/justfile).
3. **A generated env / port contract** — one `ENV_INDEX`, one `DEV_HOST`, a slot table as the
   single source of truth, `BASE + INDEX*100 + slot`, and the in-docker-DNS-vs-host-offset
   boundary law. Spec: [references/env-and-ports.md](references/env-and-ports.md).
4. **A four-file engineer skill** — `SKILL.md` / `ARCHITECTURE.md` / `TESTING.md` /
   `GOTCHAS.md`. Commands-out, why-in. Spec: [references/engineer-skill.md](references/engineer-skill.md).
5. **Thin CI** — workflows call the same `just`/CLI surface and hold ~zero logic. This is both
   reuse and resistance to CI-vendor lock-in.
6. **`doctor` is wired and green** — the in-repo invariant enforcer (a CLI verb) passes, and CI
   runs it.

`setup-engineer` reconciles the **existence and shape** of 1–6. `doctor` enforces the
**invariants** at runtime once the shape exists. Keep that split clear: setup-engineer is the
meta-reconciler that *creates and migrates*; doctor is the in-repo guard that *catches drift*.
setup-engineer runs `doctor` as its final gate.

## The reconciler loop

Run these steps in order. Do not skip the diff and do not big-bang an existing repo.

### 1. Detect

Inventory what exists. Don't assume — look.

```bash
# Identity
basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Stack / package manager
ls package.json pyproject.toml go.mod Cargo.toml 2>/dev/null
# Compose + existing env tooling
ls docker-compose*.yml compose*.yml .env .env.example 2>/dev/null
ls scripts/ 2>/dev/null
# Existing command surface
ls justfile Justfile Makefile 2>/dev/null
# Existing engineer skill — check wherever this repo keeps skills
ls -d .agents/skills/*-engineer/ .*/skills/*-engineer/ 2>/dev/null
# CI
ls .github/workflows/ .gitlab-ci.yml 2>/dev/null
```

Read whatever you find. Existing organic scripts (a `setup-env.mjs`, a `dev-data.mjs`, a
`reset-data.sh`) are not junk to delete — they are the **logic you will migrate into the CLI**.
Read them to learn the repo's real lifecycle before you propose anything.

### 2. Classify

Put the repo in exactly one bucket. This decides how aggressive you are.

- **Greenfield** — no CLI, no `just`, no env tooling, no engineer skill. → Scaffold the whole
  golden state from the per-language template. Low risk; little to break.
- **Partial** — has organic scripts and/or a monolith engineer skill (this is the akari/takaro
  case). → **Migrate**, phase by phase, verifying after each. Highest risk; never big-bang.
- **Golden** — already conforms. → Run `just doctor`, report green, stop. Don't churn a repo
  that's already correct.

### 3. Diff

Produce a concrete drift report against the golden-state checklist. For each of the six
elements, state: present / partial / missing, and the specific gap. Example:

```
CLI            partial   logic lives in 4 loose scripts/*.mjs, no single entrypoint, no `doctor`
just           missing   no justfile
env contract   partial   setup-env.mjs exists but 2 services hardcode host ports in compose
engineer skill partial   1 monolith SKILL.md (33KB) + 3 helper scripts inside the skill dir
CI             partial   workflow reimplements test orchestration inline instead of calling CLI
doctor         missing
```

### 4. Plan

Turn the diff into an **ordered, phased** remediation plan. For a Partial repo the order that
keeps the repo working at every step is:

1. **Scaffold the CLI skeleton** (verb surface + `doctor`, delegating to existing scripts at
   first) and the thin justfile over it.
2. **Migrate organic logic into the CLI** one concern at a time (env → lifecycle → data →
   tests), deleting each loose script only once its verb works.
3. **Bring the env/port contract to spec** (slot table as truth, kill hardcoded ports, derive
   boundary URLs) until `doctor` passes.
4. **Restructure the engineer skill** to the four-file floor; move commands out, move scripts
   into the CLI, keep only why/architecture/gotchas.
5. **Thin the CI** to call `just`/CLI.

Present the plan and get sign-off before applying. This matches the repo owner's standing rule:
multi-phase plans verify at the end of each phase.

### 5. Apply — phase-gated, never big-bang

After **each** phase:

```bash
just doctor      # invariants hold
just test        # nothing broke   (use the repo's real test verb if `just` isn't wired yet)
```

If a phase breaks something, stop and fix it before the next phase. Spawn verification
subagents with the Task tool for the heavier checks (run the full suite, exercise the app) so a
phase isn't declared done on a hunch. Do not delete an organic script until its replacement
verb is green.

### 6. Verify and report

End on a green `doctor` plus the report in [references/report-format.md](references/report-format.md):
what changed, what each phase verified, and any drift left for a follow-up.

## Two behavioral laws you must install

These go into the engineer skill's `SKILL.md` so **every** agent that later works in the repo
follows them ambiently — they are the heart of "guardian / continuous improvement." Full text
and rationale in [references/engineer-skill.md](references/engineer-skill.md).

- **Lifecycle hygiene** — *you brought the environment up, you tear it down when finished.*
  `just down` is the cheap reflex (keeps data, frees RAM so more instances run in parallel).
  This matters because the repo owner runs many headless instances at once; stale environments
  eating RAM is the failure mode.
- **Self-improvement (executable-encoding-first)** — when an agent fights through friction, the
  fix is routed to the most permanent layer that can hold it: a new `just`/CLI verb > a new
  `doctor` check > a `GOTCHAS.md` note. Prose is the fallback, not the default. This includes
  the **infra-change law**: adding or changing a service (datastore, queue, cache, IdP) means,
  in the same change, adding its port slot + healthcheck + `nuke` volume-coverage + regenerated
  `.env` — and `doctor` fails until all four are true.

## Reference map

| Read this | When |
|---|---|
| [references/golden-state.md](references/golden-state.md) | Before diffing — the full invariant checklist |
| [references/cli-and-just.md](references/cli-and-just.md) | Scaffolding/migrating the CLI + justfile + doctor |
| [references/env-and-ports.md](references/env-and-ports.md) | Working the env/port contract, devbox, HTTPS |
| [references/engineer-skill.md](references/engineer-skill.md) | Restructuring the engineer skill + the two laws |
| [templates/justfile](templates/justfile) | The canonical thin verb surface to drop in |
| [references/report-format.md](references/report-format.md) | The final golden-state report |
