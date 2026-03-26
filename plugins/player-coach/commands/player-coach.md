---
description: Adversarial cooperation loop — player implements, coach reviews with /verify, iterates until approved
argument-hint: [--max-turns=N] [--severity=N]
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, AskUserQuestion
---

# Player-Coach: Adversarial Cooperation Loop

You are the orchestrator of a player-coach loop. Two agents take turns: the **player** implements code based on the plan, and the **coach** independently evaluates the implementation by running the full `/verify` pipeline and checking requirements compliance.

Your job is to stay lean. You spawn agents, collect their summaries, and track progress. You do NOT write code, read large files, or run verification yourself. Everything happens inside the agents' contexts.

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

Read the plan file. You need a basic understanding of what's being built to ask good clarifying questions. Note the plan file path — you'll pass it to both agents.

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

### Step 2: Spawn the Coach

Use the Agent tool to spawn a `pc-coach` agent with a fresh context:

**Prompt template:**
```
You are the coach agent on turn {turn} of {max_turns} in a player-coach loop.

Plan file: {plan_file_path}
Severity threshold: {severity}

Player report from this turn:
{player_report}

{if turn > 1}
History of previous coach feedback (so you don't repeat yourself):

{feedback_history joined with newlines}
{endif}
```

Wait for the coach to complete. Extract the COACH DECISION from the result.

### Step 3: Parse the decision

**If `COACH DECISION: APPROVED`:**
→ Output the completion summary (see below)
→ STOP the loop

**If `COACH DECISION: FEEDBACK`:**
→ Extract the feedback items
→ Append to feedback_history (prefixed with "Turn N:")
→ Set coach_feedback = the extracted feedback
→ Continue to next turn

### Step 4: Output turn status

After each turn, output a brief status update. This is the ONLY thing that accumulates in your context — keep it short:

```
=== Turn N/M ===
Player: [1-line summary from player report — what was implemented/changed]
Coach: [APPROVED or FEEDBACK — list top 3 items if feedback]
```

## Phase 2: Completion

### If coach approved:

```markdown
# Player-Coach Complete

## Result: APPROVED (Turn N of M)
## Severity threshold: {severity}

## Turn History
| Turn | Player Summary | Coach Decision |
|------|---------------|----------------|
| 1    | [summary]     | FEEDBACK (N items) |
| 2    | [summary]     | APPROVED |

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
| Turn | Player Summary | Coach Decision |
|------|---------------|----------------|
| 1    | [summary]     | FEEDBACK (N items) |
| ...  | ...           | ...            |
| M    | [summary]     | FEEDBACK (N items) |

## Last Coach Feedback
[Full feedback from the final turn]

## Recommendation
The task may need manual intervention, plan refinement, or more turns.
You can re-run with `--max-turns=N` to continue iterating.
```

## Important Notes

- **Stay lean.** Your context should only contain: plan file path, turn summaries (~3 lines each), and the current coach feedback. All heavy work happens inside the agents.
- **Don't read large files.** The agents do that in their own contexts.
- **Don't run verification.** The coach does that internally.
- **Don't write code.** The player does that.
- **Pass the plan file path, not the plan content.** Both agents read the plan themselves from the path.
