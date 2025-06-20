# Process Task List

## Goal

To guide you through implementing a feature by working through ALL tasks systematically, with continuous testing and proper error handling, until completion or encountering unresolvable blockers.

## Input

Task list file reference: $ARGUMENTS (e.g., `tasks/tasks-prd-user-profile-editing.md`)

## Task Implementation Rules

- **Continuous execution:** Continue working through ALL tasks WITHOUT stopping for permission between tasks
- **Stop only when:**
  - All tasks are completed successfully
  - Encountering the same error 3+ times despite different approaches
  - A blocker prevents any forward progress
  - Explicit user intervention is needed (e.g., API keys, credentials)
- **Completion protocol:**  
  1. When you finish a **sub‑task**, immediately mark it as completed by changing `[ ]` to `[x]`.  
  2. If **all** subtasks underneath a parent task are now `[x]`, also mark the **parent task** as completed.
- **Testing requirement:** After EVERY sub-task, run appropriate tests/builds to verify the implementation works correctly

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## Execution Mode Selection

Before beginning task implementation, ask the user to choose their preferred execution mode:

**"Would you like to use parallel sub-agent execution for independent tasks? This can be faster but uses more tokens. (yes for parallel, no for sequential)"**

- **Parallel Mode (yes):** Launch multiple sub-agents to work on independent tasks simultaneously
  - Faster completion for tasks without dependencies
  - Higher token usage due to multiple concurrent agents
  - All dependency rules are strictly enforced
  - Only tasks with satisfied dependencies can run in parallel
  
- **Sequential Mode (no):** Process tasks one at a time in order
  - Lower token usage
  - Easier to follow progress
  - Traditional one-by-one execution

## Process

1. **Initial Setup:**
   - Read the task list file and any existing research documentation
   - Detect project type (Node.js, Python, Docker, etc.) from files
   - Check for existing CLAUDE.md for project-specific commands
   - Ask execution mode preference (parallel vs sequential)

2. **Research Phase (if not already done):**
   - Check `tasks/research/[feature]/` for existing documentation
   - If missing, perform thorough research using:
     - Context7 for library documentation
     - Web search for latest patterns and best practices
     - MCP resources for additional information
   - Save ALL findings to markdown files in research directory

3. **Continuous Task Execution:**
   - Identify next available task(s) with satisfied dependencies
   - For each task:
     a. Read relevant research documentation
     b. Implement the functionality
     c. Run immediate tests/verification
     d. If tests fail, debug and fix (up to 3 attempts)
     e. Update task list and relevant files
     f. Continue to next task WITHOUT asking permission

4. **Testing After Every Task:**
   - Run project-specific build command
   - Execute test suite
   - For Docker projects: check container health
   - For web apps: use Playwright to verify UI
   - For APIs: test endpoints
   - Document any new test commands in CLAUDE.md

5. **Error Handling:**
   - On test failure: Debug and retry (max 3 attempts)
   - Document errors in `tasks/errors-log.md`
   - If stuck after 3 attempts, move to next independent task
   - Return to blocked tasks after completing others

6. **Progress Reporting:**
   - Provide concise updates after each task completion
   - Show test results summary
   - Continue immediately without waiting for approval

## Important Guidelines

- **Research First:** Always check research docs before implementing
- **Test Continuously:** Run tests after EVERY sub-task, not just at the end
- **Don't Stop:** Keep working until all tasks are done or truly blocked
- **Document Everything:** Save research findings, test commands, and errors
- **Project Detection:** Identify and use project-specific commands:
  - Node.js: `npm test`, `npm run build`, `npm run lint`
  - Python: `pytest`, `python -m build`, `ruff`
  - Docker: `docker compose build`, `docker compose up`, check logs
  - Use Playwright for UI testing when applicable
- **Update CLAUDE.md:** Add discovered test/build commands for future sessions

## Dependency Checking

Before starting any task:
1. Parse the `[depends on: X.Y]` notation in the task description
2. For each dependency:
   - Locate the referenced task (X.Y or X.0)
   - Verify it is marked as complete `[x]`
3. If any dependencies are incomplete:
   - Skip this task
   - Show message: "Task X.Y is blocked by incomplete dependencies: [list]"
   - Find the next available task with satisfied dependencies
4. Handle multiple dependencies (e.g., `[depends on: 1.2, 3.4]`) by checking all listed tasks

## Task Completion Protocol

1. Complete the implementation for one sub-task
2. **Immediate Testing:**
   - Run build/compilation
   - Execute relevant tests
   - Verify functionality works as expected
3. Update the task list file:
   - Change `[ ]` to `[x]` for the completed sub-task
   - Update "Relevant Files" section if new files were created/modified
   - Mark parent task `[x]` if all its sub-tasks are now complete
4. Save the updated task list file
5. **Report progress briefly:** "✓ Task [X.Y] completed and tested. Moving to next task..."
6. **Continue immediately** to the next available task

## Error Handling

- If a sub-task cannot be completed due to blockers, keep it as `[ ]` and create a new sub-task describing what needs to be resolved
- Never mark a task as completed if:
  - Tests are failing
  - Implementation is partial
  - Unresolved errors occurred
  - Required files or dependencies are missing

## Instructions

1. Read the task list file specified in $ARGUMENTS
2. Check for existing research documentation in `tasks/research/[feature]/`
3. Ask user for execution mode preference (parallel/sequential)
4. Begin continuous execution:
   - Work through ALL tasks without stopping
   - Test after every implementation
   - Handle errors gracefully
   - Save important findings to documentation
5. Only stop when:
   - All tasks are complete
   - Encountering unresolvable blockers
   - User explicitly asks to stop

## Resilience Protocol

When encountering errors:
1. First attempt: Debug and fix the immediate issue
2. Second attempt: Try alternative approach
3. Third attempt: Research the error online and in documentation
4. If still failing:
   - Document the blocker in `tasks/errors-log.md`
   - Skip to next independent task
   - Return to blocked tasks after completing others

## Research Persistence

ALL research findings MUST be saved to files:
- `tasks/research/[feature]/libraries.md` - Library APIs and usage
- `tasks/research/[feature]/patterns.md` - Code examples and patterns
- `tasks/research/[feature]/dependencies.md` - Package versions and setup
- `tasks/research/[feature]/testing-strategy.md` - Test commands and approach
- `tasks/errors-log.md` - Errors encountered and solutions

This ensures knowledge persists across Claude sessions.
