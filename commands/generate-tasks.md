# Generate Task List from PRD

## Goal

To guide you in creating a detailed, step-by-step task list in Markdown format based on an existing Product Requirements Document (PRD). The task list should guide a developer through implementation with continuous testing and proper research documentation.

## Input

PRD file reference: $ARGUMENTS (e.g., `tasks/prd-user-profile-editing.md`)

## Process

1. **Receive PRD Reference:** The user provides the path to a specific PRD file
2. **Analyze PRD:** Read and analyze the functional requirements, user stories, and other sections of the specified PRD.
3. **Create Research Directory:** Create `tasks/research/[feature-name]/` directory for storing research findings.
4. **Phase 1: Generate Parent Tasks:** Based on the PRD analysis, create the file and generate the main, high-level tasks required to implement the feature. Use your judgement on how many high-level tasks to use. It's likely to be about 5. **ALWAYS include "Research and Documentation" as the first parent task.** Present these tasks to the user in the specified format (without sub-tasks yet). Inform the user: "I have generated the high-level tasks based on the PRD. Ready to generate the sub-tasks? Respond with 'Go' to proceed."
5. **Wait for Confirmation:** Pause and wait for the user to respond with "Go".
6. **Phase 2: Generate Sub-Tasks:** Once the user confirms, break down each parent task into smaller, actionable sub-tasks necessary to complete the parent task. Ensure:
   - Research sub-tasks come first for each major component
   - Every implementation sub-task is followed by a testing sub-task
   - Testing includes: build verification, unit tests, integration tests, and UI validation where applicable
   - Sub-tasks logically follow from the parent task and cover the implementation details implied by the PRD
   - Identify dependencies between tasks and use the `[depends on: X.Y]` notation
7. **Identify Relevant Files:** Based on the tasks and PRD, identify potential files that will need to be created or modified. List these under the `Relevant Files` section, including:
   - Implementation files
   - Test files for each implementation file
   - Research documentation files in `tasks/research/[feature]/`
8. **Generate Final Output:** Combine the parent tasks, sub-tasks, relevant files, and notes into the final Markdown structure.
9. **Save Task List:** Save the generated document in the `tasks/` directory with the filename `tasks-[prd-file-name].md`.

## Output Format

The generated task list _must_ follow this structure:

```markdown
## Relevant Files

### Research Documentation
- `tasks/research/[feature]/libraries.md` - Documentation of libraries, versions, and APIs to use
- `tasks/research/[feature]/patterns.md` - Code patterns and implementation examples
- `tasks/research/[feature]/dependencies.md` - Required packages and setup instructions
- `tasks/research/[feature]/testing-strategy.md` - Testing approach and commands

### Implementation Files
- `path/to/potential/file1.ts` - Brief description of why this file is relevant (e.g., Contains the main component for this feature).
- `path/to/file1.test.ts` - Unit tests for `file1.ts`.
- `path/to/another/file.tsx` - Brief description (e.g., API route handler for data submission).
- `path/to/another/file.test.tsx` - Unit tests for `another/file.tsx`.
- `lib/utils/helpers.ts` - Brief description (e.g., Utility functions needed for calculations).
- `lib/utils/helpers.test.ts` - Unit tests for `helpers.ts`.

### Notes

- Research findings MUST be saved to markdown files for future reference
- Unit tests should typically be placed alongside the code files they are testing
- Every implementation task MUST be followed by a testing task
- Testing commands vary by project type - document these in research phase

## Tasks

- [ ] 1.0 Research and Documentation
  - [ ] 1.1 Research latest best practices for [feature] using Context7, web search, and MCP resources
  - [ ] 1.2 Document library versions and APIs in `tasks/research/[feature]/libraries.md`
  - [ ] 1.3 Document code patterns in `tasks/research/[feature]/patterns.md`
  - [ ] 1.4 Identify and document testing strategy in `tasks/research/[feature]/testing-strategy.md`
  - [ ] 1.5 Update CLAUDE.md with project-specific test/build commands if needed
- [ ] 2.0 [First Implementation Task]
  - [ ] 2.1 [depends on: 1.0] Research specific implementation details for this component
  - [ ] 2.2 Implement [specific functionality]
  - [ ] 2.3 Test implementation (run build, tests, check logs)
  - [ ] 2.4 Fix any issues found in testing
- [ ] 3.0 [Next Implementation Task]
  - [ ] 3.1 [depends on: 2.0] Sub-task with research
  - [ ] 3.2 Implementation sub-task
  - [ ] 3.3 Test and verify sub-task
```

## Dependency Rules

- Use `[depends on: X.Y]` to indicate that a task depends on subtask X.Y
- Use `[depends on: X.0]` to indicate that a task depends on parent task X.0
- Multiple dependencies: `[depends on: 1.2, 3.4]`
- Dependencies must be declared immediately after the checkbox and before the task description
- A task cannot be started until all its dependencies are marked as complete `[x]`

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go") before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who will implement the feature.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `tasks/` directory in current project
- **Filename:** `tasks-[prd-file-name].md`

## Instructions

1. First, read the PRD file specified in $ARGUMENTS
2. Create the tasks directory and research subdirectory if they don't exist
3. Generate high-level parent tasks (ALWAYS include Research as first task) and wait for "Go" confirmation
4. Then generate detailed sub-tasks ensuring:
   - Research tasks come first
   - Every implementation has a corresponding test task
   - Research outputs are saved to markdown files
5. Save the complete task list in the proper location and format

## Testing Requirements

Ensure the task list includes testing after EVERY implementation:
- Build/compilation checks (`npm run build`, `cargo build`, etc.)
- Unit test execution (`npm test`, `pytest`, `cargo test`, etc.)
- Integration testing where applicable
- Docker health checks for containerized apps
- UI validation with Playwright for frontend changes
- API endpoint verification for backend changes

## Research Documentation Requirements

All research findings MUST be saved to persist across sessions:
- Library documentation and version requirements
- Code examples and patterns from official docs
- Best practices and common pitfalls
- Testing commands specific to the project
- Error solutions and troubleshooting steps