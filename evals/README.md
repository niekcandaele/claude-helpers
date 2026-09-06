# Evaluating skills

`just validate` answers *does this skill install correctly*. This answers
*does it behave*: a realistic request, run through a real harness against a
built fixture, graded on facts you can check, with the evidence kept.

A **case** is a small YAML file that is, in substance, a Promptfoo test. The
glue in `scripts/evals/` does four narrow things: prepare an isolated workspace
and harness home, generate a Promptfoo config pointing at it, execute it
through the pinned Promptfoo CLI, and freeze the evidence outside the
repository. Assertions, the viewer and the HTML/JSON reports are Promptfoo's.

## Commands

```bash
npm ci                            # install the pinned tooling (Promptfoo + Codex SDK)
just eval-list                    # what can be measured
just eval-check                   # validate every case, no model calls
just eval-run catchup-branch-state  # evaluate one case on Codex
just eval-view                    # browse saved reports, no model calls
just eval-test                    # model-free checks for the tooling itself
just eval-probe                   # one cheap live call: what the harness actually sees
```

`just eval-run` prints the planned scope — case, model, arms, repetitions,
concurrency, judge passes, caching, timeout — and then proceeds. It does not
ask twice.

## Adding a case

Create `evals/cases/<id>/case.yaml`. `just eval-check` enforces this schema,
and `just validate` folds the same checks into the repository gate.

| Key | Rule |
| --- | --- |
| `id` | lowercase-kebab, equals the directory name, unique. Saved results are keyed on it, so never rename one |
| `skill` | must resolve to `skills/<group>/<skill>/SKILL.md` |
| `kind` | `behavior` |
| `harnesses` | non-empty list; `codex` today |
| `task` | the underlying request, with no mention of the skill |
| `invocation` | the sentence that names the skill; must not appear inside `task` |
| `expected_behavior` | prose describing what a good response reports |
| `fixture` | must resolve to `evals/fixtures/<fixture>/build.sh` |
| `assert` | Promptfoo assertions; at least one with a non-zero weight |

Unknown top-level keys are an error — a typo must not be silently ignored.

Beside the case, write `expectations/acceptable.md` and
`expectations/unacceptable.md`: a genuinely good answer, and a plausible but
wrong one with the confident tone intact. They are the grader's calibration —
`just eval-test` drives both through a provider double and requires the first
to pass every required assertion and the second to fail a named one. A grader
nobody has calibrated is a grader nobody should trust.

### Weight 0 means evidence, not criterion

Promptfoo documents Codex skill detection as heuristic, so the
`skill-used` assertion carries `weight: 0`: it is recorded and shown, and it
never decides a verdict.

## The fixture contract

`evals/fixtures/<name>/build.sh` takes a destination directory, builds the
whole world the harness will see, and prints the resulting Git `HEAD`. It must
be deterministic — pin every commit date, so two builds produce identical
hashes and the trial manifest can fingerprint the fixture.

`manifest.json` beside it declares both what to build and the facts a good
answer must report. One file, so the fixture and the grader cannot drift.

A fixture contains no `AGENTS.md`, `CLAUDE.md`, `.codex/` or `.claude/` —
nothing that would inject instructions the case never intended.

## Isolation

Every trial gets a fresh workspace under the state directory, and:

- `HOME` **and** `CODEX_HOME` are both overridden. Overriding `CODEX_HOME`
  alone still lets Codex discover skills installed under the real
  `~/.agents/skills`, which would put the maintainer's whole personal catalog
  in front of the harness.
- Only the case's target skill is staged, into `$CODEX_HOME/skills/<name>/`.
- The Codex config is generated fresh — never copied from the maintainer's
  `~/.codex/config.toml`, which carries a different model, reasoning effort and
  dozens of trusted-project entries.
- `auth.json` is symlinked, never copied. No credential material is ever
  written under the evaluation state directory.
- `sandbox_mode: read-only`, `approval_policy: never`,
  `network_access_enabled: false`.
- Grader answers — `expectations/*.md`, the fixture manifest, the case's
  `expected_behavior` — stay out of the workspace, and a leak check aborts the
  trial before any inference if one turns up there.

### Harness-provided context

Codex offers a fixed set of its own skills that no case stages and no override
removes. `just eval-probe` records what the harness actually had in front of
it into `harness-context.json`, and shouts if anything else appears. On the
pilot (Codex CLI 0.153.4, September 2026) the catalog was the staged skill plus:

```
imagegen, openai-docs, plugin-creator, skill-creator, skill-installer
```

Installed Codex plugins add namespaced entries of their own — the pilot machine
also has `deep-research-work:deep-research` and
`plugin-management:plugin-management` available in other contexts. Treat this
list as unavoidable context, not a defect. A **repository** skill other than
the staged one appearing there means isolation has regressed.

## Authentication

Execution runs on the local Codex ChatGPT subscription. Preflight refuses to
start when Codex is not logged in that way, and refuses just as hard when a
paid credential is configured — `OPENAI_API_KEY`, `CODEX_API_KEY`,
`OPENAI_BASE_URL`, or an `apiKey`/`base_url` in the provider config. The
refusal names the setting and never prints its value. Nothing here falls back
to billed inference, and CI holds no credentials at all: every routine check
runs against the provider doubles in `evals/providers/double.mjs`.

## Where results land

`${SKILL_EVAL_STATE_DIR:-${XDG_STATE_HOME:-~/.local/state}/skills-evals}`,
outside the worktree entirely:

```
work/<evaluation-id>/   ephemeral; rebuilt for every trial
promptfoo-home/         Promptfoo's results database, which `just eval-view` reads
runs/<evaluation-id>/   the frozen evidence
```

Each trial directory holds `manifest.json`, `outcome.json`, `assertions.json`,
the exact request and generated config under `request/`, the final response,
`results.json` and `results.html`, the Codex rollout transcript, and the
Promptfoo log. It is then made read-only: viewer ratings and comments live in
Promptfoo's database, and cannot rewrite what the trial actually did.

Each trial ends in exactly one status, and the failures are kept apart on
purpose:

| status | meaning |
| --- | --- |
| `passed` | every required assertion passed |
| `assertion-failed` | it ran, it was graded, a required assertion failed |
| `execution-error` | the harness errored or timed out; nothing was graded |
| `ungraded` | it ran but produced nothing to grade |

## Model choice

`SKILL_EVAL_CODEX_MODEL` sets the requested model; it defaults to
`gpt-6-astra`. Not every model is reachable on a ChatGPT subscription:
`gpt-5.1-codex-max` is rejected with HTTP 400, *"not supported when using Codex
with a ChatGPT account"*.

The **resolved** backend model is recorded as `null` with a reason. The Codex
SDK does not report it through Promptfoo, and inventing it would be worse than
admitting it.

`SKILL_EVAL_TIMEOUT_S` bounds a trial (default 900). The Promptfoo Codex
provider documents no timeout of its own, so the bound comes from the OS.

## Scope

One harness, one case at a time, one trial per invocation, the candidate arm
only. Claude Code, a repository overview, repetitions, selection scenarios,
dependency staging, artifact grading, baseline arms and export packages are all
later work — see `docs/specs/skill-evaluations.md`.
