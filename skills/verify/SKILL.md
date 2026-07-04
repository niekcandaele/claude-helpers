---
name: verify
description: >
  Run comprehensive triage-first verification pipeline with specialized skills.
  Detects scope, discovers toolchain, triages files to relevant skills, runs static
  analysis, invokes review skills in parallel, exercises the app, and produces a
  unified report. Supports interactive, report-only, and auto-fix modes.
argument-hint: "[--mode=interactive|report-only|auto-fix] [--scope=staged|unstaged|branch|all] [--files=file1,file2] [--module=path] [--skip-ux] [--skip-visual] [--auto-fix-threshold=N] [--format=markdown|json] [--output=<path>] [--plan-file=<path>]"
---

# Verify Changes — Triage-First Pipeline

## Goal

Run comprehensive verification before considering changes complete. This skill detects what changed, triages files to relevant skills, runs static analysis, invokes review skills in parallel, exercises the app end-to-end, and produces a unified report with actionable findings.

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
- `--skip-visual`: Skip visual review for changes the human has already eyeballed (e.g. copy-only). Visual review is also auto-skipped when `visual-verify` is not present in the available skills (defensive — it ships as a global skill; a project can override it with its own `.claude/skills/visual-verify/`).
- `--auto-fix-threshold=N`: Minimum severity for auto-fix mode (default: 3)
- `--plan-file=<path>`: Explicit path to a plan file for completeness checking. If not provided, discover the plan from context — check if a plan is visible in conversation history (e.g., invoked from player-coach which read a plan, or a plan was created/discussed earlier in this session). If a plan is found from either source, resolve its contents for the plan completeness check in Phase 6.

**Output Format:**
- `--format=`: `markdown` (default) or `json`. When `json`, the report is serialized as a JSON object conforming to the adversary CLI schema (see Phase 8c)
- `--output=<path>`: File path to write the JSON report to. Required when `--format=json`. The Write tool is used to write the file.

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

`SCOPE_METADATA` is the source of truth for any skill that needs to reconstruct the selected diff.

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
- Check for `VERIFICATION.md` in the same skill directory — if it exists, read it and store as `CUSTOM_GATES`
  - Extract **Exerciser Gates** → will be passed to exerciser in Phase 7c
  - Extract **Review Gates** → will be passed to review agents in Phase 5/6
- The discovery phase (Phase 3) will validate these commands and only discover what's missing

**If not found:**
- `ENGINEER_CONTEXT` is empty
- `CUSTOM_GATES` is empty
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
For each file, assign it to the skills whose review is most relevant:

Categories:
- REVIEWER: Business logic, application code, architecture, patterns, security, robustness → reviewer
- GENERAL_SECOND_OPINION: Entire scoped diff → codex-reviewer
- OVER_ENGINEERING: Entire scoped diff → ponytail-review
- COMMENT_HYGIENE: Entire scoped diff → comment-review
- QA: Test files or files that need test coverage assessment → qa
- UX: UI components, CLI output, user-facing strings → ux-reviewer
- VISUAL: UI-rendering files where the change affects what a user sees on the rendered page — components (.astro, .tsx, .vue, .svelte), pages, layouts, templates, CSS files, design tokens, public assets the page depends on for rendering. NOT JSON config, NOT server-side handlers without UI side effects, NOT pure copy strings handled by ux-reviewer. → visual-verify (only if `visual-verify` skill is present)
- TEST_EXECUTION: Any code change that could affect tests → tester

A file can have multiple categories.

IMPORTANT: ALL skills always run — triage assigns files to focus each skill,
but never skips skills. Skills with no specifically assigned files review
the full scope (they may catch cross-cutting concerns).

Always assign the full scoped file list to `codex-reviewer`. It is a general second-opinion pass, not a specialist router target.

Always assign the full scoped file list to `ponytail-review`. Complexity and reuse hunting needs breadth across the whole diff, not per-file routing.

