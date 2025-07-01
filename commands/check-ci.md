# Check CI Status and Fix Failures

## Goal

To monitor CI/CD pipeline status after pushing commits, automatically analyze any failures, and propose specific fixes for identified issues. This command streamlines the debugging process by parsing CI logs, identifying error patterns, and suggesting actionable solutions.

## Input

Optional commit reference: $ARGUMENTS (e.g., `HEAD`, `abc1234`, `feature-branch`)
- Defaults to the latest commit on the current branch if not specified

## Process

1. **Identify Recent Commits:** Get the latest commit(s) to check CI status for
2. **Detect CI Platform:** Identify which CI/CD system is in use
3. **Monitor CI Status:** Poll for CI pipeline completion with real-time updates
4. **Analyze Failures:** If CI fails, extract and parse error logs
5. **Propose Fixes:** Generate specific code changes to resolve identified issues
6. **Present Solutions:** Display actionable fixes with clear next steps

## CI Platform Detection

The command automatically detects the CI/CD platform by examining configuration files:

### Detection Priority

1. **GitHub Actions**
   - Check for `.github/workflows/*.yml` or `.github/workflows/*.yaml`
   - Use `gh` CLI for API access
   - Parse workflow runs and job logs

2. **GitLab CI**
   - Check for `.gitlab-ci.yml`
   - Use `glab` CLI for API access
   - Parse pipeline and job logs

3. **CircleCI**
   - Check for `.circleci/config.yml`
   - Use CircleCI API with detected tokens

4. **Jenkins**
   - Check for `Jenkinsfile` or `.jenkins`
   - Use Jenkins API if URL is configured

5. **Travis CI**
   - Check for `.travis.yml`
   - Use Travis API with authentication

6. **Azure DevOps**
   - Check for `azure-pipelines.yml`
   - Use Azure CLI if available

## Monitoring Workflow

### 1. Initial Status Check

```bash
# Get latest commit
git rev-parse HEAD

# Get commit details
git log -1 --format="%H %s"

# Check push status
git log origin/[branch]..HEAD
```

### 2. CI Status Polling

**For GitHub Actions:**
```bash
# List workflow runs for commit
gh run list --commit [SHA]

# Get run details
gh run view [RUN_ID]

# Watch run status
gh run watch [RUN_ID]
```

**For GitLab CI:**
```bash
# Get pipeline for commit
glab ci list --per-page 1

# View pipeline details
glab ci view [PIPELINE_ID]

# Get job logs
glab ci trace [JOB_ID]
```

### 3. Real-time Updates

Display status updates every 5-10 seconds:
```
⏳ CI Status: In Progress
  ✓ Build: Success
  ⏳ Tests: Running... (2m 15s)
  ⏳ Lint: Queued
  - Deploy: Pending
```

## Error Analysis Patterns

The command recognizes and analyzes common CI failure patterns:

### 1. Test Failures

**Pattern Recognition:**
- Unit test failures: `FAIL:`, `AssertionError`, `Expected .* but got`
- Integration test failures: `Connection refused`, `timeout`
- Test file not found: `No such file or directory`

**Analysis Approach:**
- Extract failing test names and assertions
- Identify changed files that might have broken tests
- Check for missing test dependencies

### 2. Build Errors

**Pattern Recognition:**
- Compilation errors: `error:`, `cannot find symbol`
- Module not found: `Module not found`, `Cannot resolve`
- Syntax errors: `SyntaxError`, `unexpected token`

**Analysis Approach:**
- Parse error locations (file:line:column)
- Check for missing imports or dependencies
- Verify syntax in recently changed files

### 3. Linting Issues

**Pattern Recognition:**
- ESLint: `error  [rule-name]`
- Prettier: `Code style issues found`
- Python linting: `flake8`, `pylint` errors

**Analysis Approach:**
- Extract specific rule violations
- Map to fixable vs non-fixable issues
- Generate formatting commands

### 4. Dependency Problems

**Pattern Recognition:**
- npm/yarn: `npm ERR!`, `Module not found`
- pip: `No matching distribution found`
- Missing system dependencies: `command not found`

**Analysis Approach:**
- Identify missing packages
- Check lock file consistency
- Verify version compatibility

## Fix Generation

Based on the error analysis, generate specific fixes:

### 1. Test Fixes

