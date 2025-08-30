---
description: Execute demo of the most recently completed phase
argument-hint: [feature name or tasks file path]
allowed-tools: Read, Bash, Grep, Glob, LS
---

# Execute Phase Demo

Run the demonstration for the most recently completed phase of: **$ARGUMENTS**

## Process

### Step 1: Locate Task File

Find the tasks.md file:
- If given a path, use that directly
- If given a feature name, search `.design/*/tasks.md`
- Use the most recent task file for that feature

### Step 2: Identify Last Completed Phase

Analyze the tasks.md to find:
- The highest numbered phase with ALL tasks marked as `[x]`
- The phase checkpoint must also be fully marked as `[x]`
- Extract the **Demo** specification for that phase

If no phases are fully complete:
- Report that no phases are ready for demo
- Suggest running `/cata-proj/execute` first

### Step 3: Prepare Demo Environment

Before running the demo:
1. Verify prerequisites:
   - Confirm build is current (check timestamps if possible)
   - Ensure tests passed in the phase checkpoint
   - Check that required services are running

2. Display demo context:
   - Show phase name and goal
   - Display what should be demonstrable
   - List any manual setup required

### Step 4: Execute Demo

Run the demo exactly as specified:
1. **Follow Demo Steps**: Execute each step from the phase's demo description
2. **Capture Output**: Record all results and outputs
3. **No Modifications**: Do NOT make any changes to fix issues

### Step 5: Handle Demo Results

#### If Demo Succeeds:
- Report success with clear output
- Show what was demonstrated
- Confirm the phase goal was met
- Suggest next phase if available

#### If Demo Fails:
1. **STOP IMMEDIATELY** - Do not attempt fixes
2. **Analyze the Error**:
   - What specific step failed?
   - What was expected vs. what happened?
   - Is this a code issue or environment issue?
3. **Report Findings**:
   ```
   ❌ Demo Failed at: [Step that failed]
   
   Expected: [What should have happened]
   Actual: [What actually happened]
   
   Error Analysis:
   - Root Cause: [Likely reason for failure]
   - Impact: [What this means for the implementation]
   - Evidence: [Specific error messages or logs]
   
   Next Steps:
   - Fix the issue in the implementation
   - Re-run phase verification with `/cata-proj/execute`
   - Retry demo after fixes
   ```
4. **DO NOT**:
   - Attempt workarounds
   - Modify code to make it work
   - Skip to alternative demo approaches
   - Continue past the failure point

## Demo Execution Guidelines

### Demo Types by Phase:

**Early Phases (1-2)**: Usually programmatic
- API endpoint calls with curl
- Command-line execution
- Unit test demonstrations
- Log output verification

**Middle Phases (3-5)**: Mixed interaction
- Integration scenarios
- Multi-component workflows
- Data flow demonstrations
- Performance benchmarks

**Later Phases (6+)**: User-facing
- UI interactions
- End-to-end workflows
- Production-like scenarios
- Load testing results

### Common Demo Commands:

```bash
# API Testing
curl -X POST http://localhost:3000/api/endpoint
curl -H "Authorization: Bearer token" http://localhost:3000/api/resource

# Service Verification
npm run dev  # Then test specific features
docker compose ps  # Verify services running

# Database Checks
psql -c "SELECT * FROM table WHERE condition"
redis-cli GET key

# Log Analysis
tail -f logs/application.log
grep "SUCCESS" logs/latest.log

# Frontend Testing
npm run dev  # Open browser to localhost:3000
# Navigate through specific UI flows
```

### Error Analysis Patterns:

**Connection Errors**: Service not running or wrong port
**Authentication Errors**: Missing or invalid credentials
**Data Errors**: Missing test data or wrong format
**Build Errors**: Code not compiled or outdated build
**Configuration Errors**: Wrong environment variables
**Dependency Errors**: Missing packages or services

## Example Flows

### Successful Demo:
```
Input: "user-auth"

1. Found tasks at: .design/2024-01-15-user-auth/tasks.md
2. Last completed phase: Phase 2 - "Connect to Real Data"
   Demo: "User can register and receive JWT token"

3. Executing demo...
   ✓ Started auth service on port 3000
   ✓ POST /auth/register with test data
   ✓ Received JWT token in response
   ✓ Token validates correctly

4. Demo Successful!
   Phase 2 goal achieved: Real database integration working
   Next: Run `/cata-proj/execute user-auth 3` to continue
```

### Failed Demo:
```
Input: "payment-integration"

1. Found tasks at: .design/2024-01-16-payment-integration/tasks.md
2. Last completed phase: Phase 3 - "Process Transactions"
   Demo: "Complete payment flow with Stripe"

3. Executing demo...
   ✓ Payment service running
   ✓ Created payment intent
   ❌ Payment confirmation failed

4. Demo Failed at: Payment confirmation
   
   Expected: Payment status 'succeeded'
   Actual: Payment status 'requires_action'
   
   Error Analysis:
   - Root Cause: Missing 3D Secure handling
   - Impact: European cards will fail
   - Evidence: Stripe API error: "authentication_required"
   
   Next Steps:
   - Add 3DS handling to payment flow
   - Re-run `/cata-proj/execute payment-integration 3`
   - Retry demo after implementation fix
```

## Important Notes

- **Never fix during demo**: The demo command only demonstrates, never modifies
- **Honest reporting**: Report exactly what happens, good or bad
- **Clear analysis**: When it fails, explain why clearly
- **No workarounds**: If it doesn't work, it doesn't work
- **Preserve state**: Don't clean up or reset between attempts

The demo command proves that each phase delivers what it promises. If it can't be demonstrated, it's not really done.