---
name: verify
description: >
  Run comprehensive triage-first verification pipeline with specialized agents.
  Detects scope, discovers toolchain, triages files to relevant agents, runs static
  analysis, launches review agents in parallel, exercises the app, and produces a
  unified report. Supports interactive, report-only, and auto-fix modes.
argument-hint: "[--mode=interactive|report-only|auto-fix] [--scope=staged|unstaged|branch|all] [--files=file1,file2] [--module=path] [--skip-ux] [--skip-security] [--auto-fix-threshold=N]"
---

# Verify Changes — Triage-First Pipeline

## Goal

Run comprehensive verification before considering changes complete. This skill detects what changed, triages files to relevant agents, runs static analysis, launches review agents in parallel, exercises the app end-to-end, and produces a unified report with actionable findings.

## Phase 0: Parse Arguments & Mode

Parse `$ARGUMENTS` for:

**Mode** (`--mode=`):
- `interactive` (default): Full pipeline → report → interactive triage → plan → fix
- `report-only`: Full pipeline → report → STOP
- `auto-fix`: Full pipeline → report → auto-accept severity >= threshold → plan → fix → STOP

**Scope Control:**
- `--scope=staged`: Verify only staged changes
- `--scope=unstaged`: Verify only unstaged modified files
- `--scope=branch`: Verify all changes in current branch vs base
- `--scope=all`: Verify entire codebase (comprehensive audit — skips triage, runs all agents on everything)
- `--files="file1,file2"`: Verify specific files only
- `--module=path`: Verify specific module/directory
- Default (no scope arg): Auto-detect from git state

**Other Options:**
- `--skip-ux`: Skip UX review for pure backend changes
- `--skip-security`: Skip security review (not recommended)
- `--auto-fix-threshold=N`: Minimum severity for auto-fix mode (default: 3)

## Phase 1: Scope Detection

Determine what files/changes to verify.

**1. Parse User-Specified Scope (if provided):**
- Check `$ARGUMENTS` for `--scope=`, `--files=`, or `--module=` flags
- If specified, use that exact scope
- Skip auto-detection

**2. Auto-Detect Scope (default behavior):**

Priority order:
1. **Staged changes exist?** → Scope to staged files only
2. **Unstaged changes exist?** → Scope to modified files only
3. **Branch has commits ahead of base?** → Scope to branch changes
4. **No changes detected?** → Report "nothing to verify" and STOP

**Git Commands for Scope Detection:**

```bash
# Check for staged changes
git diff --cached --name-only

# Check for unstaged changes
git diff --name-only

# Check for branch changes
BASE=$(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null)
git diff --name-only $BASE HEAD

# Get line ranges for changed files
git diff --cached -U0 -- <file>  # staged
git diff -U0 -- <file>           # unstaged
git diff -U0 $BASE HEAD -- <file> # branch
```

**3. Build Scope Context:**

Create a list of files in scope with status:
- `file.ts` (modified, lines 45-67, 89-102)
- `new-file.ts` (added, entire file)
- `old-file.ts` (deleted)

Store as `SCOPE_CONTEXT` for passing to agents.

Also build a machine-usable `SCOPE_METADATA` block for agents that need exact diff reconstruction:
- `scope_mode`: `staged`, `unstaged`, `branch`, `files`, `module`, `all`, or the resolved auto-detected mode
- `base_ref`: exact baseline ref/commit used for the scoped diff
- `compare_ref`: exact comparison target (`HEAD`, `INDEX`, `WORKTREE`, or explicit ref)
- `path_filter`: exact scoped paths, or `ALL_SCOPED_FILES`
- `diff_command`: exact git diff command used to define the scope
- `merge_base`: exact merge-base hash for branch scope, otherwise empty

`SCOPE_METADATA` is the source of truth for any agent that needs to reconstruct the selected diff.

**4. Format Scope for Agents:**

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

Example machine-readable metadata:
```text
SCOPE_METADATA:
- scope_mode: unstaged
- base_ref: INDEX
- compare_ref: WORKTREE
- path_filter: src/auth/login.ts,src/auth/middleware.ts
- diff_command: git diff -- src/auth/login.ts src/auth/middleware.ts
- merge_base:
```

## Phase 2: Load Engineer Skill

