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

3. **Testing Phase** (automatic via /cata-proj:demo)
   - Automatically invoke demo command
   - Demo runs via cata-tester agent
   - Verify functionality
   - Report results

## Implementation

### Step 1: Planning Phase

First, research and plan what needs to be done:

1. Locate and read the tasks.md file
2. Identify the target phase to execute
3. Read the design document for context
4. Analyze what each task requires
5. Check current state (git status, existing code)
6. Create a detailed execution plan

Then present the plan using ExitPlanMode for approval.

### Step 2: Execution Phase

After plan approval, execute the implementation directly:

1. **Initial Setup**
   - Locate and read the design document (in `.design/*/design.md`)
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

### Step 3: Testing Phase - AUTOMATIC DEMO EXECUTION

**MANDATORY**: After execution completes successfully, you MUST automatically run the demo:

1. **Extract the feature name** from $ARGUMENTS:
   - If $ARGUMENTS is a path like `.design/2024-01-15-user-auth/tasks.md`, extract `user-auth`
   - If $ARGUMENTS is already a feature name like `user-auth`, use it directly
   - If $ARGUMENTS includes a phase number (e.g., `user-auth 2`), use only the feature name

2. **Automatically invoke the demo command** using SlashCommand:
   ```
   Use the SlashCommand tool with:
   command: "/cata-proj:demo [feature-name]"
   ```

3. **Wait for demo results**:
   - If demo passes: Phase is complete and verified
   - If demo fails: Implementation has issues that must be fixed

**This is NOT optional** - every phase implementation must be automatically verified through the demo command. Do not ask the user to run the demo manually.

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
6. Automatically invoke /cata-proj:demo to verify the implementation
7. Report any blockers with detailed analysis

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
5. **Run Demo**: Automatically invoke /cata-proj:demo to verify implementation

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
/cata-proj/execute .design/2024-01-15-user-auth/tasks.md
```

## Important Notes

- **Planning is mandatory**: Always create and get approval before execution
- **No workarounds**: Implementation follows the plan exactly
- **Automatic testing**: Demo runs automatically after execution
- **Quality gates**: Each phase must pass demo before moving on
- **Clear reporting**: Blockers and failures are reported immediately

## Process Flow

```
1. Human runs: /cata-proj/execute feature-name
2. Planning phase begins:
   - Research requirements
   - Analyze current state
   - Create detailed plan
   - Exit plan mode for approval
3. Upon approval:
   - Execute the plan directly
   - Update tasks.md on success
4. Automatically invoke demo:
   - Use SlashCommand to run /cata-proj:demo feature-name
   - Demo command launches cata-tester agent
   - Demo executes and reports success or failure
5. Human decides next steps based on demo results
```

This ensures thoughtful, tested, and verified implementation at every phase.

Remember: The goal is correct implementation, not quick implementation. A blocked task with good analysis is better than a working workaround that will cause problems later.