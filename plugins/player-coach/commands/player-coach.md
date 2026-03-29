---
description: Adversarial cooperation loop — player implements, /verify reviews, creates PR, passes CI
argument-hint: [--max-turns=N] [--severity=N] [--no-pr]
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, AskUserQuestion, Skill
---

# Player-Coach: Adversarial Cooperation Loop

You are the orchestrator of a player-coach loop. The player implements code, `/cata-helpers:verify --mode=report-only` runs the full verification pipeline, and then (by default) a PR is created and CI must pass. The loop ends when a PR exists with green CI — or when `--no-pr` is set, after verification is clean.

There is no separate coach agent. The verify command runs all verification agents and produces the report. You apply the severity threshold mechanically.

## Phase 0: Pre-Loop Setup

### 1. Check that a plan exists

The plan file is the requirements document for this loop. Without it, there's nothing to implement.

```bash
ls .claude/plans/*.md 2>/dev/null | head -5
```

If no plan exists, tell the user:
> "The player-coach loop needs a plan to work from. Create one first with `/plan` or enter plan mode. The plan should describe what you want implemented — requirements, constraints, tech stack, expected behavior."

Then STOP.

### 2. Read the plan

Read the plan file. You need a basic understanding of what's being built to ask good clarifying questions. Note the plan file path — you'll pass it to the player agent.

### 3. Parse arguments

Check `$ARGUMENTS` for:
- `--max-turns=N` — maximum iterations
- `--severity=N` — minimum severity threshold for issues that must be fixed
- `--no-pr` — skip PR creation and CI checking (just run the verify loop)

### 4. Clarify with the user

Use `AskUserQuestion` to fill in anything not specified. Only ask what's genuinely needed — don't ask for the sake of asking.

**Always ask (if not in arguments), using the EXACT format below:**

- **Max turns** — ask with these exact options:
  - `5` — quick (small fixes, focused tasks)
  - `10` — standard (typical features) **[default]**
  - `20` — thorough (large features, complex changes)

- **Severity threshold** — ask with these exact options:
  - `3` — strict (fix almost everything)
  - `5` — moderate (fix meaningful issues) **[default]**
  - `7` — lenient (only fix critical/high issues)

**Ask only if the plan is unclear about:**

- Scope or ambiguity in requirements
- Missing critical information the player will need
- Anything that would cause the player to get stuck

### 5. Confirm and start

Briefly summarize the configuration to the user:
> "Starting player-coach loop: [max_turns] turns, severity threshold [N], PR+CI [enabled/disabled]. Plan: [1-line plan summary]"

## Phase 1: The Loop

```
Initialize:
  turn = 0
  feedback = ""
  feedback_history = []
  sticky_issues = {}        # VI-IDs that reappear across turns → friction signals
  player_concerns = []      # non-"none" remaining concerns from player reports
  ci_failures_log = []      # CI failure details for journey narrative
  phase = "verify"          # "verify" or "ci"
  pr_url = ""
  pr_enabled = true         # false if --no-pr
```

For each turn (1 to max_turns):

### Step 1: Spawn the Player

Use the Agent tool to spawn a `pc-player` agent with a fresh context:

**Prompt template:**
```
You are the player agent on turn {turn} of {max_turns} in a player-coach loop.

Plan file: {plan_file_path}
Severity threshold: {severity}

{if turn == 1}
This is turn 1. There is no previous feedback. Implement the plan from scratch.
{else}
Verification feedback from turn {turn - 1} that you must address:

{feedback}
{endif}
```

Wait for the player to complete. Extract the PLAYER REPORT from the result.

**Output to the user immediately after the player completes:**
```markdown
## Turn N/M — Player Report

**Changes:**
- path/to/file.ts — what was changed
- path/to/other.ts — what was changed

**Build:** pass/fail
**Tests:** X passed, Y failed
**App starts:** yes/no/N/A
**Concerns:** [any remaining concerns from player report, or "none"]
```

### Step 2: Run Verification

Invoke the report-only verification pipeline via the Skill tool:

```
/cata-helpers:verify --mode=report-only
```

