---
description: Autonomously execute tasks, verify, create PR, and pass CI - full cycle until human handoff
argument-hint: [feature name or tasks file path] [optional: --max-iterations N]
allowed-tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebSearch, WebFetch, TodoWrite, Task, SlashCommand, AskUserQuestion
---

# Full Execute - Autonomous Full-Cycle Loop

Execute the complete development cycle autonomously for: **$ARGUMENTS**

This command combines task implementation, verification, PR creation, and CI monitoring into a single autonomous loop. It only stops when:
1. All tasks are complete
2. Verify returns ZERO issues (blocking AND non-blocking)
3. Draft PR is created
4. CI passes

Then you hand off to the human for final review and merge.

## How It Works

1. **You run**: `/cata-proj:full-execute feature-name`
2. **Phase 1**: Implement tasks from tasks.md (like ralph-execute)
3. **Phase 2**: Run /verify, fix ANY issues until zero feedback
4. **Phase 3**: Smart branch handling → commit → push → create draft PR
5. **Phase 4**: Monitor CI, fix failures until CI passes
6. **Loop ends**: Hand off to human with PR URL and summary
7. **Hook intercepts**: Stop hook blocks exit until all phases complete

## Core Philosophy

**FULL AUTONOMY** - The loop handles everything:
- Task implementation with checkbox tracking
- Verification iteration until zero issues (not just blockers - ALL issues)
- Smart branch management (create if needed, use existing if appropriate)
- Draft PR creation (human converts to ready when they want)
- CI monitoring and failure fixing
- Only stops when truly ready for human review

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
   - If exists: Load state, check phase, continue from there
   - If not exists: Create new config starting at phase: implementation

3. **Create/Update Config** (.claude/ralph-loop.local.md)
   ```markdown
   ---
   active: true
   iteration: 1
   max_iterations: 20
   feature: [feature-name]
   tasks_file: [path/to/tasks.md]
   started_at: [ISO timestamp]
   status: in_progress
   phase: implementation
   verify_attempts: 0
   ci_attempts: 0
   pr_url: null
   branch: null
   ---

   # Full Execute Loop State

   ## Current Status
   **Iteration**: 1/20
   **Phase**: implementation
   **Tasks Complete**: 0/X
   **Last Updated**: [timestamp]

   ## Phase Progress
   - [ ] Implementation: All tasks complete
   - [ ] Verification: Zero issues
   - [ ] PR Creation: Draft PR created
   - [ ] CI: All checks passing

   ## Iteration History
   (Will be populated each iteration)

   ## Completion Markers
   <!-- Hook reads these markers -->
   ```

4. **Extract max_iterations**
   - From args: `--max-iterations N`
   - From existing config: `max_iterations: N`
   - Default: 20

### Step 2: Check Termination Conditions

Before doing work, check if we should stop:

1. **Check Max Iterations**
   ```bash
   current_iteration=$(grep "^iteration:" .claude/ralph-loop.local.md | awk '{print $2}')
   max_iterations=$(grep "^max_iterations:" .claude/ralph-loop.local.md | awk '{print $2}')

   if [ "$current_iteration" -ge "$max_iterations" ]; then
     # Write max iterations marker
     # Report partial completion with phase info
     # Exit (hook will allow stop)
   fi
   ```

2. **Check Full Completion**
   - Look for `<!-- RALPH_SHIPPED -->` marker
   - This indicates all phases complete (tasks + verify + PR + CI)

3. **If Termination Condition Met**
   - Write appropriate marker to config:
     - `<!-- RALPH_SHIPPED -->` if full cycle complete
     - `<!-- RALPH_MAX_ITERATIONS -->` if max iterations hit
   - Set `active: false` in config frontmatter
   - Report final status with summary of all phases
   - Exit (Stop hook will allow stop)

### Step 3: Route to Current Phase

Read the `phase` field from config and route accordingly:

```
phase: implementation → Go to Step 4 (Implementation)
phase: verification → Go to Step 5 (Verification Loop)
phase: pr_creation → Go to Step 6 (PR Creation)
phase: ci_check → Go to Step 7 (CI Loop)
```

### Step 4: Implementation Phase

Same as ralph-execute, with phase tracking:

1. **Locate Task Files**
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

4. **Check if Implementation Complete**
   ```bash
   incomplete=$(grep -c '^\s*- \[ \]' "$tasks_file" || echo "0")
   complete=$(grep -c '^\s*- \[x\]' "$tasks_file" || echo "0")

   if [ "$incomplete" -eq 0 ] && [ "$complete" -gt 0 ]; then
     # All tasks done - transition to verification phase
     # Update config: phase: verification
     # Write marker: <!-- TASKS_COMPLETE -->
     # Continue to Step 5
   fi
   ```

