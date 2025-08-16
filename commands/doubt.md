# Doubt - Aggressive Work Verification

## Goal

To perform aggressive, skeptical verification of recent work, catching any shortcuts, lazy implementations, or sneaky workarounds. This command is designed to be paranoid and thorough, ensuring no corners were cut and all work was completed properly.

## Input

Optional scope: $ARGUMENTS (e.g., `tests`, `implementation`, `all`)
- Defaults to checking everything if not specified

## Process

1. **Initial Suspicion Check:** Scan recent git changes and todo lists for red flags
2. **Test Suite Audit:** Verify tests are real, running, and meaningful
3. **Implementation Analysis:** Check for incomplete or placeholder code
4. **Code Quality Inspection:** Look for shortcuts and bad practices
5. **Requirements Verification:** Compare actual implementation against original requirements
6. **Generate Skeptical Report:** Present all findings with severity ratings

## Verification Phases

### Phase 1: Recent Changes Analysis

Examine recent commits and changes:
```bash
# Check recent commits for suspicious messages
git log --oneline -20 | grep -iE "(quick|fix|temp|hack|todo|fixme|workaround|disable|skip|comment.*out)"

# Look at recent file changes
git diff HEAD~5 --name-only

# Check current uncommitted changes
git status --porcelain
git diff
```

### Phase 2: Test Suite Integrity

**Suspicious Test Patterns to Detect:**

1. **Disabled Tests:**
   ```javascript
   // These are all red flags:
   it.skip('should do something', ...)
   xit('should validate input', ...)
   test.only('basic test', ...)  // Only running one test!
   fit('focused test', ...)
   describe.skip('entire suite disabled', ...)
   ```

2. **Commented Assertions:**
   ```javascript
   it('should validate data', () => {
     const result = processData(input);
     // expect(result.valid).toBe(true);  ← CAUGHT YOU!
     // expect(result.errors).toHaveLength(0);
     expect(result).toBeDefined(); // Weak assertion
   });
   ```

3. **Meaningless Tests:**
   ```javascript
   it('should work', () => {
     expect(true).toBe(true);  // Useless test
   });
   
   it('should not fail', () => {
     // No assertions at all!
   });
   ```

4. **Test Manipulation:**
   ```javascript
   beforeEach(() => {
     jest.spyOn(console, 'error').mockImplementation(); // Hiding errors!
   });
   ```

### Phase 3: Implementation Shortcuts

**Lazy Patterns to Detect:**

1. **Not Implemented:**
   ```javascript
   function complexFeature() {
     throw new Error('Not implemented');
     // or
     return; // Early return doing nothing
     // or
     // TODO: Actually implement this
   }
   ```

2. **Placeholder Code:**
   ```javascript
   function processData(data) {
     // Quick fix for now
     return data; // Just passing through!
   }
   ```

3. **Stubbed Functionality:**
   ```javascript
   async function fetchData() {
     // return await api.get('/data');  ← Commented out real code
     return { fake: 'data' }; // Hardcoded response
   }
   ```

4. **Error Swallowing:**
   ```javascript
   try {
     doSomethingRisky();
   } catch (e) {
     // Empty catch block - errors disappear!
   }
   ```

### Phase 4: Code Quality Violations

**Bad Practices to Find:**

1. **Debug Code Left Behind:**
   ```javascript
   console.log('HERE!!!');
   console.debug('data:', sensitiveData);
   debugger; // Breakpoint left in code
   ```

2. **Hardcoded Values:**
   ```javascript
   const API_KEY = 'sk-1234567890'; // Should be in env
   const MAX_RETRIES = 3; // Should be configurable
   const BASE_URL = 'http://localhost:3000'; // Environment-specific
   ```

3. **Commented Original Code:**
   ```javascript
   // function originalImplementation() {
   //   // 50 lines of commented code
   // }
   function quickHack() {
     return null; // "Simplified" version
   }
   ```

