---
description: Run comprehensive verification with multiple agents (reviewer, tester, UX, coherence)
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, AskUserQuestion
---

# Verify Changes

## Goal

Run comprehensive verification before considering changes complete. This command launches multiple specialized agents in parallel to review code quality, run tests, and validate user experience.

## Input

Optional arguments: $ARGUMENTS

**Scope Control:**
- `--scope=staged`: Verify only staged changes
- `--scope=unstaged`: Verify only unstaged modified files
- `--scope=branch`: Verify all changes in current branch vs base
- `--scope=all`: Verify entire codebase (comprehensive audit)
- `--files="file1,file2"`: Verify specific files only
- `--module=path`: Verify specific module/directory
- Default (no scope arg): Auto-detect from git state (staged or modified files)

**Other Options:**
- `--skip-ux`: Skip UX review for pure backend changes
- `--skip-security`: Skip security review (not recommended)

## Scope Detection Strategy

Before verification, determine what files/changes to focus on:

**1. Parse User-Specified Scope (if provided):**
- Check `$ARGUMENTS` for `--scope=`, `--files=`, or `--module=` flags
- If specified, use that exact scope
- Skip auto-detection

**2. Auto-Detect Scope (default behavior):**

Priority order:
1. **Staged changes exist?** → Scope to staged files only
2. **Unstaged changes exist?** → Scope to modified files only
3. **Branch has commits ahead of base?** → Scope to branch changes
4. **No changes detected?** → Report "nothing to verify"

**Git Commands for Scope Detection:**

```bash
# Detect staged files
STAGED=$(git diff --cached --name-only)

# Detect unstaged modified files
UNSTAGED=$(git diff --name-only)

# Get all uncommitted changes
ALL_CHANGES=$(git diff HEAD --name-only)

# Get branch changes (for --scope=branch)
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
MERGE_BASE=$(git merge-base HEAD origin/$BASE_BRANCH 2>/dev/null || git merge-base HEAD $BASE_BRANCH 2>/dev/null || echo "HEAD")
BRANCH_FILES=$(git diff --name-only $MERGE_BASE..HEAD)

# Get changed line ranges per file (for detailed scope)
git diff --unified=0 HEAD | grep -E '^\+\+\+ b/|^@@' > /tmp/changes.txt
# Parse to extract: file.ts (lines 45-67, 89-102)
```

**3. Build Scope Context:**

Create a list of files in scope with status:
- `file.ts` (modified, lines 45-67, 89-102)
- `new-file.ts` (added, entire file)
- `old-file.ts` (deleted)

**4. Format Scope for Agents:**

Pass scope to each agent as:
```
VERIFICATION SCOPE:
Files in scope:
- src/auth/login.ts (modified, lines 45-67, 89-102)
- src/auth/middleware.ts (modified, lines 12-34)
- tests/auth/login.test.ts (added, entire file)

CRITICAL SCOPE CONSTRAINTS:
- ONLY flag issues in code that was ADDED or MODIFIED in these files/lines
- DO NOT flag issues in surrounding context or old code unless it blocks the new changes
- DO NOT flag issues in other files not listed above
- Focus exclusively on the quality of the NEW or CHANGED code

Exception: You MAY flag issues in old code IF:
1. The new changes directly interact with or depend on that old code
2. The old code issue is causing the new code to be incorrect
3. The old code issue creates a blocker for the new functionality

Git commands to see your scoped changes:
git diff HEAD -- <scoped-files>
git diff --cached -- <scoped-files>
```

## Process

1. **Determine Verification Scope:** Detect what to verify (see Scope Detection Strategy above)
2. **Launch Verification Agents IN PARALLEL:**
   - `cata-reviewer`: Code review for design adherence, over-engineering, AI slop
   - `cata-tester`: Execute test suite and report failures
   - `cata-ux-reviewer`: Test user-facing changes (unless `--skip-ux` or clearly backend-only)
   - `cata-coherence`: Check if changes fit in the codebase (reinvented wheels, pattern violations, stale docs/AI tooling)
   - `cata-security`: Security vulnerability detection (unless `--skip-security`)