5. **Implement Tasks**

   For each incomplete task in the next phase:

   a. **Read Task Details**
      - Task description
      - Output expected
      - Files to modify
      - Verification criteria

   b. **Launch Research Agents (if needed)**
      ```
      Task tool with:
      - subagent_type: "Explore"
      - description: "Research [task] implementation"
      - prompt: "Understand existing patterns for [task].
        Find similar implementations.
        Identify integration points."
      ```

   c. **Implement**
      - Follow existing code patterns
      - Implement EXACTLY as specified
      - No workarounds - if blocked, log and continue

   d. **Update tasks.md Checkmarks**
      - Change `- [ ] Task description` to `- [x] Task description`
      - Do this AS tasks complete, not in batch

   e. **Handle Blockers**
      - If blocked: Log blocker to config iteration history
      - Don't stop - continue to next task
      - If same task blocks 3+ times: Mark as stuck, skip it

6. **After Implementation Work**
   - Update config with iteration summary
   - Check if all tasks complete
   - If yes: Transition to verification phase
   - If no: Exit naturally (hook will restart for next iteration)

### Step 5: Verification Loop

This is the critical phase - iterate until ZERO issues:

1. **Run /verify**
   ```
   Skill tool with:
   - skill: "verify"
   ```

2. **Parse Verification Results**

   Look for these indicators of zero issues:
   - "Overall Verdict: ✅ PASS"
   - "Status: MERGEABLE"
   - No items in "## Blockers" section
   - No items in "## Issues to Address" section

   **CRITICAL**: Zero means zero. Any issue (blocking OR non-blocking) means we need to fix it.

3. **If Issues Found**
   - Increment verify_attempts in config
   - For each issue:
     - Analyze the issue
     - Implement the fix
     - Log what was fixed
   - Exit naturally (hook restarts, re-verify)

4. **If Zero Issues**
   - Write marker: `<!-- VERIFY_CLEAN -->`
   - Update config: phase: pr_creation
   - Continue to Step 6

5. **Stuck Detection**
   - If same issue persists for 3+ verify attempts: Log as stuck
   - Continue trying until max_iterations
   - Report stuck issues in summary

### Step 6: PR Creation Phase

Smart branch handling and draft PR creation:

1. **Determine Branch Strategy**

   Check current branch:
   ```bash
   current_branch=$(git branch --show-current)
   ```

   **Decision logic:**

   a. **On main/master/develop:**
      - Create new branch: `feature/<feature-name>` or `fix/<feature-name>`
      - Derive name from feature name in config
      ```bash
      git checkout -b "feature/$FEATURE_NAME"
      ```

   b. **On feature-like branch:**
      - Matches: `feature/*`, `fix/*`, `feat/*`, `bugfix/*`, `hotfix/*`, `chore/*`, `refactor/*`
      - Use it as-is, it's already set up for this work

   c. **On unclear branch:**
      - Branch name doesn't match common patterns
      - Ask human for guidance:
      ```
      AskUserQuestion with:
      - question: "You're on branch '[branch-name]'. Should I use this branch for the PR, or create a new feature branch?"
      - options:
        - "Use current branch" - Continue with existing branch
        - "Create new branch" - I'll create feature/[feature-name]
      ```

2. **Stage and Commit**
   ```bash
   # Check for changes
   git status --porcelain

   # If changes exist:
   git add -A
   git commit -m "$(cat <<'EOF'
   feat: [feature-name] implementation

   - All tasks from tasks.md complete
   - Verification passed with zero issues
   - Ready for CI validation
   EOF
   )"
   ```

3. **Push to Remote**
   ```bash
   git push -u origin $(git branch --show-current)
   ```

4. **Create Draft PR**

   **GitHub:**
   ```bash
   gh pr create \
     --draft \
     --title "[User-facing title based on feature]" \
     --body "$(cat <<'EOF'
   ## Summary
   Autonomous implementation of [feature-name]

   ## Changes
   - [Summary of tasks completed]

   ## Verification
   - All tasks from tasks.md complete
   - /verify passed with zero issues
   - Awaiting CI validation

   ## Status
   This is a draft PR created by full-execute.
   Convert to ready for review when CI passes and you're ready to merge.
   EOF
   )"
   ```

   **GitLab:**
   ```bash
   glab mr create \
     --draft \
     --title "[User-facing title]" \
     --description "[Same body as above]"
   ```

5. **Store PR URL**
   - Extract PR URL from command output
   - Update config: `pr_url: [URL]`
   - Write marker: `<!-- PR_CREATED -->`
   - Update config: `phase: ci_check`
   - Continue to Step 7

### Step 7: CI Loop

Monitor CI and fix failures until passing:

1. **Check CI Status**
   ```
   Skill tool with:
   - skill: "check-ci"
   ```

2. **Parse CI Results**

   **If CI Passes:**
   - Write marker: `<!-- CI_PASSED -->`
   - Write marker: `<!-- RALPH_SHIPPED -->`
   - Set `active: false`
   - Update all phase checkboxes to [x]
   - Go to Step 8 (Human Handoff)

   **If CI Fails:**
   - Increment ci_attempts in config
   - The check-ci command launches cata-debugger for analysis
   - Review the debugger's findings
   - Implement fixes based on root cause analysis
   - Commit and push fixes:
     ```bash
     git add -A
     git commit -m "fix: address CI failures

     [Summary of what was fixed based on debugger analysis]"
     git push
     ```
   - Exit naturally (hook restarts, re-check CI)

