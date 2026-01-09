---
description: Run comprehensive verification with multiple agents (reviewer, tester, UX, coherence)
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite
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
3. **Debug Analysis (if failures):** If cata-tester OR cata-ux-reviewer failed, launch cata-debugger for root cause analysis
4. **Generate Unified Report:** Combine all agent findings with clear verdict
5. **STOP:** Present report and wait for human decision

## CRITICAL: No Hiding Issues

**This is the most important principle of this command.**

The AI has a tendency to soften or hide issues. This is UNACCEPTABLE. The report must be brutally honest:

### What Counts as a BLOCKER

- **ANY test failure** - Not a "minor issue", not "mostly passing", it's a BLOCKER
- **Environmental issues preventing tests from running** - Not "we couldn't verify due to environment", it's a BLOCKER
- **Lint failures** - Not "some style issues", it's a BLOCKER
- **Build failures** - Not "compilation warnings", it's a BLOCKER
- **Tests that couldn't execute** - Not "skipped due to setup", it's a BLOCKER

### Unacceptable Language

NEVER use phrases like:
- ❌ "Everything works, just a few test failures"
- ❌ "The important tests passed"
- ❌ "Minor environmental issues prevented some tests"
- ❌ "Tests mostly passed with some edge case failures"
- ❌ "Good enough for now"
- ❌ "Production ready despite..."
- ❌ "Non-critical failures"

### Required Mindset

- Tests should ALWAYS pass - 100% pass rate is the only acceptable outcome
- Tests should ALWAYS be able to run - any setup/environment issue is a bug
- If it's not all green, it's NOT MERGEABLE
- Partial success is failure
- Be transparent - show ALL issues prominently

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

  Review for: design adherence, over-engineering, AI slop, structural completeness."

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
  ANY failure = overall FAIL.
  If tests cannot run, that is also a FAIL.

  When reporting failures:
  - Clearly indicate if failures are in tests related to the scoped changed files
  - Prioritize failures in test files that cover the changed code
  - Still report ALL failures, but annotate which are in-scope vs out-of-scope"

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
  Report usability issues and friction points in THE SCOPED CHANGES ONLY."

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
  Report any coherence issues found IN THE SCOPED CHANGES."
```

**Important:** Replace `[Insert scope list here]` with the actual scope determined in step 1.

## Conditional Debug Analysis

**After the initial 4 agents complete**, check if cata-tester OR cata-ux-reviewer reported failures. If either failed:

```
# Agent 5: Debug Analysis (conditional)
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
  Focus on identifying WHY the failures occurred, especially in relation to the scoped changes."
```

Only launch this agent if there are actual failures to analyze. Skip if all tests passed and UX review found no critical issues.

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

## Verification Scope

**Scope Mode:** [staged / unstaged / branch / all / files / module]

**Files Verified:**
- src/auth/login.ts (modified, lines 45-67, 89-102)
- src/auth/middleware.ts (modified, lines 12-34)
- tests/auth/login.test.ts (added, entire file)

**Files Excluded:** All other files in codebase (not reviewed for this verification)

---

## Overall Verdict: ✅ PASS / ❌ FAIL / ⚠️ BLOCKED

**Status:** [MERGEABLE / NOT MERGEABLE]

---

## Test Results (cata-tester)

**Status:** ✅ ALL PASSED / ❌ FAILURES / ⚠️ COULD NOT RUN

[If failures or issues:]
⚠️ BLOCKER: [Exact issue - tests failed / tests couldn't run / etc.]

**Summary:**
- Total: X tests
- Passed: Y
- Failed: Z
- Skipped: W

**Failures:**
[List each failure with details]

---

## Code Review (cata-reviewer)

**Status:** ✅ APPROVED / ❌ ISSUES FOUND

**Critical Issues:** [Count]
**Major Issues:** [Count]
**Minor Issues:** [Count]

[Summary of findings]

---

## UX Review (cata-ux-reviewer)

**Status:** ✅ GOOD / ⚠️ ISSUES / ❌ CRITICAL / ⏭️ SKIPPED

[Summary of findings or reason for skip]

---

## Coherence Check (cata-coherence)

**Status:** ✅ COHERENT / ⚠️ ISSUES / ❌ MAJOR CONCERNS

**Reinvented Wheels:** [Count]
**Pattern Violations:** [Count]
**Stale AI Tooling:** [Count]
**Documentation Drift:** [Count]

[Summary of findings]

---

## Debug Analysis (cata-debugger)

**Status:** ✅ N/A (no failures) / 🔍 ANALYZED

[Only include this section if cata-debugger was launched]

**Root Cause Analysis:**
[Diagnostic findings from debugger]

**Investigation Summary:**
[What was investigated and discovered]

---

## Blockers

[List ALL blockers prominently - these prevent merging]

1. ❌ [Blocker 1]
2. ❌ [Blocker 2]

## Issues to Address

[List non-blocking issues that should still be fixed]

---

## Next Steps

[Clear guidance based on results]
- If PASS: "Changes verified. Ready for commit/merge."
- If FAIL: "Must fix blockers before proceeding. See issues above."
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
   - All 4 agents (or 3 if UX skipped) run simultaneously
   - **CRITICAL:** Include scope information in each agent prompt
   - Each agent receives the exact files and lines to focus on

6. **Collect results:**
   - Wait for all agents to complete
   - Gather outputs from each

7. **Launch debugger if failures:**
   - If cata-tester OR cata-ux-reviewer reported failures
   - Launch cata-debugger to analyze root cause
   - **Include scope context in debugger prompt**
   - Gather diagnostic output

8. **Generate unified report:**
   - **Add scope section at top** showing what was verified
   - Determine overall verdict
   - List ALL issues prominently
   - Include debug analysis if debugger ran
   - Make blockers impossible to miss
   - Clearly indicate what was IN scope vs excluded

9. **STOP and present:**
   - Display the report
   - Wait for human decision
   - DO NOT proceed to any next steps automatically

## Important Notes

- **Scope-aware verification** - Always detect and communicate scope to agents
- **Include scope in ALL agent prompts** - Critical for focused reviews
- **Run agents in parallel** - Use single message with multiple Task tool calls
- **Never auto-proceed** - Always stop after presenting report
- **Be honest** - Surface all issues, don't minimize or hide
- **Assume tests work** - Any test issue is a bug, not an excuse
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
