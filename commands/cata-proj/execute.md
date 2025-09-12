---
description: Execute tasks phase-by-phase using the cata-coder agent
argument-hint: [feature name or tasks file path] [optional: phase number]
allowed-tools: Task
---

# Execute Tasks by Phase

Execute implementation tasks for: **$ARGUMENTS**

This command launches the specialized `cata-coder` agent to handle phase-by-phase task execution with strict adherence to specifications and zero tolerance for workarounds.

## Implementation

Launch the cata-coder agent with the Task tool:

```
Use the Task tool to launch the cata-coder agent with:
- subagent_type: "cata-coder"
- description: "Execute tasks phase-by-phase"
- prompt: "Execute the implementation tasks for: $ARGUMENTS

Follow your strict no-workarounds protocol. Read the design document and tasks.md file, then execute the appropriate phase. If a phase number is provided in the arguments, execute that specific phase. Otherwise, execute the first incomplete phase.

Report progress clearly and stop immediately if you encounter any blockers."
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

- The agent will NEVER implement workarounds
- All blockers are reported with root cause analysis
- Quality checks are mandatory (lint, build, test)
- Progress is tracked in the tasks.md file
- Each phase ends with a demonstrable outcome