3. **Manual Exercise (cata-exerciser):** Start the app and exercise the feature end-to-end
   - If BLOCKED with LOGIN_REQUIRED or UNCLEAR_FEATURE: Ask user for help, retry
4. **Debug Analysis (if failures):** If cata-tester OR cata-ux-reviewer OR cata-exerciser failed, launch cata-debugger for root cause analysis
5. **Generate Unified Report:** Combine all agent findings with clear verdict
6. **STOP:** Present report and wait for human decision

## CRITICAL: No Hiding Issues

**This is the most important principle of this command.**

The AI has a tendency to soften or hide issues. This is UNACCEPTABLE. The report must be brutally honest:

### Required Mindset

- Tests should ALWAYS pass - 100% pass rate is the only acceptable outcome
- Tests should ALWAYS be able to run - any setup/environment issue is a bug
- Be transparent - show ALL issues prominently
- Report facts - let humans decide what to act on

### Severity Scale (1-10)

All agents use a numeric severity scale instead of categorical labels:

| Range | Impact | Examples |
|-------|--------|----------|
| 9-10 | Critical | Data loss, security vulnerability, cannot function |
| 7-8 | High | Major functionality broken, significant problems |
| 5-6 | Moderate | Clear issues, workarounds exist |
| 3-4 | Low | Minor issues, slight inconvenience |
| 1-2 | Trivial | Polish, cosmetic, optional improvements |

**Important:** Severity reflects "how big is this issue?" - NOT "must you fix it?" The human decides what to act on.

## Agent Invocation

Launch all agents in a single message using the Task tool. **CRITICAL:** Include scope information in each agent prompt.

**Template for Agent Prompts:**

Each agent prompt MUST include the scope context at the beginning:

```
VERIFICATION SCOPE:
[Insert determined scope here - list of files with line ranges]

CRITICAL SCOPE CONSTRAINTS:
- ONLY flag issues in code that was ADDED or MODIFIED in the scoped files/lines
- DO NOT flag issues in surrounding context or old code unless it blocks the new changes
- DO NOT flag issues in other files not listed in scope
- Focus exclusively on the quality of the NEW or CHANGED code

Exception: You MAY flag issues in old code IF:
1. The new changes directly interact with or depend on that old code
2. The old code issue is causing the new code to be incorrect
3. The old code issue creates a blocker for the new functionality

[Agent-specific instructions below...]
```

**Agent Invocation Examples:**