Always assign the full scoped file list to `comment-review`. Ephemeral references and history comments can appear in any changed file.

Output a JSON-like mapping:
{
  "skill_assignments": {
    "reviewer": ["all scoped files"],
    "codex-reviewer": ["all scoped files"],
    "ponytail-review": ["all scoped files"],
    "comment-review": ["all scoped files"],
    "qa": ["test files and files needing test coverage"],
    "ux-reviewer": ["UI/CLI/user-facing files"],
    "visual-verify": ["UI-rendering files (components, pages, layouts, templates, CSS, design tokens, rendering-affecting public assets)"],
    "tester": ["all"],
  },
  "toolchain": {
    "test": "npm test",
    "build": "npm run build",
    "lint": ["npx eslint", "npx tsc --noEmit"]
  }
}
```

**If `--skip-ux`:** The UX reviewer skill is skipped (explicit user override only).
**If `--skip-visual`:** The visual-verify skill is skipped. Also auto-skipped when `visual-verify` is not present in the available skills (defensive; it is normally always present as a global skill).

**Output:** Store the skill assignments as `TRIAGE_RESULT` and toolchain commands as `TOOLCHAIN`.

## Phase 4: Static Analysis

Invoke `static-analysis` (haiku model) with:
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

Assemble a compact context bundle (~50-100 lines) for review skills:

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

CUSTOM REVIEW GATES:
{Review Gates from VERIFICATION.md, or "None defined"}
These are repo-maintainer-defined requirements. If any rule falls in your review domain,
report PASS/FAIL for it. Failed gates should be reported as severity 9 findings.

DIFF STAT:
{output of: git diff --stat [scope args]}
```

**Keep this compact.** Skills read files themselves — the bundle just tells them where to look and what's already known.

## Phase 6: Launch Review Skills (Parallel)

Invoke ALL review skills in parallel using the Skill tool. Every skill runs every time — no skills are skipped based on triage. Skips are explicit and limited:
- `--skip-ux` excludes `ux-reviewer`.
- `--skip-visual` excludes `visual-verify`.
- `visual-verify` is also auto-skipped if it is not present in the available skills list (defensive: it ships globally and is normally always present; a project may shadow it with its own `.claude/skills/visual-verify/` to customize capture conventions).

**Model routing is handled by skill frontmatter:**
- opus: reviewer (comprehensive review: design, architecture, coherence, hardening, security)
- sonnet: codex-reviewer, ponytail-review, comment-review, qa, ux-reviewer, exerciser, visual-verify
- haiku: tester, static-analysis

**Each skill prompt includes:**
1. The `CONTEXT_BUNDLE` from Phase 5
2. Per-skill file list from `TRIAGE_RESULT.skill_assignments`
3. Static findings relevant to their domain
4. Instruction to read engineer skill reference files for their domain if available
5. Skill-specific instructions (see templates below)

For `codex-reviewer`, `SCOPE_METADATA` is authoritative. It must not infer scope mode from filenames or prose when exact metadata is available.

### Skill Prompt Templates

**For each skill, the prompt follows this structure:**

```
{CONTEXT_BUNDLE}

YOUR ASSIGNED FILES:
{files from TRIAGE_RESULT.skill_assignments for this skill}

RELEVANT STATIC FINDINGS:
{filtered findings from STATIC_SUMMARY relevant to this skill's domain}

{If engineer skill exists:}
ENGINEER SKILL REFERENCE:
Reference files are available at .claude/skills/{engineer-skill-name}/
Read files relevant to your domain (e.g., TESTING.md for tester, architecture docs for reviewer).

{Skill-specific instructions...}

OUTPUT FORMAT: For each issue found, provide:
- Title (short description)
- Severity (1-10, where 1=trivial, 10=critical)
- Location (file:line)
- Description (what the issue is and why it matters)
```

**Skill-specific instruction blocks:**