This runs ALL verification agents (tester, exerciser, reviewer, hardener, coherence, architect, security, qa, and any others in the verify pipeline), deduplicates findings, and produces a unified verification report with VI-{n} issue IDs and severity ratings. It does NOT fix anything — that's the player's job on the next turn.

The verify command handles agent spawning, parallelism, deduplication, and reporting. No need to manage agent lists here — if verify adds new agents in the future, they're automatically included.

Wait for verify to complete.

**Output to the user:**
```markdown
## Turn N/M — Verification Complete
```
The verify command already outputs its own detailed report (agent results table + deduplicated issues table), so just add the turn context header above it.

**CRITICAL: The verify skill will output its report and return. After it returns, YOU (the player-coach) MUST continue to Step 3 — apply the severity threshold and decide whether to loop. Do NOT stop here.**

### Step 3: Apply severity threshold and decide

This is mechanical — no judgment call needed.

**Extract the issues from the verification report. Count issues at or above the severity threshold.**

**Friction tracking (do this every turn, before the APPROVED/FEEDBACK decision):**

1. **Sticky issues**: Compare this turn's issues against the previous turn's feedback by title, location, and description — NOT by VI-ID (VI-IDs are sequential counters regenerated each run, so VI-1 in turn 1 and VI-1 in turn 2 are unrelated). If an issue from this turn matches a previous turn's issue by content (same file/location, same root cause), add it to `sticky_issues` with both turn numbers. These are issues the player failed to fix on the first attempt — a friction signal.
2. **Player concerns**: If the player report's "Remaining concerns" section lists any items (is not empty, "none", "N/A", or similar), append it to `player_concerns` with the turn number.

**If zero issues at/above threshold → APPROVED:**

Output to the user:
```markdown
## Turn N/M — APPROVED

No issues at or above severity threshold {severity}.
[If there are issues below threshold: "N issues below threshold noted but not blocking."]
```

If `pr_enabled` is true, proceed to Phase 1.5 (PR + CI). Otherwise, output the completion summary (Phase 2) and STOP.

**If any issues at/above threshold → FEEDBACK:**

Collect all issues at/above threshold. These become feedback for the next player turn.

Output to the user:
```markdown
## Turn N/M — FEEDBACK (N issues at/above severity {severity})

**Issues for next turn:**
1. VI-1 (sev 8) [tester, reviewer]: [title] — [description]
2. VI-3 (sev 5) [hardener]: [title] — [description]

[If below-threshold issues exist: "N additional issues below threshold (not blocking)."]
```

Set feedback = the issues list above, append to feedback_history (prefixed with "Turn N:"), and continue to next turn.

## Phase 1.5: PR Creation + CI Loop

This phase runs after verification passes (APPROVED) when `pr_enabled` is true (the default). Set `phase = "ci"`.

### Step 1: Create the PR

First, check if a PR already exists for the current branch:

```bash
gh pr view --json url 2>/dev/null
```

**If a PR already exists:** Extract the URL, store it as `pr_url`, and skip to Step 2.

**If no PR exists:** Invoke the create-pr skill:

```
/cata-helpers:create-pr
```

This creates a feature branch, commits changes, pushes, and opens a PR. Extract the PR URL from the output and store it as `pr_url`.

**If create-pr fails** (no remote, auth error, branch conflict, etc.): Report the failure to the user and fall back to the `--no-pr` completion summary (Phase 2). Do not retry — the user needs to fix the underlying issue.

### Step 1b: Update PR with rich description

After `pr_url` is obtained (whether from an existing PR or newly created), compose a comprehensive PR description and apply it. The human wasn't present during implementation — this description is their primary way to understand what happened.

**Compose the PR body using this template, then apply it with `gh pr edit`:**

```bash
gh pr edit {pr_url} --body "$(cat <<'PRBODY'
{composed body — see template below}
PRBODY
)"
```

If `gh pr edit` fails, warn the user but do not fail the loop — the generic description from create-pr is an acceptable fallback.

#### PR Description Template

Populate this from the accumulated loop state (plan, feedback_history, sticky_issues, player_concerns, ci_failures_log, and the final verification report):