```
# Agent 1: Code Review
Task tool with:
- subagent_type: "cata-reviewer"
- description: "Review code changes in scope"
- prompt: "VERIFICATION SCOPE:
  Files in scope:
  [Insert scope list here - e.g.:]
  - src/auth/login.ts (modified, lines 45-67, 89-102)
  - src/auth/middleware.ts (modified, lines 12-34)
  - tests/auth/login.test.ts (added, entire file)

  CRITICAL SCOPE CONSTRAINTS:
  - ONLY review code in the files and line ranges listed above
  - Flag issues ONLY in newly added or modified code
  - Ignore issues in old code unless they block the new changes
  - Do not review files outside this scope
  - Focus on the quality and correctness of THIS change set

  When checking design adherence, cross-cutting completeness, etc:
  - Verify that changes in scope are complete (e.g., if route added, check if tests exist)
  - But do NOT audit the entire codebase for unrelated issues

  Exception: Flag old code issues IF they directly impact the new changes.

  Use git diff to see the actual changes:
  git diff HEAD -- [scoped files]

  Review for: design adherence, over-engineering, AI slop, structural completeness.

  OUTPUT FORMAT: For each issue found, provide:
  - Title (short description)
  - Severity (1-10, where 1=trivial, 10=critical)
  - Location (file:line)
  - Description (what the issue is and why it matters)"

# Agent 2: Test Execution
Task tool with:
- subagent_type: "cata-tester"
- description: "Run test suite"
- prompt: "VERIFICATION SCOPE AWARENESS:
  The current change set modified these files:
  [Insert scope list here]

  Run the full test suite for this repository.
  First discover the test framework:
  - Check package.json for test scripts
  - Check for pytest, cargo test, go test, etc.

  Execute the full test suite.
  Report exact pass/fail counts.
  If tests cannot run, report what prevented execution.

  When reporting failures, for EACH failure provide:
  - Title (short description of what failed)
  - Severity (1-10, where 1=trivial, 10=critical)
  - Location (test file:line)
  - Description (error message, expected vs actual)
  - Scope annotation: IN-SCOPE or OUT-OF-SCOPE relative to changed files"

# Agent 3: UX Review (unless skipped)
Task tool with:
- subagent_type: "cata-ux-reviewer"
- description: "Review user-facing changes in scope"
- prompt: "VERIFICATION SCOPE:
  Files in scope:
  [Insert scope list here]

  UX REVIEW CONSTRAINTS:
  - ONLY test user-facing changes in the scoped files
  - Do not audit the entire UI/CLI for issues
  - Focus on the UX of what changed in this scope
  - Ignore UX issues in unchanged parts of the application

  Review user experience for the scoped changes.
  Test any UI, CLI output, error messages, or API responses that were modified.
  Report usability issues and friction points in THE SCOPED CHANGES ONLY.

  OUTPUT FORMAT: For each issue found, provide:
  - Title (short description)
  - Severity (1-10, where 1=trivial, 10=critical)
  - Location (page/component/command)
  - Description (user impact and what you observed)"

# Agent 4: Coherence Check
Task tool with:
- subagent_type: "cata-coherence"
- description: "Check if scoped changes fit in codebase"
- prompt: "VERIFICATION SCOPE:
  Files in scope:
  [Insert scope list here]

  COHERENCE CONSTRAINTS:
  - Check if THESE specific changes follow codebase patterns
  - Look for reinvented wheels in THIS change set
  - Verify THIS change doesn't violate existing patterns
  - Check documentation that relates to THESE changed files
  - Do not audit the entire codebase for pattern violations
  - Focus on: 'Do these new changes fit well?'

  Research existing patterns, utilities, and conventions relevant to the scoped changes.
  Look for reinvented wheels - utilities that already exist that these changes duplicate.
  Check for pattern violations - different approaches than rest of codebase.
  Verify AI tooling (.claude/) matches actual behavior IF the scoped changes touch AI tooling.
  Check if documentation reflects the scoped code changes.

  OUTPUT FORMAT: For each issue found, provide:
  - Title (short description)
  - Severity (1-10, where 1=trivial, 10=critical)
  - Location (file:line)
  - Description (what the issue is and existing pattern to follow)"

# Agent 5: Security Review (unless --skip-security)
Task tool with:
- subagent_type: "cata-security"
- description: "Security vulnerability detection in scope"
- prompt: "VERIFICATION SCOPE:
  Files in scope:
  [Insert scope list here]

  SECURITY REVIEW CONSTRAINTS:
  - ONLY flag security issues in code that was ADDED or MODIFIED
  - First research how security is done in THIS codebase (auth, tenant isolation, validation)
  - Flag deviations from established security patterns
  - Do not audit the entire codebase for security issues
  - Focus on: 'Does this new code introduce security vulnerabilities?'

  Research existing security patterns:
  - How authentication/authorization works
  - How tenant isolation is implemented
  - What input validation patterns exist
  - What sanitization utilities are available

  Then analyze the scoped changes for:
  - Injection vulnerabilities (SQL, command, XSS)
  - Authentication/authorization issues
  - Multi-tenant data isolation violations
  - Data exposure (secrets, sensitive data in logs/responses)
  - Web security issues (cookies, CORS, CSRF)
  - Cryptography issues

  OUTPUT FORMAT: For each issue found, provide:
  - Title (short description)
  - Severity (1-10, where 1=trivial, 10=critical - multi-tenant leaks are always 9-10)
  - Location (file:line)
  - Category (Injection/Auth/Multi-Tenant/Data Exposure/Web Security/Crypto/Config)
  - Description (what the vulnerability is and attack vector)"
```

