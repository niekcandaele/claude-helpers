---
description: Autonomously execute tasks in a loop until completion or max iterations
argument-hint: [feature name or tasks file path] [optional: --max-iterations N]
allowed-tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebSearch, WebFetch, TodoWrite, Task, SlashCommand
---

# Ralph Execute - Autonomous Task Loop

Execute implementation tasks autonomously for: **$ARGUMENTS**

This command uses the Ralph Wiggum pattern: a Stop hook intercepts exit attempts and blocks the stop if work isn't complete, creating an autonomous feedback loop until all tasks are done or max iterations reached.

## How It Works

1. **You run**: `/cata-proj:ralph-execute feature-name`
2. **Command executes**: Works on tasks → runs /verify → tries to exit
3. **Hook intercepts**: Checks completion → blocks if not done
4. **Loop continues**: You see previous work → make progress → repeat
5. **Loop ends**: When all tasks complete or max iterations hit

## Core Philosophy

**AUTONOMOUS ITERATION** - The loop continues automatically:
- Failures are learning opportunities, not stop conditions
- Verify failures count against max iterations but don't stop the loop
- Tasks.md is the source of truth for completion status
- The Stop hook controls continuation, not the command

## Implementation

### Step 1: Initialize Loop State

On first run or continuation:

1. **Parse Arguments**
   ```
   $ARGUMENTS can be:
   - feature-name (finds docs/design/*/tasks.md)
   - path/to/tasks.md (direct path)
   - feature-name --max-iterations N (override default)
   ```

2. **Locate Configuration**
   - Check if `.claude/ralph-loop.local.md` exists
   - If exists: Load state, increment iteration
   - If not exists: Create new config

3. **Create/Update Config** (.claude/ralph-loop.local.md)
   ```markdown
   ---
   active: true
   iteration: 1
   max_iterations: 10
   feature: [feature-name]
   tasks_file: [path/to/tasks.md]
   started_at: [ISO timestamp]
   status: in_progress
   ---

   # Ralph Execute Loop State

   ## Current Status
   **Iteration**: 1/10
   **Tasks Complete**: 0/X
   **Last Updated**: [timestamp]
   **Status**: in_progress

   ## Iteration History
   (Will be populated each iteration)

   ## Completion Markers
   <!-- Hook reads these markers -->
   ```

4. **Extract max_iterations**
   - From args: `--max-iterations N`
   - From existing config: `max_iterations: N`
   - Default: 10

### Step 2: Check Termination Conditions

Before doing work, check if we should stop:

1. **Check Max Iterations**
   ```bash
   current_iteration=$(grep "^iteration:" .claude/ralph-loop.local.md | awk '{print $2}')
   max_iterations=$(grep "^max_iterations:" .claude/ralph-loop.local.md | awk '{print $2}')

   if [ "$current_iteration" -ge "$max_iterations" ]; then
     # Write max iterations marker
     # Report partial completion
     # Exit (hook will allow stop)
   fi
   ```

2. **Check Task Completion**
   ```bash
   tasks_file=$(grep "^tasks_file:" .claude/ralph-loop.local.md | cut -d' ' -f2-)
   incomplete=$(grep -c '^\s*- \[ \]' "$tasks_file" || echo "0")
   complete=$(grep -c '^\s*- \[x\]' "$tasks_file" || echo "0")

   if [ "$incomplete" -eq 0 ] && [ "$complete" -gt 0 ]; then
     # Write completion marker
     # Report success
     # Exit (hook will allow stop)
   fi
   ```

3. **If Termination Condition Met**
   - Write appropriate marker to config:
     - `<!-- RALPH_COMPLETE -->` if all tasks done
     - `<!-- RALPH_MAX_ITERATIONS -->` if max iterations hit
   - Set `active: false` in config frontmatter
   - Report final status
   - Exit (Stop hook will allow stop)

### Step 3: Locate Task Files

1. **Find tasks.md**
   - If $ARGUMENTS is a path ending in .md: use it
   - If feature name: search `docs/design/*/tasks.md` matching feature
   - If not found: error and exit