```markdown
## Summary

{2-4 sentences explaining what was built and why, derived from the plan.
Write for someone who was NOT involved in planning or implementation.
Include the motivation/problem being solved, not just what files changed.}

## Architecture

{ASCII diagram showing the high-level structure of what was built or changed.
Show data flow, component relationships, request paths, module boundaries —
whatever helps the reader build a mental model quickly.

Skip this section for small or non-architectural changes (bug fixes, config tweaks).}

## What Changed

{Key changes grouped logically. Describe at component/feature level, not per-file.
Include what tests were added.}

- **Area/Component**: What was done and why
- **Another area**: What was done and why
- **Tests**: Summary of test coverage added

## Implementation Journey

Completed in {N} turns (of {M} budget), severity threshold {S}.

| Turn | Phase | Summary | Outcome |
|------|-------|---------|---------|
| 1 | Verify | {player summary} | {N issues → FEEDBACK} |
| 2 | Verify | {player summary} | {0 issues → APPROVED} |
| 3 | CI | PR created | {outcome} |
| ... | ... | ... | ... |

{If the run was smooth (≤3 turns, no sticky issues, no CI failures):
"Clean implementation — no sticky issues or repeated feedback."}

{If the run was rough (many turns, sticky issues, CI failures):
Write a brief narrative explaining what happened. Example:
"The auth middleware took 3 turns to stabilize. Turn 1's approach used
session storage but verification flagged JWT as the project convention.
After switching in turn 2, token refresh edge cases required turn 3."}

## Friction Log

{ONLY include this section if friction actually occurred. Omit entirely for clean runs.

Include items where:
- An issue persisted across 2+ turns (from sticky_issues) — the player couldn't fix it on the first try
- The player flagged unresolved concerns
- A workaround or hack was applied instead of a clean fix
- CI failures required non-trivial fixes

These are signals the human should look closely at the code in that area.

Format per item:}

- **{area/file}**: {What was hard and why}. Appeared in turns {N, M}.
  **Review**: {Specific thing the human should check — e.g., "the retry logic
  in auth.ts:45 is a workaround for a race condition, consider a proper fix"}

## Below-Threshold Issues

{Issues from the final verification that fell below the severity threshold.
These passed the bar but the human may want to address them later.
Omit this section if there are none.}

- (sev {N}) [{agent}] VI-{X}: {description}
```

#### Key guidance

- **Summary**: Synthesize the plan's goals in plain language — don't paste the plan verbatim.
- **Architecture**: Even a 3-line box-and-arrow diagram helps. Skip for trivial changes.
- **Friction Log**: This is the most important section. A clean run with no friction log signals "smooth, standard review." A friction log signals "pay attention here." Be honest about hacks and workarounds — the human would rather know now than discover issues in production.

**Output to user:**
```markdown
## PR Created

PR: [pr_url]
PR description updated with implementation context.
Checking CI status...
```

### Step 2: Check CI

Invoke the check-ci skill to monitor CI status:

```
/cata-helpers:check-ci
```

This handles platform detection, polling, and failure investigation.

Three possible outcomes:

**If all checks pass → proceed to Phase 2 (Completion) with PR info.**

**If any checks fail → continue to Step 3.**

**If no CI checks are configured** (empty checks output): Treat as passed and proceed to Phase 2 (Completion) with PR info.

### Step 3: CI Failure → Player Fix → Re-check

This sub-loop shares the turn budget with Phase 1. For each CI fix iteration:

```
Increment turn.
If turn > max_turns → go to Phase 2 ("turn limit during CI" variant). STOP the loop.
```

**3a. Format CI failures as feedback**

Extract the failure details from the check-ci output. Format as CI-N feedback items:

```markdown
## Turn N/M — CI FAILED

**CI failures for next turn:**
1. CI-1 (sev 10) [ci]: [check name] — [failure summary]
2. CI-2 (sev 10) [ci]: [check name] — [failure summary]

Spawning player to fix CI failures...
```

Keep the failure descriptions concise and actionable — extract the error message and relevant file/line, not full logs.

Also append the CI failure details to `ci_failures_log` for the PR description's friction log and journey narrative.

**3b. Spawn the player**

Same as Phase 1 Step 1, but with CI failure feedback:

```
You are the player agent on turn {turn} of {max_turns} in a player-coach loop.

Plan file: {plan_file_path}
Severity threshold: {severity}

CI failure feedback from the previous push:

{ci_feedback}
```

Wait for the player to complete. Output the player report.

**3c. Commit and push**

After the player fixes CI issues, stage only the files the player modified (from the player report), commit with a descriptive message based on what was fixed, and push:

```bash
git add <files from player report>
git commit -m "<descriptive message based on CI failures fixed>"
git push
```

If the commit fails (e.g., no changes were made — the player couldn't fix the issue), report this to the user and go to Phase 2 ("turn limit during CI" variant) with a note that the player was unable to fix the CI failure.

**3d. Re-check CI**

Go back to Step 2.

## Phase 2: Completion

### If approved (with PR+CI):

```markdown
# Player-Coach Complete

## Result: APPROVED + CI GREEN (Turn N of M)
## Severity threshold: {severity}
## PR: {pr_url}

## Turn History
| Turn | Phase  | Player Summary | Result |
|------|--------|---------------|--------|
| 1    | Verify | [summary]     | N issues → FEEDBACK |
| 2    | Verify | [summary]     | 0 issues → APPROVED |
| 3    | CI     | PR created    | 2 checks failed → FEEDBACK |
| 4    | CI     | [summary]     | All checks passed → DONE |

## Files Changed
[List from the final player report]

[If sticky_issues is non-empty OR player_concerns is non-empty OR ci_failures_log is non-empty:]
## Friction Summary
[Brief list: sticky issues, unresolved player concerns, CI failures that needed fixing.
Point the user to the PR description for full details.]
```

### If approved (without PR — `--no-pr` mode):

```markdown
# Player-Coach Complete

## Result: APPROVED (Turn N of M)
## Severity threshold: {severity}

## Turn History
| Turn | Player Summary | Issues at/above threshold |
|------|---------------|--------------------------|
| 1    | [summary]     | N issues → FEEDBACK |
| 2    | [summary]     | 0 issues → APPROVED |

## Files Changed
[List from the final player report]

[If sticky_issues is non-empty OR player_concerns is non-empty:]
## Friction Summary
[Brief list: sticky issues that took multiple turns, unresolved player concerns.]
```

### If turn limit reached (during verify phase):

```markdown
# Player-Coach: Turn Limit Reached

## Result: NOT APPROVED after M turns
## Severity threshold: {severity}

## Turn History
| Turn | Phase  | Player Summary | Result |
|------|--------|---------------|--------|
| 1    | Verify | [summary]     | N issues |
| ...  | ...    | ...           | ...    |
| M    | Verify | [summary]     | N issues |

## Remaining Issues
[Full issues list from the final verification report]

## Recommendation
The task may need manual intervention, plan refinement, or more turns.
You can re-run with `--max-turns=N` to continue iterating.
```

### If turn limit reached (during CI phase):

```markdown
# Player-Coach: Turn Limit Reached

## Result: VERIFIED but CI FAILING after M turns
## Severity threshold: {severity}
## PR: {pr_url} (CI not passing)

## Turn History
| Turn | Phase  | Player Summary | Result |
|------|--------|---------------|--------|
| 1    | Verify | [summary]     | N issues → FEEDBACK |
| 2    | Verify | [summary]     | 0 issues → APPROVED |
| 3    | CI     | PR created    | N checks failed → FEEDBACK |
| ...  | CI     | ...           | ... |
| M    | CI     | [summary]     | N checks still failing |

## Remaining CI Failures
[CI failure details from the last check]

## Recommendation
Verification passed but CI is still failing. Check the PR for details.
You can re-run with `--max-turns=N` to continue fixing CI.
```

## Important Notes

- **Don't write code.** The player does that.
- **Don't run verification yourself.** `/cata-helpers:verify --mode=report-only` does that.
- **Don't fix issues.** The player fixes them on the next turn.
- **Pass the plan file path, not the plan content.** The player reads the plan itself.
- **The decision is mechanical.** Issues at/above threshold = FEEDBACK. No issues at/above threshold = APPROVED. No subjective judgment.