**reviewer:**
```
Comprehensive review across all five dimensions:
1. Design & Code Quality: design adherence, over-engineering, AI slop, test integrity, structural completeness
2. Architecture: module boundaries, dependency direction, god objects, abstraction opportunities, coupling
3. Coherence: reinvented wheels, pattern violations, convention mismatches, documentation drift, dead code
4. Hardening: invalid inputs, error paths, inconsistent validation, orphaned references, state transitions
5. Security: injection, auth/authz, multi-tenant isolation, data exposure, crypto

Research the project's structure, patterns, and security approach BEFORE evaluating changes.
Focus on: 'Is this change well-designed, structurally sound, pattern-consistent, robust, and secure?'
```

**codex-reviewer:**
```
Run the local Codex CLI as an independent second-opinion reviewer.
Use `codex review` via Bash, not Claude's native analysis alone.
`codex review` is long-running: run it as a detached background command (no short Bash timeout) and poll for completion, honoring `CODEX_REVIEW_TIMEOUT` (default 30 min), so larger changes are not killed mid-review.
Use `SCOPE_METADATA` as the source of truth for scope reconstruction.
Adapt the verify scope into a temporary diff-only workspace under /tmp so Codex reviews only the intended changes.
Do NOT infer staged vs unstaged vs branch vs path-filtered scope from assigned files or prose if `SCOPE_METADATA` says otherwise.
If exact reconstruction from `SCOPE_METADATA` is not possible, report PATCH_CONSTRUCTION_FAILED instead of reviewing an approximate diff.
If Codex is unavailable (missing CLI, auth missing, network blocked, sandbox blocked), report BLOCKED status with a short factual reason.
If scope is `--scope=all`, report SKIPPED_UNSUPPORTED_SCOPE rather than attempting a whole-codebase audit.
Normalize Codex output into: title, severity, location, description.
```

**ponytail-review:**
```
Review the scoped diff for over-engineering ONLY: reinvented stdlib, unneeded
dependencies, speculative abstractions, dead flexibility, shrinkable logic.
Correctness, security, and performance are out of scope — other skills own those.
Verify each proposed replacement actually exists (grep for the codebase helper,
confirm the stdlib/native feature) before reporting it.
Normalize findings into: title, severity (cap 5), location, category (tag), description.
If nothing to cut, report COMPLETED with zero findings ("Lean already. Ship.").
```

**comment-review:**
```
Review ONLY comments and docstrings added or modified in the scoped diff
(plus pre-existing comments the changes make stale).
Flag: ephemeral review-ID references (VI-N, CI-N, "per review feedback"),
historical change-narration ("previously", "now we", "replaced X with Y"),
stale comments contradicting the code, reviewer-appeasement, and redundant restatement.
Comments must describe the current code and its intent — git owns history.
Code correctness, design, and prose docs are out of scope — other skills own those.
Normalize findings into: title, severity (floor 5, cap 6 — the floor is deliberate),
location, category (tag), description including a concrete rewrite (or "delete").
If comments are clean, report COMPLETED with zero findings.
```

**tester:**
```
Run the full test suite using: {test command from TOOLCHAIN}
Report exact pass/fail counts.
If tests cannot run, report what prevented execution.
For EACH failure: title, severity, location, error message, and whether it's IN-SCOPE or OUT-OF-SCOPE.
```

**ux-reviewer:**
```
ONLY test user-facing changes in the scoped files.
Do not audit the entire UI/CLI for issues.
Focus on the UX of what changed in this scope.
Test any UI, CLI output, error messages, or API responses that were modified.
```

**qa:**
```
Evaluate whether the scoped changes are adequately tested.
Assess test quality, mock usage, and test type appropriateness.
Adapt expectations to codebase testing maturity.
Focus on: 'Are these changes well-tested with good tests?'
```