2. **Find design.md**
   - Look for design.md in same directory as tasks.md
   - If not found: log warning, continue without design context

3. **Validate tasks.md Format**
   - Check for checkbox format: `- [ ]` or `- [x]`
   - If no checkboxes found: error, suggest /cata-proj:tasks
   - Count total, complete, incomplete tasks

### Step 4: Track Iteration Progress

Use TodoWrite to show current iteration status:

```
TodoWrite with:
- Iteration N/M: [current iteration / max iterations]
- Tasks complete: X/Y
- Current phase: [phase name]
- Tasks in this iteration: [list of tasks attempting]
```

This gives visibility into what the loop is doing each iteration.

### Step 5: Execute Tasks

**NO PLANNING PHASE** - Ralph loops don't stop for approval, they iterate.

1. **Identify Next Incomplete Phase**
   ```
   - Read tasks.md
   - Find first phase with incomplete tasks (- [ ])
   - That's the target phase for this iteration
   ```

2. **Launch Research Agents (if needed)**

   For complex phases, launch research agents:

   a. **Explore Agent** - Understand codebase context
   ```
   Task tool with:
   - subagent_type: "Explore"
   - description: "Research [phase] implementation"
   - prompt: "Understand existing patterns for [phase].
     Find similar implementations.
     Identify integration points.
     Map files that need modification."
   ```

   b. **Researcher Agent** (if unfamiliar tech)
   ```
   Task tool with:
   - subagent_type: "cata-researcher"
   - description: "Research [technology]"
   - prompt: "Research [technology] best practices.
     Find current documentation (2026).
     Identify potential pitfalls."
   ```

3. **Implement Tasks**

   For each incomplete task in the phase:

   a. **Read Task Details**
      - Task description
      - Output expected
      - Files to modify
      - Verification criteria
      - Dependencies

   b. **Implement**
      - Follow existing code patterns (from research)
      - Implement EXACTLY as specified
      - No workarounds - if blocked, log to config and continue to verify
      - Update code, tests, docs as needed

   c. **Update tasks.md Checkmarks**
      ```
      - Change `- [ ] Task description` to `- [x] Task description`
      - Do this AS tasks complete, not in batch
      - tasks.md is source of truth for completion
      ```

   d. **Handle Blockers**
      - If blocked: Log blocker to config iteration history
      - Don't stop - continue to verify
      - Next iteration will see the blocker and try alternative approach
      - If same task blocks 3+ times: Skip it, mark as stuck in config

### Step 6: Run Verification

After implementing tasks, run verification:

1. **Invoke /verify**
   ```
   Skill tool with:
   - skill: "verify"
   - No arguments needed
   ```

2. **Capture Results**
   - Verification runs: cata-reviewer, cata-tester, cata-ux-reviewer, cata-coherence
   - May launch cata-debugger if failures detected
   - Results returned in verification report

3. **Log to Config**
   ```markdown
   ### Iteration N - [timestamp]
   **Tasks Attempted**: [list]
   **Verify Result**: PASS | FAIL
   **Tasks Completed**: X
   **Notes**: [what happened this iteration]
   **Failures**: [if verify failed, what failed]
   ```

4. **Handle Verify Failures**
   - If verify FAILS: Log failure, count against max iterations
   - DO NOT stop - Ralph philosophy is to keep trying
   - Next iteration will see the failures and fix them
   - If same failure 3+ iterations: Log as stuck scenario

### Step 7: Update State and Report

1. **Update Config Frontmatter**
   ```yaml
   ---
   active: true
   iteration: [incremented]
   max_iterations: [unchanged]
   feature: [unchanged]
   tasks_file: [unchanged]
   started_at: [unchanged]
   status: in_progress | complete | max_iterations_reached
   ---
   ```

2. **Sync Task Count**
   ```
   - Count tasks.md checkboxes again
   - Update "Tasks Complete: X/Y" in config
   - Track progress percentage
   ```

3. **Report Progress**
   ```
   Iteration N/M complete

   Progress:
   - Tasks complete: X/Y (P%)
   - Verify result: PASS | FAIL
   - Next iteration will: [continue | stop]

   [If failures: list failures]
   [If blockers: list blockers]
   ```