**Important:** Replace `[Insert scope list here]` with the actual scope determined in step 1.

## Conditional Debug Analysis

**After the initial 5 agents complete**, check if cata-tester OR cata-ux-reviewer reported failures. If either failed:

```
# Agent 6: Debug Analysis (conditional)
Task tool with:
- subagent_type: "cata-debugger"
- description: "Analyze test/UX failures in scope"
- prompt: "VERIFICATION SCOPE CONTEXT:
  Files changed in this scope:
  [Insert scope list here]

  DEBUGGING SCOPE:
  - Focus on failures that could be caused by these recent changes
  - Investigate the interaction between new code and existing code
  - If failures are unrelated to the scope, note that explicitly

  Analyze the root cause of the failures reported by verification agents.
  Review the test failures and/or UX issues found.
  Use git, logs, and available tools to investigate.
  Provide detailed diagnostic report without fixing anything.
  Focus on identifying WHY the failures occurred, especially in relation to the scoped changes.

  OUTPUT FORMAT: For each root cause identified, provide:
  - Title (short description of root cause)
  - Severity (1-10, where 1=trivial, 10=critical)
  - Location (file:line or area)
  - Description (detailed diagnosis and evidence)"
```

Only launch this agent if there are actual failures to analyze. Skip if all tests passed and UX review found no high-severity issues.

## Manual Exercise Testing (cata-exerciser)

After the initial 5 agents complete, launch `cata-exerciser` to actually run and test the application.

This step verifies that the feature works when you actually use it, not just when automated tests run.

### Why This Matters

Automated tests pass, but the app can still be broken:
- Tests mock dependencies that fail in real env
- Integration points that aren't fully tested
- Startup issues that tests bypass
- UI that renders but doesn't function

The exerciser catches these by actually running the app.

### When to Run cata-exerciser

**ALWAYS. No skip flag. Non-negotiable.**