**visual-verify:** *(only invoked if the skill is present in the available skills list and `--skip-visual` was not passed)*
```
Read the engineer skill for screenshot mechanics (wrapper command, dev URLs, viewport conventions) — typically VISUAL.md or the engineer SKILL.md.
For each UI-rendering file in YOUR ASSIGNED FILES, identify at least one route that renders it (grep imports for components; page files render directly).
Take screenshots at desktop (1440-wide, full-page) AND mobile (390-wide, full-page). If responsive sizing changed, sample boundary widths too.
Open every PNG with `Read` and apply the holistic articulation step described in the skill: write 2-3 sentences describing the composition in designer's terms (balance, weight, hierarchy, rhythm, alignment, density, color, typography). Anything in that paragraph that reads as a complaint becomes a finding.
Focus on: 'Would a designer ship this?' — not 'is anything imperfect?'
If no UI-rendering files in scope or no running app discoverable, return STATUS: SKIPPED with a one-line factual reason — same convention as codex-reviewer.
Output structured findings (Title / Severity / Location / Category / Description) per the skill's reviewer-mode protocol.
```

### Plan Completeness Check (Parallel, Conditional)

This check runs in parallel with the review skills above. It has no dependency on their output — it only needs the plan and the branch diff.

**If a plan was resolved** (via `--plan-file` flag or discovered from conversation context):

Invoke a general-purpose agent (sonnet) with:

```
PLAN FILE:
{plan file contents}

BRANCH DIFF:
{output of the diff command from SCOPE_METADATA, or `git diff {base}...HEAD`}

SCOPE CONTEXT:
{SCOPE_CONTEXT from Phase 1}

You are checking whether the implementation is complete relative to the plan.

Instructions:
- Identify all phases, sections, and steps described in the plan
- For each, determine whether the branch diff contains changes that implement it
- A phase is "addressed" if the diff contains changes that clearly correspond to its requirements
- If significant portions of the plan are unimplemented, emit a single finding:
  - Title: "Plan incomplete — only phase N of M implemented" (or similar descriptive summary)
  - Severity: 8
  - Description: List which phases/sections are implemented and which are missing, with brief reasoning
  - Sources: ["plan-completeness"]
  - Location: null (omit)
- If the plan appears fully implemented, emit NO finding (do not emit a success finding)

OUTPUT FORMAT: For each issue found, provide:
- Title (short description)
- Severity (1-10, where 1=trivial, 10=critical)
- Location (file:line or null)
- Description (what the issue is and why it matters)
```

**If no plan was resolved** (no flag, nothing in context): skip this check entirely, no finding emitted.

## Phase 7: Collect Results + Conditional Agents

### 7a. Wait for all Phase 6 skills to complete

Collect structured findings from each skill. Extract ONLY:
- Title
- Severity (1-10)
- Location (file:line)
- Category (skill-specific)
- Description

**Discard investigation narratives.** Keep the orchestrator context lean.

For `codex-reviewer`, also collect skill status if no findings were produced:
- `COMPLETED`
- `BLOCKED`
- `SKIPPED_UNSUPPORTED_SCOPE`

For `visual-verify`, also collect skill status if no findings were produced:
- `COMPLETED`
- `SKIPPED` with reason (`NO_UI_FILES_IN_SCOPE`, `NO_RUNNING_APP_DISCOVERABLE`, `NO_SCREENSHOT_MECHANISM`). SKIPPED is expected behavior, not a warning — it just means there was nothing visual in scope.

**Codex BLOCKED handling:** If `codex-reviewer` reports BLOCKED, this is a significant event — the independent second-model review did not run. Flag it prominently in the report:
- In `report-only` mode: Include BLOCKED status with high visibility in the Agent Results Summary and add a prominent warning after the summary table.
- In `interactive` mode: Use `AskUserQuestion` to ask: "Codex review was BLOCKED ({reason}). Continue without Codex review, or stop to resolve?"
- `SKIPPED_UNSUPPORTED_SCOPE` is expected for `--scope=all` and is not flagged as a warning.