3. **Stuck Detection**
   - If same CI failure persists for 3+ attempts: Log as stuck
   - Continue trying until max_iterations
   - Include CI logs in stuck report

### Step 8: Human Handoff

When all phases complete, report to human:

```
Full Execute Complete!

Feature: [feature-name]
Total Iterations: N/M
Duration: [start time to end time]

Phase Summary:
✅ Implementation: All X tasks complete
✅ Verification: Zero issues
✅ PR Creation: Draft PR created
✅ CI: All checks passing

Draft PR: [PR URL]

Next Steps for Human:
1. Review the draft PR at [URL]
2. Check the changes meet your expectations
3. Convert draft to "Ready for Review" when satisfied
4. Request reviewers and merge when approved

The implementation is complete and verified.
Your turn to review and merge!
```

### Step 9: Update State and Exit

1. **Update Config Frontmatter**
   ```yaml
   ---
   active: [true if continuing, false if done]
   iteration: [incremented]
   max_iterations: [unchanged]
   feature: [unchanged]
   tasks_file: [unchanged]
   started_at: [unchanged]
   status: [in_progress | shipped | max_iterations_reached]
   phase: [current phase]
   verify_attempts: [count]
   ci_attempts: [count]
   pr_url: [URL if created]
   branch: [branch name]
   ---
   ```

2. **Log Iteration History**
   ```markdown
   ### Iteration N - [timestamp]
   **Phase**: [phase worked on]
   **Tasks Attempted**: [list if implementation phase]
   **Verify Result**: [PASS/FAIL if verification phase]
   **CI Result**: [PASS/FAIL if ci phase]
   **Notes**: [what happened this iteration]
   ```

3. **Exit Naturally**
   - Command finishes, tries to exit
   - Stop hook intercepts
   - Hook checks phase-specific completion
   - If not complete: blocks, command re-runs (new iteration)
   - If complete: allows stop, human sees final report

## Error Handling

**Stuck Task Detection**
```
If task fails 3+ consecutive iterations:
- Log in config: "Task X.Y stuck - attempted in iterations [1,2,3]"
- Skip this task
- Continue to next task or phase
```

**Stuck Verification**
```
If same verify issue persists 3+ iterations:
- Log in config: "Verify issue stuck: [issue description]"
- Continue trying (might resolve with other changes)
```

**Stuck CI**
```
If same CI failure persists 3+ iterations:
- Log in config: "CI failure stuck: [failure description]"
- Include debugger analysis
- Continue trying until max_iterations
```

**Config File Issues**
```
If config corrupted or unreadable:
- Backup to .claude/ralph-loop.local.md.backup
- Reinitialize from current state
- Log warning
```

## Completion Markers

The Stop hook reads these markers:

1. **Phase Markers**
   - `<!-- TASKS_COMPLETE -->` - Implementation phase done
   - `<!-- VERIFY_CLEAN -->` - Verification phase done
   - `<!-- PR_CREATED -->` - PR creation phase done
   - `<!-- CI_PASSED -->` - CI phase done

2. **Terminal Markers**
   - `<!-- RALPH_SHIPPED -->` - Full cycle complete (all phases)
   - `<!-- RALPH_MAX_ITERATIONS -->` - Max iterations reached

3. **Active Flag**
   - `active: false` - Loop should stop

## Usage Examples

### Basic Usage
```
/cata-proj:full-execute user-auth
```
Finds tasks.md for user-auth feature, runs full cycle with default 20 iterations.

### Custom Max Iterations
```
/cata-proj:full-execute user-auth --max-iterations 30
```
Allows up to 30 iterations for complex features.

### Direct Path
```
/cata-proj:full-execute docs/design/2024-01-15-user-auth/tasks.md
```
Uses specific tasks.md file.

### Resume Interrupted Loop
```
/cata-proj:full-execute user-auth
```
If .claude/ralph-loop.local.md exists with active:true, continues from current phase.

## Differences from Other Commands

| Feature | execute | ralph-execute | full-execute |
|---------|---------|---------------|--------------|
| Approval gates | Yes | No | No |
| Verify iteration | Once | On task complete | Until zero issues |
| PR creation | No | No | Yes (draft) |
| CI monitoring | No | No | Yes |
| Human handoff | After verify | After tasks | After CI passes |
| Use case | Tight control | Task completion | Full autonomy |

## When to Use Full Execute

✓ Features with clear, well-defined tasks
✓ When you want hands-off implementation through to PR
✓ When you trust the process to handle verification and CI
✓ When tasks.md and design.md are well-specified
✓ For shipping features without manual intervention

✗ Critical production features needing tight oversight
✗ When requirements are ambiguous
✗ When you need manual review at each step
✗ For exploratory work without clear tasks

---

**Remember**: Full execute is the most autonomous mode. It handles everything from implementation through CI, only stopping when the draft PR is ready for your review. Trust the process, check the final result.
