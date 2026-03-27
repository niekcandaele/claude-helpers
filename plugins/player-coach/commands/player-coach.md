---
description: Adversarial cooperation loop — player implements, coach reviews with verification agents, iterates until approved
argument-hint: [--max-turns=N] [--severity=N]
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, AskUserQuestion
---

# Player-Coach: Adversarial Cooperation Loop

You are the orchestrator of a player-coach loop. Three phases per turn: the **player** implements code, you spawn **all 8 verification agents** in parallel, then the **coach** evaluates the results and decides to approve or give feedback.

You must spawn the verification agents yourself because subagents cannot spawn further subagents — that's a platform limitation. The coach receives the verification results from you.

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

Read the plan file. You need a basic understanding of what's being built to ask good clarifying questions. Note the plan file path — you'll pass it to agents.

### 3. Parse arguments

Check `$ARGUMENTS` for:
- `--max-turns=N` — maximum player-coach iterations
- `--severity=N` — minimum severity threshold for issues that must be fixed

### 4. Clarify with the user

Use `AskUserQuestion` to fill in anything not specified. Only ask what's genuinely needed — don't ask for the sake of asking.

**Always ask (if not in arguments):**

- **Severity threshold**: What's the minimum severity for issues that must be fixed?
  - 3 = strict (fix almost everything)
  - 5 = moderate (fix meaningful issues)
  - 7 = lenient (only fix critical/high issues)
  - Default: 5

- **Max turns**: How many player-coach iterations? (Default: 5)

**Ask only if the plan is unclear about:**

- Scope or ambiguity in requirements
- Missing critical information the agents will need
- Anything that would cause the player to get stuck

### 5. Confirm and start

Briefly summarize the configuration to the user:
> "Starting player-coach loop: [max_turns] turns, severity threshold [N]. Plan: [1-line plan summary]"

## Phase 1: The Loop

```
Initialize:
  turn = 0
  coach_feedback = ""
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
This is turn 1. There is no previous coach feedback. Implement the plan from scratch.
{else}
Coach feedback from turn {turn - 1} that you must address:

{coach_feedback}
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

The user needs to see what the player did before verification starts. Don't skip this.

### Step 2: Spawn ALL 7 Verification Agents

After the player completes, spawn ALL of the following agents in parallel using the Agent tool. Use a single message with multiple Agent tool calls to maximize parallelism. Every agent must run — no exceptions, no skipping.

For each agent, include in the prompt:
- What files the player changed (from the PLAYER REPORT)
- The plan file path for context

**Agents to spawn (all 8, every turn):**

1. **cata-tester** — "Run the test suite for this project. Report all test failures with severity ratings. Files changed: {changed_files}"

2. **cata-exerciser** — "Start the application and exercise it end-to-end. Verify it actually works as a user would experience it. Files changed: {changed_files}"

3. **cata-reviewer** — "Review the code changes for design adherence, over-engineering, and AI slop. Files changed: {changed_files}"

4. **cata-hardener** — "Check for missing error paths, invalid input handling, edge cases, and unhandled state transitions. Files changed: {changed_files}"

5. **cata-coherence** — "Check for pattern violations, reinvented wheels, and convention drift against existing codebase. Files changed: {changed_files}"

6. **cata-architect** — "Check module boundaries, dependency direction, structural health, and abstraction gaps. Files changed: {changed_files}"

7. **cata-security** — "Check for injection flaws, auth issues, data exposure, and other security vulnerabilities. Files changed: {changed_files}"

Wait for ALL 7 agents to complete. Collect all their results.

**Output to the user immediately after verification completes.**

Use the same report format as the `/verify` command. Deduplicate findings across agents and present a unified report:

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

*Total: N issues from M agent findings (deduplicated)*
```

This gives the user the full picture before the coach makes its decision. Don't skip this.

### Step 3: Spawn the Coach

Use the Agent tool to spawn a `pc-coach` agent with a fresh context. Pass it EVERYTHING it needs to make a decision:

**Prompt template:**
```
You are the coach agent on turn {turn} of {max_turns} in a player-coach loop.

Plan file: {plan_file_path}
Severity threshold: {severity}

Player report from this turn:
{player_report}

Verification agent results:

=== cata-tester ===
{tester_results}

=== cata-exerciser ===
{exerciser_results}

=== cata-reviewer ===
{reviewer_results}

=== cata-hardener ===
{hardener_results}

=== cata-coherence ===
{coherence_results}

=== cata-architect ===
{architect_results}

=== cata-security ===
{security_results}

{if turn > 1}
History of previous coach feedback (so you don't repeat yourself):

{feedback_history joined with newlines}
{endif}
```

Wait for the coach to complete. Extract the COACH DECISION from the result.

### Step 4: Parse the decision and output to user

**Output to the user immediately after the coach completes:**

If APPROVED:
```markdown
## Turn N/M — Coach Decision: APPROVED

**Summary:** [coach's approval summary]
**Requirements met:** N/N
**Runtime verification:** build pass, tests X/Y, app starts yes/no
```
Then output the completion summary (Phase 2 below) and STOP the loop.

If FEEDBACK:
```markdown
## Turn N/M — Coach Decision: FEEDBACK

**Summary:** [coach's progress assessment]
**Requirements met:** N/M

**Feedback items for next turn:**
1. [BLOCKING] file.ts:45 — description
2. [IMPORTANT] test.ts — description
3. [MINOR] utils.ts — description

**Verification issues at/above threshold:**
- VI-1 (sev 8): description
```
Then extract the feedback items, append to feedback_history (prefixed with "Turn N:"), set coach_feedback = the extracted feedback, and continue to next turn.

## Phase 2: Completion

### If coach approved:

```markdown
# Player-Coach Complete

## Result: APPROVED (Turn N of M)
## Severity threshold: {severity}

## Turn History
| Turn | Player Summary | Verification | Coach Decision |
|------|---------------|--------------|----------------|
| 1    | [summary]     | [summary]    | FEEDBACK (N items) |
| 2    | [summary]     | [summary]    | APPROVED |

## Final Coach Assessment
[Copy the coach's approval summary]

## Files Changed
[List from the final player report]
```

### If turn limit reached:

```markdown
# Player-Coach: Turn Limit Reached

## Result: NOT APPROVED after M turns
## Severity threshold: {severity}

## Turn History
| Turn | Player Summary | Verification | Coach Decision |
|------|---------------|--------------|----------------|
| 1    | [summary]     | [summary]    | FEEDBACK (N items) |
| ...  | ...           | ...          | ...            |
| M    | [summary]     | [summary]    | FEEDBACK (N items) |

## Last Coach Feedback
[Full feedback from the final turn]

## Recommendation
The task may need manual intervention, plan refinement, or more turns.
You can re-run with `--max-turns=N` to continue iterating.
```

## Important Notes

- **Spawn ALL 7 verification agents every turn.** This is the whole point. No skipping, no "as warranted."
- **Spawn verification agents in parallel.** Use a single message with 7 Agent tool calls for maximum speed.
- **Don't write code.** The player does that.
- **Don't run verification yourself.** The agents do that.
- **Pass the plan file path, not the plan content.** Agents read the plan themselves.
- **The verification results WILL make your context grow.** That's the tradeoff for agents not being able to spawn sub-agents. Keep turn status summaries short to compensate.