### 7b. Conditional: debugger

If tester OR ux-reviewer OR exerciser reported failures (severity 7+):

Invoke `debugger` with:
```
VERIFICATION SCOPE CONTEXT:
{SCOPE_CONTEXT}

FAILURES TO INVESTIGATE:
{list of failures from tester/ux/exerciser}

Analyze the root cause of these failures.
Focus on failures caused by the scoped changes.
If failures are unrelated to scope, note that explicitly.
```

### 7c. Always: exerciser with issue verification

Invoke `exerciser` (sonnet) with:
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

ISSUES FOUND BY REVIEW SKILLS:
{List of all issues found in Phase 6 with VI-IDs, severity, title, location}

While exercising, attempt to trigger each reported issue and report verification status
(CONFIRMED / NOT REPRODUCED / NOT APPLICABLE / BLOCKED).

{If CUSTOM_GATES has exerciser gates:}
CUSTOM EXERCISER GATES:
{List of exerciser gates from VERIFICATION.md}

These are mandatory repo-maintainer-defined checks. After exercising the feature, you MUST
check each gate and report PASS/FAIL with evidence. Any failing gate means your overall
status cannot be PASSED — use FAILED instead.
```

**Handle exerciser barriers:**
- If BLOCKED with `LOGIN_REQUIRED`, `UNCLEAR_FEATURE`, `NO_EXERCISE_STRATEGY`, `NO_ENGINEER_SKILL`, or `SERVICE_UNAVAILABLE` (interactive/auto-fix modes only):
  1. Use `AskUserQuestion` to get help from the user
  2. Re-invoke exerciser with the user's response
  3. If still blocked, record as final BLOCKED status
- In `report-only` mode: Record BLOCKED status in report without asking user

## Phase 8: Generate Unified Report

### 8a. Issue Deduplication

1. Collect all findings from each skill in structured format (including any plan-completeness finding from Phase 6)
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

**Skills run:** reviewer, codex-reviewer, ponytail-review, comment-review, tester, qa, ux-reviewer, visual-verify, exerciser
**Skills skipped:** [none, or list if --skip-ux / --skip-visual was used, or if visual-verify was not present in available skills]
**Static analysis:** ESLint (3 findings), tsc (1 finding)

---

## Skill Results Summary

| Skill | Status | Notes |
|-------|--------|-------|
| static-analysis | Completed | 4 findings (3 warnings, 1 error) |
| tester | X passed, Y failed | [brief note] |
| reviewer | Completed | Found N items (design, arch, coherence, hardening, security) |
| codex-reviewer | Completed / **BLOCKED** / Skipped | Found N items / [reason] |
| ponytail-review | Completed | Found N items (net -N lines possible) / Lean already |
| comment-review | Completed | Found N items / Comments clean |
| qa | Completed | Found N items |
| ux-reviewer | Completed / Skipped | Found N items / [reason] |
| visual-verify | Completed / Skipped / Not Available | Found N items / [reason] |
| exerciser | PASSED / FAILED / BLOCKED | [reason if blocked] |
| plan-completeness | Complete / Incomplete / Skipped | [summary if incomplete, reason if skipped] |
| debugger | Ran / N/A | [if applicable] |

---

## Issues Found

[Deduplicated issues from all agents, sorted by severity descending]

| ID | Sev | Title | Sources | Location | Description |
|----|-----|-------|---------|----------|-------------|
| VI-1 | 9 | [Short title] | tester, reviewer | file:line | [Combined description] |
| VI-2 | 7 | [Short title] | security | file:line | [Description] |

*Severity: 9-10 Critical | 7-8 High | 5-6 Moderate | 3-4 Low | 1-2 Trivial*
*Sources column shows which agents flagged the issue. Multiple sources = higher confidence.*

**Total: N issues from M skill findings (deduplicated)**

---

## Exerciser Verification

| Issue ID | Title | Exerciser Status | Notes |
|----------|-------|-----------------|-------|
| VI-1 | [title] | CONFIRMED | [observation] |
| VI-2 | [title] | NOT REPRODUCED | [what was tried] |
| VI-3 | [title] | NOT APPLICABLE | [reason] |

---

## Custom Verification Gates

{If no VERIFICATION.md exists or no custom gates defined: omit this section entirely}

### Exerciser Gates
| # | Rule | Status | Evidence |
|---|------|--------|----------|
| 1 | [rule from VERIFICATION.md] | PASS / FAIL / BLOCKED | [from exerciser report] |

### Review Gates
| # | Rule | Status | Checked By | Evidence |
|---|------|--------|------------|----------|
| 1 | [rule from VERIFICATION.md] | PASS / FAIL / NOT CHECKED | [skill name] | [from skill findings] |

**Custom Gates: X/Y passed, Z blocked**
```

