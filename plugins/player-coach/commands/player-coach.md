---
description: Adversarial cooperation loop — player implements, /verify reviews, iterates until clean
argument-hint: [--max-turns=N] [--severity=N]
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, AskUserQuestion, Skill
---

# Player-Coach: Adversarial Cooperation Loop

You are the orchestrator of a player-coach loop. Two phases per turn: the **player** implements code, then `/cata-helpers:verify-report-only` runs the full verification pipeline. Issues at or above the severity threshold become feedback for the next player turn. The loop ends when verification is clean or the turn limit is reached.

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

### 4. Clarify with the user

Use `AskUserQuestion` to fill in anything not specified. Only ask what's genuinely needed — don't ask for the sake of asking.

**Always ask (if not in arguments):**

- **Severity threshold**: What's the minimum severity for issues that must be fixed?
  - 3 = strict (fix almost everything)
  - 5 = moderate (fix meaningful issues)
  - 7 = lenient (only fix critical/high issues)
  - Default: 5

- **Max turns**: How many iterations? (Default: 5)

**Ask only if the plan is unclear about:**

- Scope or ambiguity in requirements
- Missing critical information the player will need
- Anything that would cause the player to get stuck

### 5. Confirm and start

Briefly summarize the configuration to the user:
> "Starting player-coach loop: [max_turns] turns, severity threshold [N]. Plan: [1-line plan summary]"

## Phase 1: The Loop

```
Initialize:
  turn = 0
  feedback = ""
  feedback_history = []
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
/cata-helpers:verify-report-only
```

This runs ALL verification agents (tester, exerciser, reviewer, hardener, coherence, architect, security, qa, and any others in the verify pipeline), deduplicates findings, and produces a unified verification report with VI-{n} issue IDs and severity ratings. It does NOT fix anything — that's the player's job on the next turn.

The verify command handles agent spawning, parallelism, deduplication, and reporting. No need to manage agent lists here — if verify adds new agents in the future, they're automatically included.

Wait for verify to complete.

**Output to the user:**
```markdown
## Turn N/M — Verification Complete
```
The verify command already outputs its own detailed report (agent results table + deduplicated issues table), so just add the turn context header above it.

### Step 3: Apply severity threshold and decide

This is mechanical — no judgment call needed.

**Extract the issues from the verification report. Count issues at or above the severity threshold.**

**If zero issues at/above threshold → APPROVED:**

Output to the user:
```markdown
## Turn N/M — APPROVED

No issues at or above severity threshold {severity}.
[If there are issues below threshold: "N issues below threshold noted but not blocking."]
```
Then output the completion summary (Phase 2 below) and STOP the loop.

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

## Phase 2: Completion

### If approved:

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
```

### If turn limit reached:

```markdown
# Player-Coach: Turn Limit Reached

## Result: NOT APPROVED after M turns
## Severity threshold: {severity}

## Turn History
| Turn | Player Summary | Issues at/above threshold |
|------|---------------|--------------------------|
| 1    | [summary]     | N issues |
| ...  | ...           | ...      |
| M    | [summary]     | N issues |

## Remaining Issues
[Full issues list from the final verification report]

## Recommendation
The task may need manual intervention, plan refinement, or more turns.
You can re-run with `--max-turns=N` to continue iterating.
```

## Important Notes

- **Don't write code.** The player does that.
- **Don't run verification yourself.** `/cata-helpers:verify-report-only` does that.
- **Don't fix issues.** The player fixes them on the next turn.
- **Pass the plan file path, not the plan content.** The player reads the plan itself.
- **The decision is mechanical.** Issues at/above threshold = FEEDBACK. No issues at/above threshold = APPROVED. No subjective judgment.