Check if the project has a pre-configured engineer skill:

```bash
ls .claude/skills/*-engineer/SKILL.md 2>/dev/null
```

**If found:**
- Read the engineer SKILL.md
- Read key reference files it points to (TESTING.md, architecture docs, etc.)
- Extract: test commands, build commands, linter commands, architecture notes
- Store as `ENGINEER_CONTEXT` — this is pre-verified knowledge from `/setup-engineer`
- The discovery phase (Phase 3) will validate these commands and only discover what's missing

**If not found:**
- `ENGINEER_CONTEXT` is empty
- The discovery phase will do full discovery from scratch

## Phase 3: Discovery & Triage

Launch ONE `Explore` agent (fast, read-only) with two jobs in a single prompt:

### Job A: Discover Project Toolchain

**If engineer skill exists:** Validate that the provided commands still work and discover anything missing:
```
The engineer skill provides these commands:
- Test: {test_command}
- Build: {build_command}
- Lint: {lint_commands}

Verify each command exists (which/type check). For any that fail, discover alternatives.
Discover any additional linters/type-checkers not covered by the engineer skill.
```

**If no engineer skill:** Full discovery:
```
Discover the project's toolchain:
- Test command (npm test, pytest, cargo test, go test, etc.)
- Build command (npm run build, cargo build, go build, etc.)
- Linter commands (eslint, pylint, clippy, golangci-lint, etc.)
- Type-checker commands (tsc --noEmit, mypy, etc.)

Check package.json scripts, Makefile targets, CI config, pyproject.toml, Cargo.toml, go.mod.
Output concrete commands that can be executed.
```

### Job B: Triage Changed Files

```
Read each changed file (not just the extension — look at actual content).
For each file, assign it to the agents whose review is most relevant:

Categories:
- CODE_REVIEW: Business logic, application code → cata-reviewer
- GENERAL_SECOND_OPINION: Entire scoped diff → cata-codex-reviewer
- SECURITY: Auth, crypto, input handling, data access → cata-security
- HARDENING: Input validation, error paths, state management → cata-hardener
- ARCHITECTURE: Module structure, dependencies, abstractions → cata-architect
- COHERENCE: Pattern adherence, existing utilities → cata-coherence
- QA: Test files or files that need test coverage assessment → cata-qa
- UX: UI components, CLI output, user-facing strings → cata-ux-reviewer
- TEST_EXECUTION: Any code change that could affect tests → cata-tester

A file can have multiple categories.

IMPORTANT: ALL agents always run — triage assigns files to focus each agent,
but never skips agents. Agents with no specifically assigned files review
the full scope (they may catch cross-cutting concerns).

Always assign the full scoped file list to `cata-codex-reviewer`. It is a general second-opinion pass, not a specialist router target.

Output a JSON-like mapping:
{
  "agent_assignments": {
    "cata-reviewer": ["src/auth.ts", "src/api/users.ts"],
    "cata-codex-reviewer": ["all scoped files"],
    "cata-security": ["src/auth.ts"],
    "cata-tester": ["all"],
    ...
  },
  "toolchain": {
    "test": "npm test",
    "build": "npm run build",
    "lint": ["npx eslint", "npx tsc --noEmit"]
  }
}
```

**If `--skip-ux` or `--skip-security`:** Those specific agents are skipped (explicit user override only).

**Output:** Store the agent assignments as `TRIAGE_RESULT` and toolchain commands as `TOOLCHAIN`.

## Phase 4: Static Analysis

Launch `cata-static` agent (haiku model) with:
- The scoped file list from Phase 1
- The linter/type-checker commands discovered in Phase 3

```
SCOPED FILES:
{scope file list}

COMMANDS TO RUN:
{each linter/type-checker command from TOOLCHAIN}

Run each command on the scoped files. Parse output into structured findings.
Report only findings in scoped files.
```

Wait for results. Store as `STATIC_SUMMARY`.

## Phase 5: Build Context Bundle

Assemble a compact context bundle (~50-100 lines) for review agents:

```
CONTEXT_BUNDLE:

VERIFICATION SCOPE:
{SCOPE_CONTEXT from Phase 1}

SCOPE METADATA:
{SCOPE_METADATA from Phase 1}

ENGINEER SKILL SUMMARY:
{Brief summary from ENGINEER_CONTEXT, or "No engineer skill found — toolchain discovered via exploration"}
{If engineer skill exists: "Reference files available at .claude/skills/{name}/ — read TESTING.md, ARCHITECTURE.md etc. for your domain"}

STATIC ANALYSIS SUMMARY:
{STATIC_SUMMARY from Phase 4 — just the findings table, not raw output}

TOOLCHAIN:
- Test: {command}
- Build: {command}
- Lint: {commands}

DIFF STAT:
{output of: git diff --stat [scope args]}
```

**Keep this compact.** Agents read files themselves — the bundle just tells them where to look and what's already known.

## Phase 6: Launch Review Agents (Parallel)

Launch ALL review agents in parallel using the Agent tool. Every agent runs every time — no agents are skipped based on triage (only explicit `--skip-ux` or `--skip-security` flags can exclude an agent).

**Model routing is handled by agent frontmatter:**
- opus: cata-reviewer, cata-security, cata-hardener, cata-coherence, cata-architect, cata-qa
- sonnet: cata-ux-reviewer, cata-codex-reviewer
- haiku: cata-tester

**Each agent prompt includes:**
1. The `CONTEXT_BUNDLE` from Phase 5
2. Per-agent file list from `TRIAGE_RESULT.agent_assignments`
3. Static findings relevant to their domain (e.g., security lint rules → cata-security)
4. Instruction to read engineer skill reference files for their domain if available
5. Agent-specific instructions (see templates below)

For `cata-codex-reviewer`, `SCOPE_METADATA` is authoritative. It must not infer scope mode from filenames or prose when exact metadata is available.

### Agent Prompt Templates

**For each agent, the prompt follows this structure:**

```
{CONTEXT_BUNDLE}

YOUR ASSIGNED FILES:
{files from TRIAGE_RESULT.agent_assignments for this agent}

RELEVANT STATIC FINDINGS:
{filtered findings from STATIC_SUMMARY relevant to this agent's domain}

{If engineer skill exists:}
ENGINEER SKILL REFERENCE:
Reference files are available at .claude/skills/{engineer-skill-name}/
Read files relevant to your domain (e.g., TESTING.md for cata-tester, architecture docs for cata-architect).

{Agent-specific instructions...}

OUTPUT FORMAT: For each issue found, provide:
- Title (short description)
- Severity (1-10, where 1=trivial, 10=critical)
- Location (file:line)
- Description (what the issue is and why it matters)
```

**Agent-specific instruction blocks:**

**cata-reviewer:**
```
Review for: design adherence, over-engineering, AI slop, structural completeness.
When checking completeness, verify changes in scope are complete (e.g., if route added, check if tests exist).
But do NOT audit the entire codebase for unrelated issues.
```

**cata-codex-reviewer:**
```
Run the local Codex CLI as an independent second-opinion reviewer.
Use `codex review` via Bash, not Claude's native analysis alone.
Use `SCOPE_METADATA` as the source of truth for scope reconstruction.
Adapt the verify scope into a temporary diff-only workspace under /tmp so Codex reviews only the intended changes.
Do NOT infer staged vs unstaged vs branch vs path-filtered scope from assigned files or prose if `SCOPE_METADATA` says otherwise.
If exact reconstruction from `SCOPE_METADATA` is not possible, report PATCH_CONSTRUCTION_FAILED instead of reviewing an approximate diff.
If Codex is unavailable (missing CLI, auth missing, network blocked, sandbox blocked), report BLOCKED status with a short factual reason.
If scope is `--scope=all`, report SKIPPED_UNSUPPORTED_SCOPE rather than attempting a whole-codebase audit.
Normalize Codex output into: title, severity, location, description.
```

**cata-tester:**
```
Run the full test suite using: {test command from TOOLCHAIN}
Report exact pass/fail counts.
If tests cannot run, report what prevented execution.
For EACH failure: title, severity, location, error message, and whether it's IN-SCOPE or OUT-OF-SCOPE.
```

**cata-ux-reviewer:**
```
ONLY test user-facing changes in the scoped files.
Do not audit the entire UI/CLI for issues.
Focus on the UX of what changed in this scope.
Test any UI, CLI output, error messages, or API responses that were modified.
```

