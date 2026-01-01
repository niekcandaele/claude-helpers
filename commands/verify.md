# Verify Changes

## Goal

Run comprehensive verification before considering changes complete. This command launches multiple specialized agents in parallel to review code quality, run tests, and validate user experience.

## Input

Optional scope: $ARGUMENTS (e.g., `--skip-ux` to skip UX review for pure backend changes)

## Process

1. **Analyze Changes:** Run `git diff` to understand what changed
2. **Launch Verification Agents IN PARALLEL:**
   - `cata-reviewer`: Code review for design adherence, over-engineering, AI slop
   - `cata-tester`: Execute test suite and report failures
   - `cata-ux-reviewer`: Test user-facing changes (unless `--skip-ux` or clearly backend-only)
   - `cata-coherence`: Check if changes fit in the codebase (reinvented wheels, pattern violations, stale docs/AI tooling)
3. **Generate Unified Report:** Combine all agent findings with clear verdict
4. **STOP:** Present report and wait for human decision

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

Launch all agents in a single message using the Task tool:

```
# Agent 1: Code Review
Task tool with:
- subagent_type: "cata-reviewer"
- description: "Review code changes"
- prompt: "Review the changes in this repository.
  Use git diff to see what changed.
  Check for design adherence, over-engineering, AI slop.
  Provide detailed code review."

# Agent 2: Test Execution
Task tool with:
- subagent_type: "cata-tester"
- description: "Run test suite"
- prompt: "Run the test suite for this repository.
  First discover the test framework:
  - Check package.json for test scripts
  - Check for pytest, cargo test, go test, etc.
  Execute the full test suite.
  Report exact pass/fail counts.
  ANY failure = overall FAIL.
  If tests cannot run, that is also a FAIL."

# Agent 3: UX Review (unless skipped)
Task tool with:
- subagent_type: "cata-ux-reviewer"
- description: "Review user-facing changes"
- prompt: "Review user experience for changes in this repository.
  Use git diff to identify user-facing changes.
  Test any UI, CLI output, error messages, or API responses.
  Report usability issues and friction points."

# Agent 4: Coherence Check
Task tool with:
- subagent_type: "cata-coherence"
- description: "Check if changes fit in codebase"
- prompt: "Check if these changes fit in the codebase.
  Research existing patterns, utilities, and conventions.
  Look for reinvented wheels - utilities that already exist.
  Check for pattern violations - different approaches than rest of codebase.
  Verify AI tooling (.claude/) matches actual behavior.
  Check if documentation reflects current code.
  Report any coherence issues found."
```

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

1. **Check for changes:**
   ```bash
   git status
   git diff --stat
   ```

2. **Determine if UX review needed:**
   - Parse `$ARGUMENTS` for `--skip-ux` flag
   - If not explicitly skipped, analyze changed files
   - Look for UI/frontend/CLI/message changes
   - Default to INCLUDING UX review

3. **Launch agents in parallel:**
   - Use Task tool with multiple tool calls in single message
   - All 4 agents (or 3 if UX skipped) run simultaneously

4. **Collect results:**
   - Wait for all agents to complete
   - Gather outputs from each

5. **Generate unified report:**
   - Determine overall verdict
   - List ALL issues prominently
   - Make blockers impossible to miss

6. **STOP and present:**
   - Display the report
   - Wait for human decision
   - DO NOT proceed to any next steps automatically

## Important Notes

- **Run agents in parallel** - Use single message with multiple Task tool calls
- **Never auto-proceed** - Always stop after presenting report
- **Be honest** - Surface all issues, don't minimize or hide
- **Assume tests work** - Any test issue is a bug, not an excuse
- **Default to more verification** - When in doubt, run more agents

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
