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
npm ci                            # install the pinned tooling (Promptfoo + harness SDKs)
just eval-list                    # what can be measured
just eval-check                   # validate every case, no model calls
just eval-run catchup-branch-state              # evaluate it on Codex
just eval-run catchup-branch-state claude-code  # evaluate it on Claude Code
just eval-run catchup-branch-state both         # both, serially, two separate results
just eval-view                    # browse saved reports, no model calls
just eval-test                    # model-free checks for the tooling itself
just eval-probe                   # one cheap live call: what Codex actually sees
just eval-probe claude-code       # the same, for Claude Code
```

`HARNESS` defaults to `codex`, so an invocation written before Claude Code
existed costs exactly what it used to.

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
| `harnesses` | non-empty list of `codex` and/or `claude-code`, each named once |
| `task` | the underlying request, with no mention of the skill |
| `invocation` | the sentence that names the skill; must not appear inside `task` |
| `expected_behavior` | prose describing what a good response reports |
| `fixture` | must resolve to `evals/fixtures/<fixture>/build.sh` |
| `assert` | Promptfoo assertions; at least one with a non-zero weight |

Unknown top-level keys are an error — a typo must not be silently ignored.

`task`, `invocation` and `expected_behavior` must also name no harness. The
same text is sent to every selected harness, so "using Codex" or a path under
`.claude/` in a case would make the comparison unfair in a way nothing
downstream could detect. `just eval-check` refuses such a case.

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

## Harnesses

A case declares the harnesses it can be measured on, and each one gets its own
trial: its own workspace build, its own isolated harness home, its own
transcript, its own `results.json` and its own directory of frozen evidence.
Selecting `both` runs them serially and prints two verdicts. Nothing is
combined — no pass rate, no average, no "mostly passing" — because a result on
one harness is not evidence about the other.

Both harnesses receive the same task, the same fixture, the same assertions and
the same staged skill, byte for byte. Exactly two things are translated at the
provider boundary:

- **The invocation.** The case states it once, in neutral prose. Codex is sent
  that prose. Claude Code is sent `/<skill>`, because Claude Code honours a
  skill's own `disable-model-invocation: true` frontmatter and refuses to load
  such a skill on prose alone, while the slash form a person would type still
  loads it. Codex ignores that frontmatter entirely. The *task* that follows is
  identical on both.
- **The tool evidence.** The `skill-used` assertion reads the provider's
  reported skill calls. Codex reports them directly. On Claude Code a typed
  invocation is a command rather than a `Skill` tool call, so it reaches the
  provider empty and the saved transcript is read instead.
  `manifest.skill_evidence` records which source answered, and records the
  reason when neither could — an unavailable answer is never turned into a
  confident negative.

### Which integration Claude Code uses, and why

Promptfoo's native `anthropic:claude-agent-sdk` provider, not an adapter around
the CLI. Three questions decided it, each answered against the installed
provider source rather than the documentation:

| Question | Answer |
| --- | --- |
| Can it reach the subscription with no API key? | Yes. It refuses to start without `ANTHROPIC_API_KEY` *unless* `apiKeyRequired: false` is set; with that, the OAuth credential answers. The pilot's `modelUsage` came back `"provider": "firstParty"`. |
| Can it be isolated per trial? | Yes. The provider takes an `env` map and layers it over its own process environment, which is where `CLAUDE_CONFIG_DIR` and `HOME` are set. |
| Does it surface the evidence? | Yes — `metadata.skillCalls`, `metadata.modelUsage` keyed by resolved model id, `response.sessionId`, `cost` and normalised token usage. |

One piece of friction is worth knowing: the provider resolves the optional SDK
package from the directory holding the config, and the generated config lives
beside the trial, outside the repository. `work/<evaluation-id>/node_modules`
is a symlink back to the repository's install so both stay true.

`session_id` is generated fresh per trial. Reusing one is refused by the
harness with *"Session ID … is already in use"*, which is a useful guarantee:
a trial cannot silently continue an earlier conversation.

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

### Isolation on Claude Code

The same shape, with Claude Code's own levers:

- `CLAUDE_CONFIG_DIR` **and** `HOME` are both overridden. `CLAUDE_CONFIG_DIR`
  replaces `$HOME/.claude` wholesale, and on a maintainer's machine that
  directory is where the whole personal skill catalog lives.
- Only the case's target skill is staged, into
  `$CLAUDE_CONFIG_DIR/skills/<name>/`.
- `settings.json` is generated fresh, never copied, and sets
  `syncClaudeAiSkills: false`. A claude.ai-synced catalog is remote, personal
  and non-deterministic; it would put the maintainer's skills in front of the
  harness and nothing downstream could tell that it had.
- `.credentials.json` is symlinked, never copied — always as a symlink, even
  when the target is absent, so the shape of the trial does not depend on
  whether the machine happens to be logged in.
- `projects/` is created empty. It is where the harness writes its conversation
  transcript, so an empty one before the trial is the concrete evidence that the
  conversation was fresh, and exactly one file in it afterwards is the evidence
  that only this trial wrote there.
- `setting_sources: [user]` — the isolated config dir *is* the only "user"
  scope, so project and local settings, which a fixture could otherwise inject,
  never reach the trial. `strict_mcp_config: true` keeps MCP servers out too.
- The allowed tools are the read-only filesystem set plus `Bash`; `Write`,
  `Edit`, `NotebookEdit`, `WebFetch`, `WebSearch` and `Task` are denied.
- Before any inference, `claude auth status --json` is run against the trial's
  own directories and must report `loggedIn: true` with
  `authMethod: "claude.ai"`. That proves the isolation did not accidentally
  cost the subscription login, and it costs no inference.

A **repository** skill other than the staged one appearing in the probe means
isolation has regressed on either harness.

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
list as unavoidable context, not a defect.

Claude Code ships bundled skills of its own. On the pilot (Claude Code 2.1.263,
September 2026) the probe reported:

```
code-review
```

That is narrower than what the harness actually ships — asked to enumerate its
own catalog, Claude Code answers poorly, and it did not name the staged skill
either, although the graded trial then loaded and used it. So the recorded list
is an observation, not a promise, and — as on Codex — it varies by machine:
treat it as a **superset** and never assert equality. Bundled skills stay
enabled and are recorded as unavoidable context, symmetrically with Codex where
they cannot be disabled at all. `disableBundledSkills` (or
`CLAUDE_CODE_DISABLE_BUNDLED_SKILLS`) is the lever if the recorded catalog ever
proves to be a problem.

## Authentication

Execution runs on the local subscription of whichever harness is selected, and
every preflight failure names the harness it affects.

| harness | route | login check |
| --- | --- | --- |
| `codex` | `chatgpt-subscription` | `~/.codex/auth.json` has `auth_mode: "chatgpt"` |
| `claude-code` | `claude-subscription` | `claude auth status --json` reports `loggedIn: true`, `authMethod: "claude.ai"`, `apiProvider: "firstParty"`, and no `apiKeySource` |

`claude auth status --json` makes no model call, so the check is free. An
`apiKeySource` field in its answer is the conflict signal — the exact analogue
of Codex's `auth_mode != "chatgpt"`. The refusal names the setting only, never
its value, length or prefix.

Preflight refuses just as hard when a paid credential is configured anywhere,
whatever harness is selected and whether or not a provider double stands in:

| setting | affects |
| --- | --- |
| `OPENAI_API_KEY`, `CODEX_API_KEY`, `OPENAI_BASE_URL` | codex |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_CUSTOM_HEADERS`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX` | claude-code |

Provider-config keys are refused too: `apiKey` and `base_url` for Codex,
`apiKey`, `apiKeyHelper` and `forceLoginMethod` for Claude Code. Nothing here
falls back to billed inference. The acceptance pilot ran with no paid API
credential present in the environment and paid overage disabled on the account.

CI holds no credentials at all: every routine check runs against the provider
doubles in `evals/providers/double.mjs`, and preflight skips the per-harness
login checks when a double stands in.

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
`results.json` and `results.html`, the harness's own session transcript, and the
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
| `unsupported` | the case does not declare this harness; nothing was executed |

`unsupported` is a saved trial directory carrying a manifest and an
`outcome.json` but no results file. It exists so a harness the case never
claimed leaves visible evidence of the gap in a two-harness comparison instead
of quietly vanishing from it, and it never counts as a pass.

## Model choice

| harness | variable | default |
| --- | --- | --- |
| `codex` | `SKILL_EVAL_CODEX_MODEL` | `gpt-6-astra` |
| `claude-code` | `SKILL_EVAL_CLAUDE_MODEL` | `sonnet` |

Not every model is reachable on a ChatGPT subscription: `gpt-5.1-codex-max` is
rejected with HTTP 400, *"not supported when using Codex with a ChatGPT
account"*.

`sonnet` is a **mutable alias**: it names a tier, not a build, and an alias
alone does not establish that two harnesses were compared on equivalent models.
That is exactly why the manifest records `model.requested` verbatim *and*
`model.resolved`. On Claude Code the resolved identity comes from
`metadata.modelUsage`, which is keyed by resolved model id — the pilot's
`sonnet` resolved to `claude-sonnet-5`. Several keys are recorded as a list,
because several models really were used. On Codex it stays `null` with a
reason: the Codex SDK does not report it through Promptfoo, and inventing it
would be worse than admitting it. Pin a full model name in either variable when
reproducibility matters more than the tier.

`manifest.cost_estimate` carries an API-rate figure alongside a `basis` that
says plainly what it is not: not an invoice, and not remaining subscription
quota. It is never printed as a charge.

`SKILL_EVAL_TIMEOUT_S` bounds a trial (default 900). The Promptfoo Codex
provider documents no timeout of its own, so the bound comes from the OS.

## Scope

Two harnesses, one case at a time, one trial per harness per invocation, the
candidate arm only. A repository overview, repetitions, selection scenarios,
dependency staging, artifact grading, baseline arms and export packages are all
later work — see `docs/specs/skill-evaluations.md`.