**cata-coherence:**
```
Check if THESE specific changes follow codebase patterns.
Look for reinvented wheels in THIS change set.
Verify THIS change doesn't violate existing patterns.
Check documentation that relates to THESE changed files.
Focus on: 'Do these new changes fit well?'
```

**cata-architect:**
```
Analyze the ARCHITECTURAL IMPACT of these specific changes.
Check if changes degrade structural health (module boundaries, dependency direction, layering).
Look for abstraction opportunities (3+ duplications).
Check for god object growth in changed files.
Focus on: 'Do these changes maintain healthy architecture?'
```

**cata-security:**
```
ONLY flag security issues in code that was ADDED or MODIFIED.
First research how security is done in THIS codebase (auth, tenant isolation, validation).
Flag deviations from established security patterns.
Focus on: 'Does this new code introduce security vulnerabilities?'
```

**cata-hardener:**
```
Systematically check what happens with invalid/missing/extreme input.
Check if every failure mode gives feedback.
Compare validation across entry points.
Check for orphaned references and missing cascade behavior.
Focus on: 'What failure scenarios do these changes not handle?'
```

**cata-qa:**
```
Evaluate whether the scoped changes are adequately tested.
Assess test quality, mock usage, and test type appropriateness.
Adapt expectations to codebase testing maturity.
Focus on: 'Are these changes well-tested with good tests?'
```

## Phase 7: Collect Results + Conditional Agents

### 7a. Wait for all Phase 6 agents to complete

Collect structured findings from each agent. Extract ONLY:
- Title
- Severity (1-10)
- Location (file:line)
- Category (agent-specific)
- Description

**Discard investigation narratives.** Keep the orchestrator context lean.

For `cata-codex-reviewer`, also collect agent status if no findings were produced:
- `COMPLETED`
- `BLOCKED`
- `SKIPPED_UNSUPPORTED_SCOPE`

Blocked or skipped Codex runs are reported in the Agent Results Summary but do not abort verification.

### 7b. Conditional: cata-debugger

If cata-tester OR cata-ux-reviewer OR cata-exerciser reported failures (severity 7+):

Launch `cata-debugger` with:
```
VERIFICATION SCOPE CONTEXT:
{SCOPE_CONTEXT}

FAILURES TO INVESTIGATE:
{list of failures from tester/ux/exerciser}

Analyze the root cause of these failures.
Focus on failures caused by the scoped changes.
If failures are unrelated to scope, note that explicitly.
```

### 7c. Always: cata-exerciser with Issue Verification

Launch `cata-exerciser` (sonnet) with:
```
{CONTEXT_BUNDLE}

Exercise the changes end-to-end:
1. Read the engineer skill (.claude/skills/*-engineer/) if it exists — follow its instructions for starting the environment, authenticating, and interacting with services
2. Start the full local environment (app + all backing services)
3. Determine exercise strategy based on change type:
   - Frontend/UI changes → use Playwright to navigate and interact
   - API/backend changes → make actual API calls via curl, verify responses and data state
   - Data/search/indexing changes → trigger operations, query services via CLI tools to verify data was written/indexed
   - Job/worker changes → trigger jobs, verify side effects via database/service queries
   - Mixed → exercise through all affected interfaces
4. Verify data flows end-to-end — don't stop at "endpoint returns 200", follow data through the system
5. Report whether the specific changes actually work with real data

If you hit a barrier (can't start, need credentials, unclear what to test, no engineer skill for complex backend):
- Return BLOCKED status with specific reason
- If you cannot determine HOW to exercise the change, that is severity 9-10

ISSUES FOUND BY REVIEW AGENTS:
{List of all issues found in Phase 6 with VI-IDs, severity, title, location}

While exercising, attempt to trigger each reported issue and report verification status
(CONFIRMED / NOT REPRODUCED / NOT APPLICABLE / BLOCKED).
```

**Handle exerciser barriers:**
- If BLOCKED with `LOGIN_REQUIRED`, `UNCLEAR_FEATURE`, `NO_EXERCISE_STRATEGY`, `NO_ENGINEER_SKILL`, or `SERVICE_UNAVAILABLE` (interactive/auto-fix modes only):
  1. Use `AskUserQuestion` to get help from the user
  2. Re-launch cata-exerciser with the user's response
  3. If still blocked, record as final BLOCKED status
