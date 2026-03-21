# Check CI Status and Investigate Failures

## Goal

Monitor CI/CD pipeline status after pushing commits. When failures occur, delegate to the cata-debugger agent for systematic investigation and evidence-based root cause analysis.

## Input

Optional commit reference: $ARGUMENTS (e.g., `HEAD`, `abc1234`, `feature-branch`)
- Defaults to the latest commit on the current branch if not specified

## Process

1. **Identify Recent Commits:** Get the latest commit(s) to check CI status for
2. **Detect CI Platform:** Identify which CI/CD system is in use
3. **Monitor CI Status:** Poll for CI pipeline completion with real-time updates
4. **Handle Results:**
   - If success → Present success summary
   - If failure → Launch cata-debugger agent to investigate
5. **Present Report:** Show agent's investigation findings or success status

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

## Failure Investigation

When CI fails, delegate investigation to the cata-debugger agent:

### Agent Invocation

Use the Task tool to launch the cata-debugger agent with:
- CI job/pipeline ID
- Failed job names
- Relevant log excerpts
- Commit information

Example prompt for agent:
```
Investigate CI failure for commit [SHA]:
- Failed jobs: [job names]
- CI platform: [GitHub Actions/GitLab CI/etc]
- Job logs available via: [command to fetch logs]

Please gather evidence about:
1. What specifically failed (tests, build, lint, etc.)
2. Exact error messages and stack traces
3. Which files/changes are involved
4. Root cause based on evidence

Provide a complete investigation report.
```

### What the Agent Will Do

The cata-debugger agent will:
1. Fetch complete CI logs for failed jobs
2. Identify exact error messages and locations
3. Trace the failure through execution flow
4. Gather evidence about environment and context
5. Present findings without proposing fixes

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

🔍 Launching cata-debugger agent to investigate...
```

**Then present the agent's complete investigation report, which will include:**
- Problem Investigation Report
- Evidence Gathered (logs, errors, stack traces)
- Root Cause Analysis (based on facts)
- Affected Components
- Recommendations for Resolution

The agent's report provides evidence-based findings without implementing fixes.

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

## Final Instructions

### Core Workflow
1. Always start by checking the latest commit unless specified otherwise
2. Detect CI platform automatically - don't assume GitHub Actions
3. Monitor CI status continuously without requiring user input
4. When CI completes:
   - **Success** → Present success summary with timing details
   - **Failure** → Launch cata-debugger agent immediately

### Agent Delegation
5. When launching cata-debugger:
   - Provide commit SHA and job details
   - Include command to fetch relevant logs
   - Specify which jobs failed
   - Let agent conduct systematic investigation

### Reporting
6. Present the agent's complete investigation report
7. The agent's report will be evidence-based, not solution-based
8. Never modify code or implement fixes automatically
9. Wait for human decision on next steps after presenting findings

### Error Handling
10. Handle multiple CI platforms if repository uses several
11. If CI is still running after 30 minutes, report timeout and current status

## Usage Examples

```bash
# Check CI for latest commit
/check-ci

# Check CI for specific commit
/check-ci abc1234

# Check CI for a branch
/check-ci feature/new-api
```