### 8c. JSON Output (`--format=json --output=<path>`)

When both `--format=json` and `--output=<path>` are set, build and write a JSON report file **after** generating the internal report data (8a/8b still run to produce the deduplicated issue list).

**Top-level schema:**

```json
{
  "schemaVersion": 1,
  "status": "ok | blocked | error",
  "findings": [ ... ],
  // ...plus all existing report fields preserved for backward compatibility
}
```

**Step 1 — Determine `status`:**

| Condition (checked in order) | `status` |
|------------------------------|----------|
| Verify itself crashed or could not execute at all (skill invocation failed, no files to analyze, internal error) | `"error"` |
| Verify cannot produce meaningful analysis (entire codebase fails to parse, no toolchain discovered, no skills could run) | `"blocked"` |
| Verify completed its pipeline (even if tests fail or build has errors) | `"ok"` |

**Important:** Build/typecheck errors and test failures are **not** terminal statuses. They are fixable problems that should be emitted as **findings** with severity 9-10, so that callers (e.g. the adversary loop) can pass them back to the implementer. `"blocked"` means verify itself cannot function, not that the code under test has problems.

**Step 2 — Build `findings` array:**

For each deduplicated issue from Phase 8a, create a finding object:

```json
{
  "title": "<issue title>",
  "severity": <number 1-10>,
  "description": "<issue description>",
  "sources": ["<skill1>", "<skill2>"],
  "location": { "path": "<file>", "line": <number> }
}
```

- `title`, `severity`, `description`, `sources` — copy directly from the issue
- `location` — parse the string format `"path/to/file.js:27-36"`: split on the **last** `:`, use everything before as `path`, parse the first number after `:` as `line`. If the string has no `:` followed by a number, omit `location` entirely
- `id` — drop, not included in findings

**Step 3 — Assemble full JSON object:**

Combine the adversary-required fields with existing report data:

```json
{
  "schemaVersion": 1,
  "status": "<mapped status>",
  "findings": [ <transformed findings> ],
  "overall": { "result": "<pass|issues-found>", "mode": "<scope mode>" },
  "scope": { "files": [...], "excluded": [...] },
  "triage": { "skills_run": [...], "skills_skipped": [...] },
  "skillResults": { ... },
  "issues": [ <original issues with id, string location, etc.> ],
  "exerciserVerification": [ ... ],
  "customGates": { ... }
}
```

The adversary reads only `schemaVersion`, `status`, and `findings`. All other fields are preserved for other consumers and debugging.

**Step 4 — Write file:**

Use the Write tool to write the JSON (pretty-printed with 2-space indent) to the `--output` path.

## Phase 9: Mode-Specific Post-Report

### Mode: `report-only`

Output the report and return control to the caller. Do not triage, plan, or fix anything.

- No user prompts — do not use `AskUserQuestion`
- Skip triage/fix phases entirely
- After outputting the report, the verify execution is complete — the caller continues its own flow

**If `--format=json` and `--output=<path>` are set:**
- Phase 8c already wrote the JSON file — the file IS the report
- Output a single confirmation line: `JSON report written to <path>` (no markdown report)
- Return control to the caller