```markdown
## Test Failure Fix

**Failed Test:** `test_user_authentication`
**Error:** AssertionError: Expected status 200 but got 401

**Proposed Fix:**
1. Update the test to include authentication token:
   ```python
   headers = {'Authorization': 'Bearer test-token'}
   response = client.get('/api/user', headers=headers)
   ```

2. Or update the implementation to handle missing auth:
   ```python
   if not request.headers.get('Authorization'):
       return JsonResponse({'error': 'Unauthorized'}, status=401)
   ```
```

### 2. Build Fixes

```markdown
## Build Error Fix

**Error:** Cannot find module './utils/helper'
**Location:** src/components/Dashboard.js:5

**Proposed Fix:**
1. Check if file was moved/renamed:
   ```bash
   find . -name "helper.js" -o -name "helper.ts"
   ```

2. Update import path:
   ```javascript
   // Change from:
   import { helper } from './utils/helper';
   // To:
   import { helper } from '../utils/helper';
   ```
```

### 3. Linting Fixes

```markdown
## Linting Fix

**Issues Found:** 5 style violations

**Auto-fix available:**
```bash
npm run lint -- --fix
# or
npx eslint . --fix
```

**Manual fixes needed:**
- Line 45: Unused variable 'tempData' - remove or use it
- Line 78: Missing return type - add explicit type annotation
```

### 4. Dependency Fixes

```markdown
## Dependency Fix

**Error:** Module 'requests' not found

**Proposed Fix:**
1. Add to requirements.txt:
   ```
   requests==2.31.0
   ```

2. Install locally:
   ```bash
   pip install requests
   ```

3. Update CI config to install dependencies:
   ```yaml
   - run: pip install -r requirements.txt
   ```
```

## Output Format

### Success Case

```
✅ CI Status: All checks passed!

📊 Summary:
  ✓ Build: Success (1m 23s)
  ✓ Tests: 156 passed (2m 45s)
  ✓ Lint: No issues (0m 15s)
  ✓ Security: No vulnerabilities (0m 38s)

🎉 Your code is ready to merge!
```

### Failure Case

```
❌ CI Status: Failed

📊 Summary:
  ✓ Build: Success (1m 23s)
  ❌ Tests: 2 failed, 154 passed (2m 45s)
  ⚠️ Lint: 3 warnings (0m 15s)
  ✓ Security: No vulnerabilities (0m 38s)

🔍 Analyzing failures...

## Test Failures Detected

### 1. test_user_profile_update
**Error:** AssertionError: 404 != 200
**File:** tests/test_api.py:45

**Likely Cause:** The endpoint '/api/profile' may have been renamed or removed.

**Proposed Fix:**
[Detailed fix as shown above]

### 2. test_data_validation
[Additional test failure details]

## Next Steps:
1. Apply the proposed fixes above
2. Run tests locally: `npm test`
3. Commit fixes: `/commit-and-push`
4. Re-run CI: `/check-ci`
```

## Error Handling

- **No CI Configuration:** Inform user that no CI configuration was detected
- **Authentication Required:** Guide user to authenticate with CI platform
- **API Rate Limits:** Handle rate limiting with appropriate delays
- **Network Issues:** Retry with exponential backoff
- **Timeout:** Stop monitoring after 30 minutes with timeout message
- **Partial Logs:** Attempt to work with available information

## Platform-Specific Features

### GitHub Actions

- Support for matrix builds (multiple job variations)
- Artifact download for detailed logs
- Re-run failed jobs command
- Workflow dispatch triggers

### GitLab CI

- Pipeline stage analysis
- Manual job triggers
- Merge request pipeline support
- Child pipeline detection

## Configuration Options

Users can customize behavior via environment variables:

- `CI_CHECK_TIMEOUT`: Maximum time to wait for CI completion (default: 30m)
- `CI_POLL_INTERVAL`: How often to check status (default: 10s)
- `CI_AUTO_FIX`: Whether to auto-apply simple fixes (default: false)

## Final Instructions

1. Always start by checking the latest commit unless specified otherwise
2. Detect CI platform automatically - don't assume GitHub Actions
3. Monitor CI status continuously without requiring user input
4. Parse all available logs thoroughly before proposing fixes
5. Generate specific, actionable fixes rather than generic advice
6. Present fixes in order of likelihood to resolve the issue
7. Include commands that can be copy-pasted
8. Never modify code automatically - always present fixes for review
9. Handle multiple CI platforms if repository uses several
10. Provide clear next steps after presenting fixes

## Usage Examples

```bash
# Check CI for latest commit
/check-ci

# Check CI for specific commit
/check-ci abc1234

# Check CI for a branch
/check-ci feature/new-api
```