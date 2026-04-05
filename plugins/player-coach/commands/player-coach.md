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

**The exerciser (cata-exerciser) must run every single turn.** The exerciser does a real E2E smoke test — it starts the application, uses the feature, and checks data flows. Tests passing is not sufficient; the feature must actually work end-to-end with real interactions. Do not rationalize skipping it ("the changes were small", "just a fix", "saving time") — the exerciser runs every turn because any code change can break E2E behavior in ways that unit tests miss. If the verification report comes back without a cata-exerciser row in the Agent Results Summary, treat verification as incomplete and re-invoke verify.

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

**EXERCISER GATE (check this before the APPROVED/FEEDBACK decision):**

Look at the verification report's Agent Results Summary table for the `cata-exerciser` row. This gate is mechanical — a table lookup with no room for judgment calls.

1. **cata-exerciser row is MISSING from the report:** The exerciser did not run. Output:
   ```markdown
   ## Turn N/M — EXERCISER MISSING
   The exerciser did not run this turn. Re-running verification.
   ```
   Re-invoke `/cata-helpers:verify --mode=report-only`. This does not increment the turn counter.

2. **cata-exerciser status is FAILED:** The feature does not work end-to-end. This blocks approval regardless of severity threshold — treat it as a severity 10 issue. Add the exerciser's failure description to feedback and continue to next turn.

3. **cata-exerciser status is BLOCKED:** The feature could not be verified. This blocks approval — treat as severity 9. The player must resolve the blocker (startup failure, missing credentials, unclear exercise strategy) so the exerciser can run. Add to feedback and continue to next turn.

4. **cata-exerciser status is PASSED:** Proceed to the CUSTOM GATES CHECK below.

A feature cannot be approved without a passing exerciser. The exerciser is what proves the feature actually works — not just that tests pass or code reviews look clean.

**CUSTOM GATES CHECK (after exerciser gate, before APPROVED/FEEDBACK):**

Look at the verification report for a "Custom Verification Gates" section. This gate is mechanical — same pattern as the exerciser gate.

1. **No "Custom Verification Gates" section in report:** No custom gates defined — proceed to the APPROVED/FEEDBACK decision below.

2. **Any custom gate has status FAIL:** This blocks approval regardless of severity threshold — treat each failed gate as a severity 10 issue. Add the failed gates with their evidence to feedback and continue to next turn.

3. **Any custom gate has status BLOCKED:** This blocks approval — treat as severity 9. The player must resolve whatever prevented the gate from being checked. Add to feedback and continue to next turn.

4. **All custom gates PASS:** Proceed to the APPROVED/FEEDBACK decision below.

Custom gates are repo-maintainer-defined invariants. A feature cannot be approved with failing custom gates.

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

{If any custom gates failed or blocked:}
**Failed Custom Gates:**
- Gate 1: "[rule text]" — FAILED: [evidence from report]
- Gate 3: "[rule text]" — BLOCKED: [reason from report]

[If below-threshold issues exist: "N additional issues below threshold (not blocking)."]
```

Set feedback = the issues list above, append to feedback_history (prefixed with "Turn N:"), and continue to next turn.

## Phase 1.5: PR Creation + CI Loop

This phase runs after verification passes (APPROVED) when `pr_enabled` is true (the default). Set `phase = "ci"`.

### Step 1: Write context file and create the PR

Before invoking the create-pr skill, write the accumulated loop state to a temp file so the skill can produce a rich, context-aware PR description with inline review comments. The human wasn't present during implementation — this is their primary way to understand what happened.

**Write the context file:**

```bash
cat > /tmp/pc-pr-context.md << 'CONTEXT'
## Plan Summary
{Synthesize the plan's goals in 2-4 sentences. Write for someone who was NOT
involved in planning. Include the problem being solved.}

## Implementation Journey

Completed in {N} turns (of {M} budget), severity threshold {S}.

| Turn | Phase | Summary | Outcome |
|------|-------|---------|---------|
{turn history table from feedback_history}

{If smooth: "Clean implementation — no sticky issues or repeated feedback."}
{If rough: brief narrative of what happened and why.}

## Friction Log
{From sticky_issues and player_concerns. Only include if friction occurred.
For each item, include the file/line reference so the skill can post inline comments.}

- **{area}** ({file}:{line}): {What was hard and why}. Turns {N, M}.

## Below-Threshold Issues
{From final verification report. Omit if none.}

- (sev {N}) [{agent}] VI-{X}: {description}

## CI Failures
{From ci_failures_log. Omit if none.}
CONTEXT
```

**Invoke the create-pr skill with the context:**

```
/cata-helpers:create-pr --context=/tmp/pc-pr-context.md
```

The skill creates the feature branch, commits, pushes, opens the PR with a rich description, and posts inline review comments on friction areas. Extract the PR URL from the output and store it as `pr_url`.

**If a PR already exists:** The skill detects this and updates the description instead.

**If create-pr fails** (no remote, auth error, branch conflict, etc.): Report the failure to the user and fall back to the `--no-pr` completion summary (Phase 2). Do not retry — the user needs to fix the underlying issue.

**Output to user:**
```markdown
## PR Created

PR: [pr_url]
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