If the exerciser cannot complete (no app, can't start, etc.), that is reported as a severity 9-10 issue - not silently skipped.

Even for pure libraries or config-only changes, the exerciser should attempt to run and report what it finds.

### Exercise Agent Invocation

```
# Agent: Manual Exercise
Task tool with:
- subagent_type: "cata-exerciser"
- description: "Exercise feature end-to-end"
- prompt: "VERIFICATION SCOPE:
  Files in scope:
  [Insert scope list here]

  Exercise the application end-to-end:
  1. Start the application (docker compose, npm run dev, etc.)
  2. Navigate to the feature affected by these changes
  3. Exercise the feature as a user would
  4. Report whether it works

  If you hit a barrier (can't start, need credentials, unclear what to test):
  - Return BLOCKED status with specific reason
  - I will ask the user for help if needed

  OUTPUT FORMAT: For each issue found, provide:
  - Title (short description)
  - Severity (1-10, where 1=trivial, 10=critical)
  - Location (where in the app)
  - Description (what failed and what you observed)"
```

### Handling Exercise Barriers

If cata-exerciser returns BLOCKED with reason `LOGIN_REQUIRED` or `UNCLEAR_FEATURE`:

1. **Use AskUserQuestion** to get help from the user:
   - For LOGIN_REQUIRED: "The exerciser needs to log in to test the feature. Please choose: (1) Provide test credentials (username and password), (2) Point me to a file containing credentials (e.g., .env, seeds), or (3) Log in manually in your browser and tell me when ready to continue."
   - For UNCLEAR_FEATURE: "I'm not sure what feature to exercise. The changed files are: [insert actual file list]. What user flow or feature should I test?"

2. **Re-launch cata-exerciser** with the user's response added to the prompt

3. **If user can't help** or second attempt also fails: Final status is BLOCKED

### Exercise Barriers

If cata-exerciser cannot complete, report it factually with severity:
- App won't start → Report with severity 10
- Database not available → Report with severity 9
- Can't log in (after asking user) → Report with severity 8
- Feature doesn't work → Report with severity based on impact
- Environmental issue → Report with appropriate severity

Manual verification barriers are reported as high-severity issues in the Issues Found table.

## When to Skip UX Review

Only skip `cata-ux-reviewer` when ALL of these are true:
- No changes to UI components, templates, or frontend code
- No changes to CLI output formatting or help text
- No changes to error messages or user-facing strings
- No changes to API response messages
- Pure backend, infrastructure, or internal refactoring only

When in doubt, RUN THE UX REVIEW. It's better to review unnecessarily than to miss issues.

## Test Framework Detection

Discover and run tests based on what exists in the repository:

### JavaScript/TypeScript
```bash
# Check package.json for test script
cat package.json | jq -r '.scripts.test // empty'
# Run: npm test, yarn test, pnpm test
```

### Python
```bash
# Check for pytest
pytest --version && pytest
# Or: python -m pytest
# Or: python -m unittest discover
```

### Rust
```bash
cargo test
```

### Go
```bash
go test ./...
```

### Other
Look for Makefile targets, CI configuration, or README instructions.

## Report Format

After all agents complete, generate this unified report:

```markdown
# Verification Report

## Scope

**Mode:** [staged / unstaged / branch / all / files / module]

**Files Verified:**
- src/auth/login.ts (modified, lines 45-67, 89-102)
- src/auth/middleware.ts (modified, lines 12-34)
- tests/auth/login.test.ts (added, entire file)

**Files Excluded:** All other files in codebase (not in scope for this verification)

---

## Agent Results Summary

| Agent | Status | Notes |
|-------|--------|-------|
| cata-tester | X passed, Y failed | [brief note if any] |
| cata-reviewer | Completed | Found N items |
| cata-ux-reviewer | Completed / Skipped | Found N items / [reason] |
| cata-coherence | Completed | Found N items |
| cata-security | Completed / Skipped | Found N items / [reason] |
| cata-exerciser | PASSED / FAILED / BLOCKED | [reason if blocked] |
| cata-debugger | Ran / N/A | [if applicable] |

---

## Issues Found

[Deduplicated issues from all agents, sorted by severity descending]

Issues are assigned **VI-{n}** IDs (Verification Issue) for easy reference during discussion.

| ID | Sev | Title | Sources | Description |
|----|-----|-------|---------|-------------|
| VI-1 | 9 | [Short title] | tester, reviewer | [Combined description from all agents that flagged this] |
| VI-2 | 7 | [Short title] | reviewer, coherence | [Description with context] |
| VI-3 | 5 | [Short title] | ux | [Description] |
| VI-4 | 3 | [Short title] | coherence | [Description] |

*Severity: 9-10 Critical | 7-8 High | 5-6 Moderate | 3-4 Low | 1-2 Trivial*

*Sources column shows which agents flagged the issue. Multiple sources = higher confidence the issue is real.*

**Total: N issues from M agent findings (deduplicated)**

---

STOP - Awaiting human decision.
```

## Issue Deduplication

When combining agent findings into the final report:

1. **Collect all findings** from each agent in structured format (title, severity, location, description)

2. **Identify duplicates** - same underlying issue flagged by multiple agents:
   - Same file/location mentioned
   - Same root cause described differently
   - Same symptom from different perspectives (code issue → test failure → user impact)

3. **Merge into single issue:**
   - Create one VI-{n} entry
   - List all source agents in Sources column
   - Combine descriptions to show all perspectives
   - Use the **highest severity** from the merged findings

4. **Assign sequential IDs** (VI-1, VI-2, VI-3...) to deduplicated issues

5. **Sort by severity** descending (most severe first)

6. **Show deduplication stats** - "N issues from M agent findings"

**Example Deduplication:**
```
Agent findings:
- cata-reviewer: "Missing error handling in auth.ts" (severity: 6)
- cata-tester: "Test fails - unhandled exception in auth flow" (severity: 8)
- cata-ux-reviewer: "User sees cryptic error on login failure" (severity: 7)

Merged into:
| VI-1 | 8 | Unhandled auth error | reviewer, tester, ux | Missing error handling causes test failure and cryptic user-facing error |
```

## Execution Steps

1. **Determine verification scope:**
   - Parse `$ARGUMENTS` for scope flags (`--scope=`, `--files=`, `--module=`)
   - If scope specified, use that
   - If no scope specified, auto-detect (staged → unstaged → branch)
   - Run git commands to get list of files and changed line ranges
   - Build scope context with files, statuses, and line ranges
   - If no changes detected, report "Nothing to verify" and stop

2. **Check for changes:**
   ```bash
   git status
   git diff --stat [scope-specific args]
   ```

3. **Determine if UX review needed:**
   - Parse `$ARGUMENTS` for `--skip-ux` flag
   - If not explicitly skipped, analyze changed files in scope
   - Look for UI/frontend/CLI/message changes
   - Default to INCLUDING UX review

4. **Format scope for agents:**
   - Create scope section with file list and line ranges
   - Add scope constraints section
   - Prepare to inject into each agent prompt

5. **Launch agents in parallel:**
   - Use Task tool with multiple tool calls in single message
   - All 5 agents (fewer if UX/security skipped) run simultaneously
   - **CRITICAL:** Include scope information in each agent prompt
   - Each agent receives the exact files and lines to focus on

6. **Collect results:**
   - Wait for all agents to complete
   - Gather outputs from each

7. **Launch exerciser:**
   - Launch cata-exerciser to start the app and exercise the feature
   - **Include scope context in exerciser prompt**
   - If returns BLOCKED with LOGIN_REQUIRED or UNCLEAR_FEATURE:
     a. Use AskUserQuestion to get help from user
     b. Re-launch cata-exerciser with user's response
     c. If still blocked, record as final BLOCKED status

8. **Launch debugger if failures:**
   - If cata-tester OR cata-ux-reviewer OR cata-exerciser reported failures
   - Launch cata-debugger to analyze root cause
   - **Include scope context in debugger prompt**
   - Gather diagnostic output

9. **Generate unified report:**
   - **Add scope section at top** showing what was verified
   - Determine overall verdict
   - List ALL issues prominently
   - Include exercise results (critical for end-to-end verification)
   - Include debug analysis if debugger ran
   - Make blockers impossible to miss
   - Clearly indicate what was IN scope vs excluded

10. **STOP and present:**
    - Display the report
    - Wait for human decision
    - DO NOT proceed to any next steps automatically

## Important Notes

- **Scope-aware verification** - Always detect and communicate scope to agents
- **Include scope in ALL agent prompts** - Critical for focused reviews
- **Run initial agents in parallel** - Use single message with multiple Task tool calls
- **Run exerciser after initial agents** - Sequential to avoid resource conflicts
- **Never auto-proceed** - Always stop after presenting report
- **Be honest** - Surface all issues, don't minimize or hide
- **Assume tests work** - Any test issue is a bug, not an excuse
- **Exercise failures are blockers** - Can't verify if can't exercise
- **Default to focused scope** - Auto-detect changed files unless --scope=all specified
- **Make scope visible** - Always show what was verified in the report

## After Verification - MANDATORY STOP

**🛑 After presenting the unified report, you MUST STOP COMPLETELY.**

DO NOT:
- ❌ Fix any issues found
- ❌ Re-run failed tests
- ❌ Proceed to commit
- ❌ Continue to next steps
- ❌ Act on agent findings

DO:
- ✅ Present the complete report
- ✅ Wait for human to review
- ✅ Wait for explicit instructions
- ✅ Answer clarifying questions if asked

**The verification report is FOR HUMAN DECISION-MAKING ONLY.**
