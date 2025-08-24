---
description: Execute tasks phase-by-phase with automatic verification
argument-hint: [feature name or tasks file path] [optional: phase number]
allowed-tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, LS, TodoWrite
---

# Execute Tasks by Phase

Execute implementation tasks for: **$ARGUMENTS**

## Process

### Step 1: Locate Task File

Find the tasks.md file:
- If given a path, use that directly
- If given a feature name, search `.design/*/tasks.md`
- Use the most recent task file for that feature

### Step 2: Identify Target Phase

Determine which phase to execute:
- If phase number provided, use that phase
- Otherwise, find the first phase with incomplete tasks
- Show phase goal and demo objective

### Step 3: Execute Phase Tasks

For each task in the phase:
1. Read task details (files, output, dependencies)
2. Implement the required changes
3. Handle any code removal specified
4. Verify task-level success
5. Report completion

### Step 4: Run Phase Checkpoint

After all phase tasks complete:
1. **Quality Checks**: Run each checkpoint command
   - Lint command (npm run lint, ruff, etc.)
   - Build command (npm run build, make, etc.)
   - Test command (npm test, pytest, etc.)
2. **Manual Verification**: Guide through any manual checks
3. **Demo Verification**: Confirm the demo works

### Step 5: Update Progress

If all verifications pass:
- Mark all phase tasks as complete: `- [x]`
- Mark checkpoint items as complete: `- [x]`
- Update the tasks.md file
- Report what can now be demonstrated

If verification fails:
- Report which check failed
- Show error details
- Suggest fixes
- DO NOT mark tasks as complete

## Execution Guidelines

### Task Implementation:
- Follow design document patterns
- Implement exactly what's specified
- Remove obsolete code as indicated
- Stay within task scope

### Quality Discovery:
1. Check package.json for scripts
2. Check Makefile for targets
3. Check for language-specific tools
4. Use project conventions

### Progress Tracking:
- Update tasks.md only after success
- Preserve all formatting
- Keep task descriptions intact
- Add completion timestamps if helpful

### Error Handling:
- Stop on first failure
- Provide clear error messages
- Suggest remediation steps
- Allow retry after fixes

## Example Flow

```
Input: "user-auth 1"

1. Found tasks at: .design/2024-01-15-user-auth/tasks.md
2. Executing Phase 1: "Minimal Skeleton"
   Goal: Create basic auth endpoint structure
   
3. Task 1.1: Create auth router... ✓
4. Task 1.2: Add middleware stub... ✓

5. Running Phase 1 Checkpoint:
   - Lint: ✓ Passed
   - Build: ✓ Compiled successfully  
   - Tests: ✓ 3 passing
   - Manual: Please verify /auth/login returns 200
   
6. Phase 1 Complete!
   Demo ready: "The auth endpoints exist and return mock responses"
   
7. Next: Run `/cata-proj/execute user-auth 2` for Phase 2
```

## Important Notes

- Always run ALL checkpoint commands
- Don't skip verification even if "it should work"
- Update task file immediately after success
- Provide clear demo confirmation
- Suggest the next phase command