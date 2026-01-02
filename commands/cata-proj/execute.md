---
description: Plan, execute, and test tasks phase-by-phase with approval workflow
argument-hint: [feature name or tasks file path] [optional: phase number]
allowed-tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebSearch, WebFetch, TodoWrite, Task, ExitPlanMode, SlashCommand
---

# Execute Tasks by Phase

Execute implementation tasks for: **$ARGUMENTS**

This command orchestrates a complete development cycle: planning, execution, and testing. It ensures thoughtful implementation with automatic verification.

## Core Philosophy

**ABSOLUTELY NO WORKAROUNDS** - When you encounter blockers:
1. STOP immediately
2. Analyze the root cause thoroughly
3. Report the exact blocker with detailed analysis
4. Wait for human guidance

## Workflow Overview

1. **Planning Phase** (You handle this)
   - Research the phase requirements
   - Analyze current state
   - Create execution plan
   - Get user approval

2. **Execution Phase** (You handle this directly)
   - Implement according to approved plan
   - Follow strict no-workarounds protocol
   - Update task progress

3. **Verification & Testing Phase** (automatic via /verify)
   - Invoke /verify command for comprehensive multi-agent review
   - Present verification report to human

## Implementation

### Step 1: Planning Phase

First, research and understand what needs to be done:

1. **Locate project files**
   - Find and read the tasks.md file
   - Identify the target phase to execute
   - Read the design document for context

2. **Deep Codebase Research** - MANDATORY

   Launch research agents IN PARALLEL to understand implementation context:

   a. **Codebase Exploration** - Use Task tool with subagent_type: "Explore"
      - Understand existing patterns related to this phase
      - Find similar implementations to follow
      - Identify integration points and dependencies
      - Map the code areas that will be modified

   b. **Technical Research** (if phase involves unfamiliar tech) - Use Task tool with subagent_type: "cata-researcher"
      - Research unfamiliar technologies or patterns
      - Verify approach against current best practices
      - Find potential pitfalls or edge cases

   Wait for agent results before proceeding.

3. **Synthesize Research into Plan**
   - Combine agent findings with design requirements
   - Identify specific files to modify
   - Note patterns to follow from existing code
   - Flag any concerns or unknowns discovered

4. Present the plan using ExitPlanMode for approval.

### Step 2: Execution Phase

After plan approval, execute the implementation directly:

1. **Initial Setup**
   - Locate and read the design document (in `docs/design/*/design.md`)
   - Locate and read the tasks.md file
   - Check current git status to understand the codebase state
   - Use TodoWrite to track your progress through phases and tasks

2. **Phase Execution**
   For each phase:
   - Identify the target phase (from arguments or first incomplete phase)
   - Read the phase goal and demo objective
   - Execute each task in sequence:
     - Read task details carefully
     - Implement EXACTLY as specified
     - Handle any code removal requirements
     - Verify task completion
     - Update TodoWrite progress

3. **Debugging Approach**
   When encountering issues:
   - Use `docker compose logs` to check service logs
   - Add print/console.log statements for debugging
   - Execute code to see actual behavior
   - Search online for documentation and solutions
   - But NEVER implement workarounds

4. **Blocker Reporting**
   When blocked, provide:
   ```
   ❌ Task Blocked: [Task name]

   Blocker: [What's preventing implementation]
   Root Cause: [Why this is happening]
   Impact: [What can't be completed]

   Debugging Steps Taken:
   - [Step 1 and result]
   - [Step 2 and result]

   Required to Proceed:
   - [Specific requirement 1]
   - [Specific requirement 2]

   Human Action Needed:
   [Clear description of what needs to be done]
   ```

5. **Track Corrections** - MANDATORY

   During implementation, maintain a corrections log of any issues you encountered and fixed:

   - Unexpected errors that required debugging and fixes
   - Tests that failed and needed code changes
   - Type errors or lint issues discovered during implementation
   - Configuration issues that needed adjustment
   - Any deviation from the original plan

   For each correction, note:
   - What went wrong
   - How you fixed it
   - Whether this might indicate a design issue

   After /verify completes, share this corrections log with the human alongside the verification report. The human needs visibility into what you had to "fight through" during implementation.

