---
description: Plan, execute, and test tasks phase-by-phase with approval workflow
argument-hint: [feature name or tasks file path] [optional: phase number]
allowed-tools: Read, Grep, Glob, Task, ExitPlanMode
---

# Execute Tasks by Phase

Execute implementation tasks for: **$ARGUMENTS**

This command orchestrates a complete development cycle: planning, execution, and testing. It ensures thoughtful implementation with automatic verification.

## Workflow Overview

1. **Planning Phase** (You handle this)
   - Research the phase requirements
   - Analyze current state
   - Create execution plan
   - Get user approval

2. **Execution Phase** (cata-coder agent)
   - Implement according to approved plan
   - Follow strict no-workarounds protocol
   - Update task progress

3. **Testing Phase** (cata-tester agent)
   - Run demo for completed phase
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

After plan approval, launch the cata-coder agent:

```
Use the Task tool to launch the cata-coder agent with:
- subagent_type: "cata-coder"
- description: "Execute approved plan"
- prompt: "Execute the implementation tasks for: $ARGUMENTS

Here is the approved plan:
[Include the detailed plan that was approved]

Follow your strict no-workarounds protocol. Execute each task exactly as planned. Report progress clearly and stop immediately if you encounter any blockers."
```

### Step 3: Testing Phase

After cata-coder completes successfully, automatically launch the cata-tester:

```
Use the Task tool to launch the cata-tester agent with:
- subagent_type: "cata-tester"
- description: "Test completed phase"
- prompt: "Run the demo for: $ARGUMENTS

The phase was just completed. Execute the demo to verify everything works as expected. Report any failures without attempting fixes."
```

## Usage

```
/cata-proj/execute [feature-name]
/cata-proj/execute [feature-name] [phase-number]
/cata-proj/execute [path/to/tasks.md]
/cata-proj/execute [path/to/tasks.md] [phase-number]
```

## What the Agent Does

The cata-coder agent will:
1. Locate and read the design document and tasks.md file
2. Identify the target phase to execute
3. Execute each task exactly as specified
4. Run all quality checks and verifications
5. Update progress in the tasks.md file
6. Report any blockers with detailed analysis

## Agent Philosophy

The cata-coder agent follows a strict NO WORKAROUNDS policy:
- Implements exactly what's specified
- Stops and reports when blocked
- Provides detailed blocker analysis
- Never creates mocks unless explicitly required
- Never implements "simpler" alternatives

## Process

1. **Launch the Agent**: Use the Task tool to invoke the cata-coder agent with your arguments
2. **Monitor Progress**: The agent will report its progress through each phase
3. **Handle Blockers**: If blocked, the agent will stop and provide detailed analysis
4. **Review Results**: Agent will confirm what can be demonstrated after each phase

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
   - cata-coder executes the plan
   - Updates tasks.md on success
4. Automatically:
   - cata-tester runs the demo
   - Reports success or failure
5. Human decides next steps based on results
```

This ensures thoughtful, tested, and verified implementation at every phase.