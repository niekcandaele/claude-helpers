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
2. Implement the required changes EXACTLY as specified
3. Handle any code removal specified
4. Verify task-level success
5. Report completion

### Strict Implementation Rules

**ABSOLUTELY NO WORKAROUNDS** unless explicitly instructed by the human:

- **NO MOCKS**: Don't create mock implementations unless the task explicitly says "mock" or "stub"
- **NO QUICK-FIXES**: Don't implement temporary solutions hoping to fix them later
- **NO SUBSTITUTIONS**: If a dependency/service is missing, STOP and report - don't substitute
- **NO CREATIVE INTERPRETATION**: Implement exactly what's specified, not what you think might be better

**When You MUST Stop:**
1. Missing dependencies or packages that can't be installed
2. Required services not running (databases, APIs, etc.)
3. Configuration issues that would require guessing values
4. Permissions problems that block implementation
5. Specification ambiguities that need clarification

**Problem Analysis Protocol:**
When encountering a blocker:
1. STOP immediately - do not attempt workarounds
2. Analyze the root cause
3. Document what's missing or blocking
4. Report to human with clear explanation
5. Wait for human guidance before proceeding

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
- Follow design document patterns EXACTLY
- Implement only what's specified - no extras
- Remove obsolete code as indicated
- Stay strictly within task scope
- **NO MOCKS OR WORKAROUNDS** unless task explicitly requires them

**Unacceptable Practices:**
❌ Creating mock data when real integration is specified
❌ Hardcoding values that should come from config/environment
❌ Skipping error handling "for now"
❌ Using simplified implementations as placeholders
❌ Working around missing dependencies with alternatives
❌ Implementing "good enough" versions
❌ Adding TODO comments instead of proper implementation

**Acceptable Only When Specified:**
✓ Mocks/stubs when task explicitly says "mock" or "stub"
✓ Hardcoded values when task says "use hardcoded value X"
✓ Simplified versions when task says "basic" or "simple"
✓ Workarounds when human explicitly approves them

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
- Stop on first failure - NO WORKAROUNDS
- Provide detailed error analysis
- Document the exact blocker
- DO NOT attempt fixes without human approval
- Report what's needed to properly resolve

**Error Reporting Format:**
```
❌ Task Blocked: [Task name]

Blocker: [What's preventing proper implementation]
Root Cause: [Why this is happening]
Impact: [What can't be completed]

Required to Proceed:
- [Specific requirement 1]
- [Specific requirement 2]

Human Action Needed:
[Clear description of what the human needs to do]
```

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

- **ZERO TOLERANCE FOR WORKAROUNDS** - Stop and report blockers
- Always run ALL checkpoint commands
- Don't skip verification even if "it should work"
- Update task file immediately after success
- Provide clear demo confirmation
- Suggest the next phase command
- If blocked, provide detailed analysis for human review

## Examples of When to STOP

### Missing Service:
```
Task requires connecting to Redis, but Redis is not running.
❌ WRONG: Use in-memory cache as temporary solution
✓ RIGHT: Stop and report that Redis needs to be started
```

### Missing Package:
```
Task requires 'stripe' package but it's not installed.
❌ WRONG: Mock the Stripe API calls
✓ RIGHT: Stop and ask human to run 'npm install stripe'
```

### Ambiguous Specification:
```
Task says "add validation" without specifying rules.
❌ WRONG: Implement what seems reasonable
✓ RIGHT: Stop and ask for specific validation requirements
```

### Configuration Missing:
```
Task requires API keys that aren't in environment.
❌ WRONG: Use placeholder values
✓ RIGHT: Stop and ask for proper configuration
```