- In `report-only` mode: Record BLOCKED status in report without asking user

## Phase 8: Generate Unified Report

### 8a. Issue Deduplication

1. Collect all findings from each agent in structured format
2. Identify duplicates: same file/location, same root cause, same symptom from different angles
3. Merge into single issue: list all source agents, combine descriptions, use highest severity
4. Assign sequential VI-{n} IDs
5. Sort by severity descending

### 8b. Report Format

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

## Triage Summary

**Agents run:** cata-reviewer, cata-codex-reviewer, cata-tester, cata-security, cata-hardener, cata-architect, cata-coherence, cata-qa, cata-ux-reviewer, cata-exerciser
**Agents skipped:** [none, or list if --skip-ux/--skip-security was used]
**Static analysis:** ESLint (3 findings), tsc (1 finding)

---

## Agent Results Summary

| Agent | Status | Notes |
|-------|--------|-------|
| cata-static | Completed | 4 findings (3 warnings, 1 error) |
| cata-tester | X passed, Y failed | [brief note] |
| cata-reviewer | Completed | Found N items |
| cata-codex-reviewer | Completed / Blocked / Skipped | Found N items / [reason] |
| cata-ux-reviewer | Completed / Skipped | Found N items / [reason] |
| cata-coherence | Completed | Found N items |
| cata-architect | Completed | Found N items |
| cata-security | Completed / Skipped | Found N items / [reason] |
| cata-hardener | Completed | Found N items |
| cata-qa | Completed | Found N items |
| cata-exerciser | PASSED / FAILED / BLOCKED | [reason if blocked] |
| cata-debugger | Ran / N/A | [if applicable] |

---

## Issues Found

[Deduplicated issues from all agents, sorted by severity descending]

| ID | Sev | Title | Sources | Location | Description |
|----|-----|-------|---------|----------|-------------|
| VI-1 | 9 | [Short title] | tester, reviewer | file:line | [Combined description] |
| VI-2 | 7 | [Short title] | security | file:line | [Description] |

*Severity: 9-10 Critical | 7-8 High | 5-6 Moderate | 3-4 Low | 1-2 Trivial*
*Sources column shows which agents flagged the issue. Multiple sources = higher confidence.*

**Total: N issues from M agent findings (deduplicated)**

---

## Exerciser Verification

| Issue ID | Title | Exerciser Status | Notes |
|----------|-------|-----------------|-------|
| VI-1 | [title] | CONFIRMED | [observation] |
| VI-2 | [title] | NOT REPRODUCED | [what was tried] |
| VI-3 | [title] | NOT APPLICABLE | [reason] |
```

## Phase 9: Mode-Specific Post-Report

### Mode: `report-only`

Output the report and return control to the caller. Do not triage, plan, or fix anything.

- No user prompts — do not use `AskUserQuestion`
- Skip triage/fix phases entirely
- The report is the only output
- After outputting the report, the verify execution is complete — the caller continues its own flow

### Mode: `interactive` (default)

After presenting the report, run interactive triage:

**If zero issues found:** Output the report and return. No triage needed.

**Interactive Triage Process:**

1. Present ALL issues in batches of up to 4 using `AskUserQuestion`
2. Issues sorted by descending severity (most severe first)
3. For each issue: read source file, generate 2-3 specific fix proposals + Explain + Skip
4. Record user decisions

**AskUserQuestion Format (batch of up to 4):**

```
AskUserQuestion:
  questions:
    - header: "VI-1"
      question: "{Title} — {Description}. Found at {file:line} by: {sources} (severity {N})"
      multiSelect: false
      options:
        - label: "{Fix option 1}"
          description: "{Specific action with file:line reference}"
        - label: "{Fix option 2}"
          description: "{Alternative action with file:line reference}"
        - label: "Explain"
          description: "Get the full picture before deciding"
        - label: "Skip"
          description: "Accept this issue — will not fix in this change set"
