---
description: Adversarial cooperation loop — player implements, verification agents review, iterates until clean
argument-hint: [--max-turns=N] [--severity=N]
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, AskUserQuestion
---

# Player-Coach: Adversarial Cooperation Loop

You are the orchestrator of a player-coach loop. Two phases per turn: the **player** implements code, then you spawn **all 7 verification agents** in parallel to review it. Issues at or above the severity threshold become feedback for the next player turn. The loop ends when verification is clean or the turn limit is reached.

There is no separate coach agent. The verification agents ARE the review, and you apply the severity threshold mechanically.

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

### Step 2: Spawn ALL 7 Verification Agents

After the player completes, spawn ALL of the following agents in parallel using the Agent tool. Use a single message with multiple Agent tool calls to maximize parallelism. Every agent must run — no exceptions, no skipping.

For each agent, include in the prompt:
- What files the player changed (from the PLAYER REPORT)
- The plan file path for context

**Agents to spawn (all 7, every turn):**

1. **cata-tester** — "Run the test suite for this project. Report all test failures with severity ratings. Files changed: {changed_files}"

2. **cata-exerciser** — "Start the application and exercise it end-to-end. Verify it actually works as a user would experience it. Files changed: {changed_files}"

3. **cata-reviewer** — "Review the code changes for design adherence, over-engineering, and AI slop. Files changed: {changed_files}"

4. **cata-hardener** — "Check for missing error paths, invalid input handling, edge cases, and unhandled state transitions. Files changed: {changed_files}"

5. **cata-coherence** — "Check for pattern violations, reinvented wheels, and convention drift against existing codebase. Files changed: {changed_files}"

6. **cata-architect** — "Check module boundaries, dependency direction, structural health, and abstraction gaps. Files changed: {changed_files}"

7. **cata-security** — "Check for injection flaws, auth issues, data exposure, and other security vulnerabilities. Files changed: {changed_files}"

Wait for ALL 7 agents to complete. Collect all their results.

### Step 3: Generate Verification Report and output to user

Deduplicate findings across agents and present a unified report using the same format as the `/verify` command:

```markdown
## Turn N/M — Verification Report

### Agent Results

| Agent | Status | Notes |
|-------|--------|-------|
| cata-tester | X passed, Y failed | [brief note] |
| cata-exerciser | PASSED / FAILED | [brief note] |
| cata-reviewer | Completed | Found N items |
| cata-hardener | Completed | Found N items |
| cata-coherence | Completed | Found N items |
| cata-architect | Completed | Found N items |
| cata-security | Completed | Found N items |

### Issues Found

[Deduplicate findings from all agents — same location, same root cause, or same symptom get merged into one entry. Use highest severity. List all source agents.]

| ID | Sev | Title | Sources | Description |
|----|-----|-------|---------|-------------|
| VI-1 | 8 | [title] | tester, reviewer | [merged description] |
| VI-2 | 5 | [title] | hardener | [description] |

*Severity: 9-10 Critical | 7-8 High | 5-6 Moderate | 3-4 Low | 1-2 Trivial*
*Total: N issues from M agent findings (deduplicated)*
```

### Step 4: Apply severity threshold and decide

This is mechanical — no judgment call needed:

**Count issues at or above the severity threshold.**

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

- **Spawn ALL 7 verification agents every turn.** No skipping, no "as warranted."
- **Spawn verification agents in parallel.** Use a single message with 7 Agent tool calls.
- **Don't write code.** The player does that.
- **Don't run verification yourself.** The agents do that.
- **Pass the plan file path, not the plan content.** The player reads the plan itself.
- **The decision is mechanical.** Issues at/above threshold = FEEDBACK. No issues at/above threshold = APPROVED. No subjective judgment.
