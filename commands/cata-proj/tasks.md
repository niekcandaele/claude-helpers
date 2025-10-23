---
description: Generate implementation tasks from a design document
argument-hint: [design doc path or feature name]
allowed-tools: Read, Write, Grep, Glob, LS, Bash
---

# Generate Task List

Create an actionable implementation task list based on the design document: **$ARGUMENTS**

## Process

### Step 1: Locate Design Document

First, find and read the design document:
- If given a full path, read that file directly
- If given a feature name, search in `docs/design/*/design.md` for matching documents
- Look for the most recent design doc with that feature name (by date prefix)
- Analyze requirements, architecture, and implementation details

### Step 2: Generate Task List

Create the task list in the same folder as the design document (`docs/design/YYYY-MM-DD-feature/tasks.md`) with incremental, testable tasks:

## Task Structure

```markdown
# Implementation Tasks: [Feature Name]

## Overview
[Brief summary of what we're building and the approach]
[Number of phases and why]

## Phase 1: [Descriptive Name - e.g., "Minimal Skeleton"]
**Goal**: [One clear objective for this phase]
**Demo**: "At standup, I can show: [specific demonstrable outcome]"

### Tasks
- [ ] Task 1.1: [Specific task]
  - **Output**: [What gets created/modified]
  - **Files**: [specific files]
  - **Verify**: [How to check it works]

- [ ] Task 1.2: [Another task]
  - **Depends on**: 1.1
  - **Output**: [Deliverable]
  - **Files**: [specific files]
  - **Remove**: [Any obsolete code to delete]

### Phase 1 Checkpoint
- [ ] Run lint: `npm run lint` (or appropriate command)
- [ ] Run build: `npm run build`
- [ ] Run tests: `npm test`
- [ ] Manual verification: [What to manually check]
- [ ] **Demo ready**: [Exactly what you'll show]

## Phase 2: [Descriptive Name - e.g., "Connect to Real Data"]
**Goal**: [Next logical increment]
**Demo**: "At standup, I can show: [what's new since Phase 1]"

### Tasks
- [ ] Task 2.1: [Task description]
  - **Output**: [What this adds]
  - **Files**: [specific files]
  - **Remove**: [Code that's now obsolete]

### Phase 2 Checkpoint
- [ ] Quality checks pass
- [ ] Previous functionality still works
- [ ] **Demo ready**: [What you can now demonstrate]

## Phase N: [Continue as needed...]
[Add more phases based on feature complexity]
[Simple feature = 1-2 phases, Complex = 6+ phases]

## Final Verification
- [ ] All requirements from design doc met
- [ ] All obsolete code removed
- [ ] Tests comprehensive
- [ ] Documentation updated
```

## Task Guidelines

### Phase Design Principles:
- **Start Small**: Phase 1 should be the absolute minimum that works
- **Iterate**: Each phase adds ONE logical increment
- **Demo-Driven**: Every phase ends with something you can show
- **Flexible Count**: 1 phase for trivial features, 10+ for complex ones
- **Continuous Cleanup**: Remove obsolete code as you go, not at the end

### Each Phase Should:
- Have a single, clear goal
- Take 0.5-2 days maximum
- End with a demonstrable outcome
- Include quality checkpoints
- Remove any code it makes obsolete

### Each Task Should:
- Take 15-60 minutes to complete
- Build directly on previous work
- Include specific file paths
- Note any code to remove
- Have clear verification steps

### Demo Examples:
- Phase 1: "The API endpoint returns hardcoded JSON"
- Phase 2: "Now it fetches real data from the database"
- Phase 3: "Search and filtering work"
- Phase 4: "Pagination and sorting added"
- Phase N: [Whatever makes sense next]

### Quality Checkpoints:
- Always include lint, build, test commands
- Specify exact commands for the project
- Include manual verification steps
- Confirm previous features still work

## Output

Save the task list in the same folder as the design document (`docs/design/YYYY-MM-DD-feature/tasks.md`) with:
- Clear, actionable tasks
- Specific file references
- Testable outcomes
- Logical progression
- References to code removal tasks from the design

The list should guide implementation from zero to complete feature, including cleanup of obsolete code.