**Otherwise (default markdown):**
- The markdown report is the only output

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

`ux-reviewer` runs by default like all other skills. It can only be skipped via the explicit `--skip-ux` flag. Use `--skip-ux` when ALL are true:
- No changes to UI components, templates, or frontend code
- No changes to CLI output formatting or help text
- No changes to error messages or user-facing strings
- No changes to API response messages
- Pure backend, infrastructure, or internal refactoring only

When in doubt, don't use `--skip-ux` — let it run.

## When to Skip Visual Review

`visual-verify` is a global skill (a project can override it by shipping its own `.claude/skills/visual-verify/`). It runs whenever:
1. The skill is present in the available skills list, AND
2. `--skip-visual` was not passed, AND
3. The triage assigns at least one UI-rendering file to it (it self-skips with `STATUS: SKIPPED` if not).

Use `--skip-visual` only when you have already eyeballed the rendered change in a browser and want to suppress the duplicate review (e.g. mid-session iteration where you ran `/visual-verify` manually 30 seconds ago). For copy-only changes that don't affect layout, the skill self-skips — you don't need the flag.

Visual review is the design-quality gate, not just a bug check — it asks "would a designer ship this?". Skipping it on UI work is the same kind of regret-generator as skipping mobile testing. When in doubt, don't pass `--skip-visual` — let it run.

## Context Window Discipline

This is critical since verify runs in the main context window.

- **Orchestrator stays lean**: Parse args, run git commands, apply triage, invoke skills, collect structured results, format report. No file reading beyond scope detection.
- **Skills do the heavy work**: Each helper skill has its own context window. They read files, grep, investigate.
- **Structured extraction only**: When collecting skill results, extract ONLY: title, severity, location, category, description. Discard investigation narratives.
- **No full file reads in orchestrator**: Never read source files except during the fix execution phase (interactive/auto-fix modes).
- **Compact context bundle**: Scope + static summary + diff stat. ~50-100 lines max.

## Execution Summary

1. Parse arguments and mode
2. Detect scope (git state → file list with line ranges)
3. Load engineer skill (if `.claude/skills/*-engineer/` exists)
4. Launch Explore for discovery + triage
5. Invoke static-analysis with discovered commands
6. Build compact context bundle
7. Invoke review skills in parallel (per triage assignments)
8. Collect results, invoke conditional skills (debugger if failures, exerciser always)
9. Generate unified report (dedupe, VI-IDs, severity sort, exerciser verification)
10. Mode-specific post-report (report-only → return, interactive → triage, auto-fix → auto-accept)

## Important Notes

- **All skills, every time**: Triage assigns files to focus each skill, but never skips skills — missed regressions cost more than the extra skill runs
- **Codex reviewer is a hard gate**: The independent second-model review is critical for catching blind spots. If Codex is BLOCKED, flag it prominently — the human must decide whether to proceed without it
- **Ponytail reviewer hunts complexity only**: over-engineering findings are quality debt (severity ≤5), never correctness — zero findings is the expected happy path
- **comment-review enforces a severity floor**: comment-hygiene findings are deliberately rated 5-6 so they clear the default fix threshold — do not re-rate them downward during dedup
- **Static analysis pre-step**: Linter findings feed into review skills for context
- **Engineer skill integration**: Pre-verified knowledge speeds up discovery
- **Exerciser verifies issues**: Reported issues get E2E verification status
- **Model routing via frontmatter**: Skill files specify their own model (opus/sonnet/haiku)
- **Scope-aware**: Always detect and communicate scope to agents
- **Run review skills in parallel**: Use single message with multiple Skill tool calls
- **Run exerciser after reviews**: Sequential — it needs the issue list
- **In interactive mode**: Do not auto-proceed to commit after fixes — return control to the caller
- **Be honest**: Surface all issues, don't minimize or hide