```

**Handling "Explain":** Read surrounding code, re-present with richer context (alone, not batched). Keep all fix options. If Explain again, dig deeper.

**CRITICAL: Present EVERY issue.** Never skip issues. Only stop early if the user explicitly says "stop", "done", or "skip the rest".

5. After all issues triaged, show triage decision summary table
6. If fixes to apply:
   - Call `EnterPlanMode`
   - Read ALL affected files, analyze dependencies between fixes
   - Write implementation plan to plan file
   - Call `ExitPlanMode` for approval
7. Execute approved fixes in planned order
8. Show completion summary
9. Return control to caller — do not auto-re-run verify or commit

### Mode: `auto-fix`

After presenting the report:

1. Auto-accept all issues with severity >= `--auto-fix-threshold` (default: 3)
2. Skip issues below threshold (noted in summary but not acted on)
3. No user prompts — do not use `AskUserQuestion`
4. Enter plan mode, analyze fixes, write plan
5. Execute fixes
6. Show completion summary
7. Return control (do NOT stop — the caller continues)
8. Do NOT commit

## CRITICAL: No Hiding Issues

The report must be brutally honest:

- Tests should ALWAYS pass — 100% pass rate is the only acceptable outcome
- Tests should ALWAYS be able to run — any setup/environment issue is a bug
- Be transparent — show ALL issues prominently
- Report facts — let humans decide what to act on

### Severity Scale (1-10)

| Range | Impact | Examples |
|-------|--------|----------|
| 9-10 | Critical | Data loss, security vulnerability, cannot function |
| 7-8 | High | Major functionality broken, significant problems |
| 5-6 | Moderate | Clear issues, workarounds exist |
| 3-4 | Low | Minor issues, slight inconvenience |
| 1-2 | Trivial | Polish, cosmetic, optional improvements |

Severity reflects "how big is this issue?" — NOT "must you fix it?" The human decides what to act on.

## When to Skip UX Review

`cata-ux-reviewer` runs by default like all other agents. It can only be skipped via the explicit `--skip-ux` flag. Use `--skip-ux` when ALL are true:
- No changes to UI components, templates, or frontend code
- No changes to CLI output formatting or help text
- No changes to error messages or user-facing strings
- No changes to API response messages
- Pure backend, infrastructure, or internal refactoring only

When in doubt, don't use `--skip-ux` — let it run.

## Context Window Discipline

This is critical since verify runs in the main context window.

- **Orchestrator stays lean**: Parse args, run git commands, apply triage, launch agents, collect structured results, format report. No file reading beyond scope detection.
- **Agents do the heavy work**: Each agent has its own context window. They read files, grep, investigate.
- **Structured extraction only**: When collecting agent results, extract ONLY: title, severity, location, category, description. Discard investigation narratives.
- **No full file reads in orchestrator**: Never read source files except during the fix execution phase (interactive/auto-fix modes).
- **Compact context bundle**: Scope + static summary + diff stat. ~50-100 lines max.

## Execution Summary

1. Parse arguments and mode
2. Detect scope (git state → file list with line ranges)
3. Load engineer skill (if `.claude/skills/*-engineer/` exists)
4. Launch Explore agent for discovery + triage
5. Launch cata-static with discovered commands
6. Build compact context bundle
7. Launch review agents in parallel (per triage assignments)
8. Collect results, launch conditional agents (debugger if failures, exerciser always)
9. Generate unified report (dedupe, VI-IDs, severity sort, exerciser verification)
10. Mode-specific post-report (report-only → return, interactive → triage, auto-fix → auto-accept)

## Important Notes

- **All agents, every time**: Triage assigns files to focus each agent, but never skips agents — missed regressions cost more than the extra agent runs
- **Codex reviewer is best-effort**: It should surface an independent second-model review when local Codex is available, and show BLOCKED/SKIPPED status when it is not
- **Static analysis pre-step**: Linter findings feed into review agents for context
- **Engineer skill integration**: Pre-verified knowledge speeds up discovery
- **Exerciser verifies issues**: Reported issues get E2E verification status
- **Model routing via frontmatter**: Agent files specify their own model (opus/sonnet/haiku)
- **Scope-aware**: Always detect and communicate scope to agents
- **Run review agents in parallel**: Use single message with multiple Agent tool calls
- **Run exerciser after reviews**: Sequential — it needs the issue list
- **In interactive mode**: Do not auto-proceed to commit after fixes — return control to the caller
- **Be honest**: Surface all issues, don't minimize or hide