4. **Exit Naturally**
   - Command finishes, tries to exit
   - Stop hook intercepts
   - Hook checks completion, decides to continue or allow stop
   - If continuing: This entire command re-runs (new iteration)

### Step 8: Error Handling

**Stuck Task Detection**
```
If task fails 3+ consecutive iterations:
- Log in config: "Task X.Y stuck - attempted in iterations [1,2,3]"
- Skip this task
- Move to next incomplete task
- Report stuck task in iteration summary
```

**No Progress Detection**
```
If no tasks completed in last 3 iterations:
- Log warning in config
- Continue trying (don't give up)
- Report pattern to user in iteration summary
```

**Config File Issues**
```
If config corrupted or unreadable:
- Backup to .claude/ralph-loop.local.md.backup
- Reinitialize from tasks.md state
- Start fresh iteration count
- Log warning
```

**Missing Files**
```
If tasks.md not found: Error and exit
If design.md not found: Log warning, continue
If verify command fails: Log error, this is critical, continue but report
```

## Completion Markers

The Stop hook reads these markers to decide continuation:

1. **All Tasks Complete**
   ```markdown
   <!-- RALPH_COMPLETE -->
   ```
   Added when: `incomplete_count == 0 && complete_count > 0`

2. **Max Iterations Reached**
   ```markdown
   <!-- RALPH_MAX_ITERATIONS -->
   ```
   Added when: `current_iteration >= max_iterations`

3. **Active Flag**
   ```yaml
   active: false
   ```
   Set when loop should stop (completion or max iterations)

## Final Report

When loop ends (completion or max iterations), generate report:

```
Ralph Execute Complete

Feature: [feature-name]
Total Iterations: N/M
Duration: [start time to end time]

Final Status: [COMPLETE | PARTIAL | BLOCKED]

Tasks Summary:
- Total tasks: Y
- Completed: X
- Incomplete: Z
- Stuck: W

Iteration History:
[Summary of each iteration: what was attempted, results]

Recommendations:
[If incomplete: suggest increase --max-iterations or manual intervention]
[If stuck tasks: list them with details]
[If all complete: celebrate! 🎉]
```

## Usage Examples

### Basic Usage
```
/cata-proj:ralph-execute user-auth
```
Finds tasks.md for user-auth feature, runs with default 10 iterations.

### Custom Max Iterations
```
/cata-proj:ralph-execute user-auth --max-iterations 20
```
Allows up to 20 iterations before stopping.

### Direct Path
```
/cata-proj:ralph-execute docs/design/2024-01-15-user-auth/tasks.md
```
Uses specific tasks.md file.

### Resume Interrupted Loop
```
/cata-proj:ralph-execute user-auth
```
If .claude/ralph-loop.local.md exists with active:true, continues from where it left off.

## Important Notes

- **No human approval gates** - Loop runs autonomously
- **Stop hook controls continuation** - Not the command itself
- **tasks.md is source of truth** - Checkmarks determine completion
- **Verify failures don't stop loop** - They count against max iterations
- **Failures are learning opportunities** - Next iteration fixes them
- **Stuck detection prevents infinite loops** - Tasks that fail 3+ times are skipped
- **Config tracks everything** - Full audit trail of iterations

## Differences from /cata-proj:execute

| Feature | execute | ralph-execute |
|---------|---------|---------------|
| Approval gates | Yes (after planning, after verify) | No (autonomous) |
| Loop behavior | Single run | Multi-iteration loop |
| Verify failures | Stop for human review | Log and continue |
| Use case | Critical features, tight control | Routine features, autonomous iteration |
| Stop control | Human decides | Hook decides based on completion |

## When to Use Ralph Execute

✓ Routine features with clear requirements
✓ When you want autonomous iteration
✓ When you trust the process to converge
✓ When tasks.md is well-defined
✓ For exploratory implementation

✗ Critical production features
✗ When tight control needed
✗ When requirements are ambiguous
✗ When manual review is essential

---

**Remember**: The Ralph loop is powerful but autonomous. Trust the eventual consistency, let it iterate, and check the final results when it completes.
