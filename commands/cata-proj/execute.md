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

3. **Verification & Testing Phase** (automatic multi-agent review)
   - Launch cata-reviewer agent for code review
   - Invoke /cata-proj:demo (runs cata-tester agent)
   - If demo fails: Launch cata-debugger for root cause analysis
   - Combine all outputs into unified report
   - Present comprehensive assessment to human

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

### Step 3: Verification & Testing Phase - AUTOMATIC MULTI-AGENT REVIEW

**MANDATORY**: After execution completes successfully, automatically run comprehensive verification:

1. **Extract the feature name** from $ARGUMENTS:
   - If $ARGUMENTS is a path like `.design/2024-01-15-user-auth/tasks.md`, extract `user-auth`
   - If $ARGUMENTS is already a feature name like `user-auth`, use it directly
   - If $ARGUMENTS includes a phase number (e.g., `user-auth 2`), use only the feature name

2. **Run Code Review and Functional Testing IN PARALLEL**:

   **IMPORTANT**: Launch both agents in parallel using a single message with multiple tool calls.

   a. **Code Review - Launch cata-reviewer agent**:
   ```
   Use the Task tool to launch the cata-reviewer agent with:
   - subagent_type: "cata-reviewer"
   - description: "Review phase implementation"
   - prompt: "Review the implementation for [feature-name].
     Find and read the design doc in .design/*/design.md.
     Use git diff to see changes made in this phase.
     Verify design adherence, check for over-engineering and AI slop.
     Provide detailed code review."
   ```

   b. **Functional Testing - Invoke demo command**:
   ```
   Use the SlashCommand tool with:
   command: "/cata-proj:demo [feature-name]"
   ```
   - Demo runs via cata-tester agent

   Capture both outputs for the final report

3. **Debug Analysis - If demo fails**:
   ```
   Use the Task tool to launch the cata-debugger agent with:
   - subagent_type: "cata-debugger"
   - description: "Analyze demo failures"
   - prompt: "The demo failed for [feature-name].
     Analyze the root cause of the test failures.
     Use git, logs, and available tools to investigate.
     Provide detailed diagnostic report without fixing anything."
   ```
   - Capture debugger's diagnostic report for the final report

4. **Generate Unified Report**:
   Combine all agent outputs into a comprehensive assessment:

   ```markdown
   # Phase Implementation Review: [Feature - Phase X]

   ## Code Review (cata-reviewer)
   [Insert reviewer agent output - design adherence, quality issues, AI slop]

   ## Functional Testing (cata-tester)
   [Insert demo test results - pass/fail, specific failures]

   ## Debug Analysis (cata-debugger)
   [Only if demo failed - insert root cause analysis]

   ## Overall Assessment
   **Status:** ✅ READY / ⚠️ ISSUES FOUND / ❌ FAILED

   **Critical Issues:** [Count from all agents]
   **Major Issues:** [Count from all agents]
   **Minor Issues:** [Count from all agents]

   **Recommendation:**
   - ✅ Phase complete and verified - proceed to next phase
   - ⚠️ Address issues found before proceeding
   - ❌ Must fix critical failures before phase is complete

   ## Next Steps for Human
   [Specific actions based on combined results]
   ```

5. **STOP HERE - MANDATORY PAUSE**:

   **🛑 CRITICAL: After presenting the unified report, you MUST STOP and wait for human input.**

   **DO NOT:**
   - ❌ Act on any recommendations from the agents
   - ❌ Make any fixes based on the reports
   - ❌ Implement any changes suggested by reviewers
   - ❌ Address any issues found by testers
   - ❌ Apply any debugger findings
   - ❌ Continue to the next phase
   - ❌ Make any code changes whatsoever

   **WHAT YOU SHOULD DO:**
   - ✅ Present the unified report clearly
   - ✅ Wait for the human to review the findings
   - ✅ Wait for explicit instructions from the human
   - ✅ Only proceed when the human tells you what to do next

   **The agent reports are FOR HUMAN REVIEW ONLY. Your job is to gather the information and present it, not to act on it.**

**This is NOT optional** - every phase gets full multi-agent verification and a unified assessment report, followed by a mandatory pause for human review.

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
6. Automatically launch cata-reviewer and /cata-proj:demo IN PARALLEL
7. If demo fails: Automatically launch cata-debugger for analysis
8. Generate unified report combining all agent outputs
9. 🛑 STOP and present report to human - DO NOT act on findings
10. Wait for human to provide next instructions
11. Report any blockers with detailed analysis

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
5. **Multi-Agent Verification**: Automatically run code review and functional testing in parallel, debugging if needed, then generate unified report
6. **🛑 STOP**: Present report and wait for human review - DO NOT act on agent findings

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
- **Multi-agent verification**: Code review, testing, and debugging run automatically after execution
- **Quality gates**: Each phase must pass all verification before moving on
- **Unified reporting**: Combined assessment from all agents with clear recommendations
- **🛑 MANDATORY STOP after reporting**: After presenting the unified agent report, you MUST STOP and wait for human input. DO NOT act on agent findings. DO NOT make any fixes or changes. The reports are for human review only.

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
4. Automatically run multi-agent verification (IN PARALLEL):
   - Launch cata-reviewer agent to verify design adherence and code quality
   - Use SlashCommand to run /cata-proj:demo feature-name (launches cata-tester agent)
   - If demo fails: Launch cata-debugger agent for root cause analysis
5. Combine all agent outputs into unified report
6. Present comprehensive assessment to human
7. 🛑 STOP - DO NOT act on agent findings
8. Wait for human to review and provide next instructions
9. Human decides next steps based on multi-agent report
```

This ensures thoughtful, tested, and verified implementation at every phase.

Remember: The goal is correct implementation, not quick implementation. A blocked task with good analysis is better than a working workaround that will cause problems later.