### Step 3: Verification & Testing Phase

**MANDATORY**: After execution completes successfully, run comprehensive verification:

Use the Skill tool to invoke `/verify`

This runs comprehensive verification including:
- Code review (cata-reviewer)
- Test execution (cata-tester)
- UX review (cata-ux-reviewer)
- Coherence check (cata-coherence)
- Debug analysis if tests or UX review fail (cata-debugger)

**🛑 MANDATORY STOP**: After /verify completes and presents its report, wait for human input before proceeding. DO NOT act on any findings or make any fixes.

## Unacceptable Practices

❌ Creating mocks when real integration is specified
❌ Hardcoding values that should come from config
❌ Implementing "simpler" alternatives
❌ Using TODO comments instead of proper implementation
❌ Working around missing dependencies
❌ Skipping error handling
❌ Making assumptions about ambiguous requirements

## Required Practices

✓ Search online for up-to-date documentation
✓ Check docker logs for service issues
✓ Use print debugging to understand code flow
✓ Read existing code patterns before implementing
✓ Run ALL quality checks (lint, build, test)
✓ Update tasks.md only after verification passes
✓ Report blockers immediately with full analysis

## Online Research

Always search for:
- Latest library documentation
- Known issues and solutions
- Best practices for the technology
- Security considerations
- Performance implications

## Usage

```
/cata-proj/execute [feature-name]
/cata-proj/execute [feature-name] [phase-number]
/cata-proj/execute [path/to/tasks.md]
/cata-proj/execute [path/to/tasks.md] [phase-number]
```

## What You Will Do

1. Locate and read the design document and tasks.md file
2. Identify the target phase to execute
3. Execute each task exactly as specified
4. Run all quality checks and verifications
5. Update progress in the tasks.md file
6. Invoke /verify for comprehensive multi-agent verification
7. 🛑 STOP and present report to human - DO NOT act on findings
8. Wait for human to provide next instructions
9. Report any blockers with detailed analysis

## Implementation Philosophy

Follow a strict NO WORKAROUNDS policy:
- Implements exactly what's specified
- Stops and reports when blocked
- Provides detailed blocker analysis
- Never creates mocks unless explicitly required
- Never implements "simpler" alternatives

## Process

1. **Research and Plan**: Analyze requirements and create execution plan
2. **Get Approval**: Present plan and wait for user confirmation
3. **Execute Tasks**: Implement each task exactly as planned
4. **Handle Blockers**: Stop and report with detailed analysis when blocked
5. **Verification**: Invoke /verify for comprehensive multi-agent review
6. **🛑 STOP**: Present report and wait for human review - DO NOT act on findings

## Examples

### Execute next incomplete phase:
```
/cata-proj/execute user-auth
```

### Execute specific phase:
```
/cata-proj/execute user-auth 2
```

### Execute from specific task file:
```
/cata-proj/execute docs/design/2024-01-15-user-auth/tasks.md
```

## Important Notes

- **Planning is mandatory**: Always create and get approval before execution
- **No workarounds**: Implementation follows the plan exactly
- **Verification via /verify**: Comprehensive multi-agent verification runs automatically after execution
- **Quality gates**: Each phase must pass all verification before moving on
- **🛑 MANDATORY STOP after verification**: After /verify presents its report, you MUST STOP and wait for human input. DO NOT act on findings. DO NOT make any fixes or changes.

## Process Flow

```
1. Human runs: /cata-proj/execute feature-name
2. Planning phase begins:
   - Read tasks.md, design doc
   - Launch Explore/researcher agents to understand codebase context
   - Synthesize research into detailed plan
   - Exit plan mode for approval
3. Upon approval:
   - Execute the plan directly
   - Update tasks.md on success
4. Invoke /verify for comprehensive verification
5. 🛑 STOP - wait for human to review verification report
6. Human decides next steps
```

This ensures thoughtful, tested, and verified implementation at every phase.

Remember: The goal is correct implementation, not quick implementation. A blocked task with good analysis is better than a working workaround that will cause problems later.