4. **Copy-Paste Evidence:**
   ```javascript
   // Multiple similar functions with slight variations
   function processUser() { /* ... */ }
   function processUser2() { /* ... */ }  // Lazy naming
   function processUserTemp() { /* ... */ } // Temporary?
   ```

### Phase 5: Requirements Gap Analysis

Compare implementation against requirements:

1. **Missing Features:**
   - Check if all documented requirements are implemented
   - Look for "Phase 2" or "Future" comments indicating deferred work
   - Verify all API endpoints exist and work

2. **Partial Implementation:**
   - Functions that only handle happy path
   - Missing error cases
   - Incomplete validation

3. **Changed Behavior:**
   - Implementation that differs from specification
   - "Simplified" versions that skip complexity

## Verification Commands

### Comprehensive Scan Commands

```bash
# Find all TODO/FIXME/HACK comments
grep -r "TODO\|FIXME\|HACK\|XXX\|TEMP\|QUICK" --include="*.js" --include="*.ts" --include="*.py"

# Find disabled tests
grep -r "\.skip\|\.only\|xit\|fit\|xdescribe\|fdescribe" --include="*.test.*" --include="*.spec.*"

# Find commented code blocks
grep -r "^[[:space:]]*//.*\|^[[:space:]]*#.*" --include="*.js" --include="*.ts" | grep -v "^.*:\/\/"

# Find console.log statements
grep -r "console\.\(log\|debug\|trace\)" --include="*.js" --include="*.ts" --exclude-dir=node_modules

# Find empty catch blocks
grep -A 1 "catch.*{" --include="*.js" --include="*.ts" | grep -B 1 "^[[:space:]]*}"

# Find Not Implemented patterns
grep -r "not implemented\|Not implemented\|NOT IMPLEMENTED" --include="*.js" --include="*.ts" --include="*.py"

# Find early returns doing nothing
grep -r "return;$\|return$" --include="*.js" --include="*.ts"

# Find weak assertions in tests
grep -r "expect.*toBeDefined()\|expect.*not.*toBeNull()" --include="*.test.*" --include="*.spec.*"
```

### Test Execution Verification

```bash
# Actually run the tests
npm test -- --verbose --no-coverage

# Check test output for skipped tests
npm test 2>&1 | grep -i "skip\|pending\|todo"

# Run tests with all console output visible
npm test -- --silent=false

# Check if tests are actually testing the new code
npm test -- --coverage --coveragePathIgnorePatterns=[] | grep -A 10 "Uncovered"
```

## Suspicion Scoring System

Rate findings by severity:

### 🔴 **CRITICAL** (Immediate Fix Required)
- Disabled test suites
- Not implemented functions
- Completely commented-out functionality
- Tests with no assertions
- Error swallowing with empty catch blocks

### 🟡 **HIGH** (Highly Suspicious)
- Individual skipped tests
- Weak assertions (toBeDefined only)
- TODO/FIXME in critical paths
- Hardcoded credentials or secrets
- Console.log with sensitive data

### 🟠 **MEDIUM** (Questionable Practices)
- Commented code blocks
- "Quick fix" comments
- Hardcoded configuration values
- Duplicate code (copy-paste)
- Missing error handling

### 🟢 **LOW** (Minor Concerns)
- Debug console.log statements
- Inconsistent naming
- Missing edge case handling
- Incomplete documentation

## Output Format

### When Suspicious Activity Found:

```
🚨 DOUBT REPORT - SUSPICIOUS ACTIVITY DETECTED 🚨

📊 Suspicion Summary:
  🔴 Critical Issues: 3
  🟡 High Priority: 5
  🟠 Medium Priority: 8
  🟢 Low Priority: 12

🔴 CRITICAL FINDINGS:

1. DISABLED TEST SUITE
   File: src/user.test.js:45
   Code: describe.skip('User validation tests', ...)
   Impact: Entire validation test suite is disabled!

2. NOT IMPLEMENTED FUNCTION
   File: src/api/handler.js:123
   Code: throw new Error('Not implemented yet');
   Impact: Core functionality missing!

3. COMMENTED ASSERTIONS
   File: src/auth.test.js:67-71
   Found: 5 commented expect() statements
   Impact: Test provides false confidence!

🟡 HIGH PRIORITY ISSUES:

1. CONSOLE.LOG WITH SENSITIVE DATA
   File: src/auth/login.js:89
   Code: console.log('password:', user.password);
   Risk: Security - Logging credentials!

2. EMPTY CATCH BLOCK
   File: src/data/processor.js:234
   Code: try { ... } catch(e) { }
   Risk: Errors being silently swallowed!

[... continue with all findings ...]

🔍 VERIFICATION COMMANDS TO RUN:

1. Check if tests actually pass:
   npm test -- --verbose

2. Look for more disabled tests:
   grep -r "\.skip\|\.only" src/

3. Verify implementation completeness:
   grep -r "TODO\|FIXME" src/

📝 RECOMMENDED ACTIONS:

1. ❗ Re-enable all skipped tests immediately
2. ❗ Implement the missing functions
3. ❗ Uncomment and fix test assertions
4. ⚠️ Remove all console.log statements
5. ⚠️ Add proper error handling
6. ⚠️ Replace hardcoded values with config

🎯 TRUST LEVEL: 23% - HIGHLY SUSPICIOUS

Multiple critical issues found that suggest shortcuts were taken.
This work needs immediate review and correction.
```

### When Everything Checks Out:

```
✅ DOUBT REPORT - SURPRISINGLY CLEAN ✅

📊 Verification Summary:
  Tests: All passing, no skipped tests found
  Implementation: Complete, no placeholders detected
  Code Quality: No major shortcuts identified
  Requirements: All features appear implemented

🔍 Verified:
  ✓ 47 test files scanned - all active
  ✓ 234 test cases found - none skipped
  ✓ No "not implemented" patterns found
  ✓ No console.log statements in production code
  ✓ Error handling present in async functions
  ✓ No obvious hardcoded values

⚠️ Minor Observations:
  - 3 TODO comments (all marked as enhancements)
  - Some test descriptions could be more specific
  - Found 2 long functions that could be refactored

🎯 TRUST LEVEL: 87% - ACCEPTABLE

The work appears to be honestly completed without major shortcuts.
Minor improvements could be made but no sneaky behavior detected.
```

## Configuration

The doubt command should check for a `.doubtrc` file for custom patterns:

```json
{
  "customPatterns": [
    "DEPRECATED",
    "REMOVE BEFORE PRODUCTION",
    "DO NOT COMMIT"
  ],
  "ignorePaths": [
    "node_modules",
    ".git",
    "coverage"
  ],
  "strictMode": true,
  "paranoidLevel": "maximum"
}
```

## Special Detection Patterns

### The "Fixed the Tests" Anti-Pattern
Watch for commits that "fix" failing tests by:
- Commenting out assertions
- Changing expected values to match actual (wrong) values
- Adding `.skip` to problematic tests
- Reducing test complexity

### The "Simplified Implementation" Excuse
Detect when complex features are "simplified" to avoid work:
- Removing validation
- Skipping edge cases
- Hardcoding instead of calculating
- Removing features claimed as "unnecessary"

### The "It Works On My Machine" Pattern
- Environment-specific code
- Hardcoded local paths
- Assumptions about system configuration
- Missing dependency checks

## Usage Examples

```bash
# Run comprehensive doubt check
/doubt

# Focus on test integrity
/doubt tests

# Check implementation only
/doubt implementation

# Maximum paranoia mode
/doubt --paranoid

# Check specific directory
/doubt src/api
```

## Final Instructions

1. Be EXTREMELY skeptical - assume the worst
2. Check everything twice
3. Don't trust comments that say "this works"
4. Verify tests actually test something meaningful
5. Look for patterns that hide problems
6. Check git history for suspicious "fixes"
7. Run the actual tests to verify they pass
8. Compare implementation against original requirements
9. Flag any code that seems too simple for the requirement
10. Trust nothing, verify everything

Remember: The goal is to catch laziness, shortcuts, and sneaky workarounds. Be paranoid!