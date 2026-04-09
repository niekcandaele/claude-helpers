---
name: root-cause-analysis
description: Root cause analysis — investigate directly in main context, then invoke a coach skill for adversarial review
argument-hint: [--max-turns=N] [--severity=N] [--context=skill-or-file] [problem description]
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - MultiEdit
  - Bash
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - AskUserQuestion
  - Skill
---

# Root Cause Analysis

You are the investigator conducting a root cause analysis. You gather evidence, test hypotheses, and write the report directly in this context window. After completing your investigation work each turn, you invoke a coach skill for independent adversarial review. You also manage the loop — applying the severity threshold to the coach's findings and deciding whether to loop.

There is one helper skill:
- **root-cause-coach** — reviews your report with fresh eyes, runs verification commands to spot-check your claims, pushes hard on gaps and shallow analysis

You investigate AND manage the loop. The coach reviews and pushes back. You never self-critique — that's the coach's job.

**Context continuity**: You retain full context between turns. Unlike the coach (which gets fresh context each turn), you accumulate evidence, hypotheses, and investigation state across the entire session. Do NOT re-read the report from scratch each turn — you wrote it and you remember what's in it. Only re-read specific sections if the coach challenged something specific.

## Core Investigation Behaviors

These behaviors are non-negotiable. They encode the difference between a shallow analysis that stops at "the app is slow" and a deep one that reaches "this specific function runs a redundant GROUP BY query 3000 times/min, consuming 40% of the database DTU budget."

### 1. Evidence access is non-negotiable

If you need data but can't access it, that's a blocker — not something to work around.

- **Transient failures** (timeout, connection reset, empty reply): retry up to 3 times with 5 seconds between attempts. If a port-forward or connection died, restart it and retry.
- **Persistent failures** (auth denied, resource not found, no access configured): STOP. Report to the human what you need and why. Do not continue investigating without the data.
- **NEVER** work around missing evidence by assuming what the data would show, using only partial data, or writing "to be verified later."

### 2. Every claim cites its evidence

Not "the DB was slow" but "wait stats showed LCK_M_U at 1.8ms/s, flat between normal and spike periods (query: `rate(mssql_wait_time_ms{wait_type="LCK_M_U"}[5m])` at 04:45 UTC)."

Include the exact query, command, or file:line reference so anyone can reproduce the finding. If you queried an API, show the curl command. If you read source code, cite file and line number.

### 3. Source code is plausible, not confirmed

Source code tells you what COULD happen. Runtime evidence (logs, metrics, traces, DB state) tells you what DID happen. You need both.

- Code trace alone → hypothesis is **plausible**
- Code trace + matching runtime evidence → **confirmed**
- Code trace + contradicting runtime evidence → **rejected**

Never declare root cause from source code analysis alone.

### 4. Go one layer deeper than your first answer

If you find "the app is slow" — that's a symptom, not a root cause. WHY is it slow?
If "DB locks" — what specific operation holds the lock? For how long? What data proves it?
If "resource exhaustion" — what operations consume the resources? Can they be optimized?

Keep going until you reach actionable code-level recommendations. "Increase resources" is not a root cause fix — it's a stopgap. The investigation must identify WHAT consumes the resources and WHETHER it can be made more efficient.

### 5. Use ALL available evidence sources

Don't stop at the first evidence source that gives you an answer. Cross-reference across layers:

- **Application logs** — what errors/warnings appear? What's the request flow?
- **Infrastructure events** — pod restarts, deployments, scaling events, probe failures
- **Distributed traces** — per-service timing, which hop is slow, what's the span tree?
- **Metrics** — DB wait stats, CPU/memory, request rates, queue depths, cloud provider resource metrics
- **Source code** — what does the code actually do? What locks, transactions, retries exist?
- **Database-level metrics** — blocked sessions, running queries, connection pool, per-database resource consumption

Each layer reveals something the others miss. Logs show what happened. Metrics show how much. Traces show where. Source code shows why. DB metrics show whether the database is actually the bottleneck or just a bystander.

### 6. Generate charts for quantitative findings

Every time series comparison, before/after measurement, or distribution analysis deserves a chart. Charts are generated from real queried data, never hardcoded values. If a chart generation script is available in the environment, use it. Otherwise, use matplotlib or similar via `uv run --with matplotlib`.

Chart titles describe findings, not metrics: "P95 dropped from 120s to 270ms after index migration" not "Response Time."

### 7. Scrub sensitive data from all report content

Investigation evidence often contains secrets and personally identifiable information. RCA reports get shared with teams, stakeholders, and sometimes end up in post-mortem archives — any sensitive data in the report becomes a leak.

Before writing evidence into the report or worklog, redact:
- **Credentials**: passwords, API keys, tokens, secrets, private keys
- **Connection strings**: mask embedded usernames and passwords (e.g., `postgres://[REDACTED]@db-host:5432/mydb`)
- **PII**: email addresses, phone numbers, and personal names that aren't essential to understanding the issue
- **Internal identifiers**: customer IDs, account numbers, or tenant-specific data when not directly relevant to the root cause

Use descriptive placeholders so the evidence remains useful: `[REDACTED-API-KEY]`, `[REDACTED-PASSWORD]`, `[REDACTED-EMAIL]`. Keep the structure around the redacted value — a reader should still understand the query pattern, the config shape, or the log format.

## Report Structure

Create and maintain a markdown report with this structure:

```markdown
# [Issue Title]

## Background
[Who reported, when, what system, what changed recently]

## Symptoms
[Numbered list of observable problems]

## Request/Data Flow
[ASCII diagram showing the path from trigger to outcome]

## Root Cause
> [!success] Root cause — N contributing factors
> [3 bullets max. Concise. Details go in the Issue sections below.]

## Issue 1: [title]
[Detailed analysis with inline charts. Evidence citations. Source code references.]

## Issue N: ...

## Evidence Summary
| # | What was checked | Result | Verify |
[Every evidence claim with the exact query/link to reproduce]

## Recommended Fix Path
### Immediate
### Proper fix
### Nice-to-have

## Anticipated Questions
[3-6 questions a reader would ask, with concise answers]

## Hypotheses
### H1: [name] (status: confirmed/rejected/untested)
[Rationale, evidence, conclusion]

## Investigation Trail
[Wrong theories documented so others don't repeat them]

## Source Code References
| What | File | Lines |

## Environment
| Item | Value |
```

Plus a separate **worklog** file with timestamped raw evidence (commands, outputs, interpretations).

## Phase 0: Setup and Evidence Access Discovery

### 1. Parse arguments

Check `$ARGUMENTS` for:
- `--max-turns=N` — maximum investigation iterations
- `--severity=N` — minimum severity for coach findings that require re-investigation
- `--context=<skill-or-file>` — environment-specific skill or file with access instructions
- Everything else → the problem description

### 2. Clarify with the user

Use `AskUserQuestion` to fill in anything not specified. Only ask what's genuinely needed.

**Always ask (if not in arguments), using these exact options:**

- **Max turns:**
  - `5` — focused (straightforward issues, limited scope)
  - `8` — standard (typical production investigation) **[default]**
  - `12` — thorough (complex multi-service issues, deep performance analysis)

- **Severity threshold:**
  - `5` — strict (coach pushes hard on every gap)
  - `7` — moderate (meaningful issues only) **[default]**
  - `9` — lenient (only critical depth/evidence issues)

**Ask only if unclear:**
- What system/service is affected?
- What time window should the investigation focus on?
- Where should the report be written? (default: current directory)

### 3. Evidence access discovery

Before investigating, discover what evidence sources are available:

1. If a `--context` skill or file was provided, read it to learn how to access evidence
2. Discover available evidence sources:
   - Check for project skills (`find .claude/skills -name "SKILL.md" 2>/dev/null`)
   - Check for CLAUDE.md with access instructions
   - Check what MCP tools are available
   - Check for observability access (can you reach log/metric/trace APIs?)
   - Check for source code access (are the relevant repos available?)
   - Check for database access (any DB connection tools or credentials?)
3. For each discovered source, do a quick sanity check (simple query, ls, or ping)
4. Build an EVIDENCE ACCESS INVENTORY listing each source, its status (accessible/inaccessible/not configured), and what it could provide for this investigation

### 4. Present access inventory to user

Show the inventory. If critical sources are missing, ask the human:

> "The investigation needs access to [X] to check [Y]. Can you provide instructions for how to access it, or should we proceed without it?"

Only proceed to Phase 1 when: you have sufficient evidence access, OR the human explicitly says to proceed with what's available.

### 5. Confirm and start

> "Starting investigation: [max_turns] turns, severity threshold [N]. Problem: [1-line summary]. Evidence access: [list of accessible sources]."

## Phase 1: Investigation Loop

```
Initialize:
  turn = 0
  feedback = ""
  feedback_history = []
  sticky_issues = {}        # RC-IDs that reappear across turns
  report_path = ""          # Set after turn 1
  worklog_path = ""         # Set after turn 1
```

### Each turn (1 to max_turns):

#### Step 1: Investigate

**Turn 1 — Initial investigation:**

1. Understand the problem statement
2. Map the request/data flow (trace the path hop by hop)
3. Survey available evidence sources (sanity-check each with a simple query)
4. Generate initial hypotheses (3-5, numbered, each with rationale and what evidence would confirm/reject)
5. Start testing hypotheses — highest-likelihood first
6. Create the report file and worklog file
7. Write initial findings into the report

**Turn 2+ — Address coach feedback:**

1. Read ALL coach findings from the previous turn, sorted by severity
2. For each finding at or above the severity threshold:
   - If "go deeper": gather the next layer of evidence
   - If "missing evidence": run the query/command that proves the claim
   - If "source code only": find runtime evidence that confirms or contradicts
   - If "evidence contradicts claim": re-examine the conclusion, gather fresh evidence
   - If "lazy fix": identify the actual mechanism and propose a code-level change
   - If "chart needed": query the data and generate the visualization
3. Update the report with new findings
4. Update the worklog with raw evidence

At the end of each investigation step, produce a structured summary:

```
INVESTIGATION SUMMARY
Turn: N

Evidence gathered this turn:
- [source]: [what was checked] → [finding]

Hypotheses updated:
- H1: [status change and why]

Report updated:
- [sections modified and why]

Remaining gaps:
- [what still needs checking]

Access blockers:
- [any evidence sources that couldn't be accessed — NONE if all accessible]
```

#### Step 2: Prepare Verification Shortcuts

After completing investigation work, compile a block of verification shortcuts the coach can use to spot-check your claims. These are commands YOU already ran during investigation — the coach can re-run them instantly without figuring out evidence access.

Build this from the Evidence Summary table in your report. Include 8-12 shortcuts targeting the most important claims — the ones your root cause conclusion depends on.

Format:

```
VERIFICATION SHORTCUTS

Evidence claim: "[claim from report]"
Verify with: `[exact command, query, or file:line reference]`
Expected result: [what the output should show]

Evidence claim: "[next claim]"
Verify with: `[command]`
Expected result: [expected output]

...

Key files to review:
- [file:lines] — [what this shows]
```

#### Step 3: Invoke Coach

Use the Skill tool to invoke `root-cause-coach`:

```
You are the Coach reviewing a root cause analysis report. Push hard on gaps, shallow analysis, and unsupported claims.

Report: {report_path}
Worklog: {worklog_path}
Severity threshold: {severity}
Turn: {turn} of {max_turns}

VERIFICATION SHORTCUTS:
{verification_shortcuts}

{if turn > 1}
Previous coach feedback that was addressed this turn:
{previous_feedback}
{endif}

Produce severity-scored findings (RC-N format). Focus on:
- Claims without evidence
- Shallow analysis that stops at symptoms
- Available evidence sources that weren't used
- Fix recommendations that are just "increase resources"
- Missing charts for quantitative findings
- Run verification shortcuts and check if results match the report's claims
```

#### Step 4: Decision Gate

This is mechanical — no judgment.

1. **Parse coach output** — extract all RC-N findings with severity scores. If the coach output contains no RC-N findings (or explicitly says "Report approved"), the finding count is zero.
2. **Track sticky issues** — compare this turn's findings against previous turns by content. Same topic/section reappearing = sticky. Record turn numbers.
3. **Apply threshold:**
   - **Zero findings at/above severity threshold** → **APPROVED**. Proceed to Phase 2.
   - **N findings at/above threshold** → **FEEDBACK**. Collect findings, append to feedback_history, loop to next turn.
4. **Check for stuck state:**
   - If a sticky issue has appeared 3+ turns in a row, ask the human for guidance
   - If you have access blockers, ask the human for access

#### Output each turn:

```
## Turn {turn}/{max_turns}

Investigation: {1-line summary of what was done}
Coach: {N} findings ({M} at/above severity {threshold})
Decision: {APPROVED or FEEDBACK}

{if FEEDBACK}
Top findings to address:
- RC-1 (sev X): {summary}
- RC-2 (sev Y): {summary}
{endif}
```

## Phase 2: Finalization

### 1. Final polish

Do a final polish pass on the report:
1. Ensure all charts are generated and embedded inline
2. Ensure all evidence in the summary table has a reproducible query or command
3. Write the Anticipated Questions section (3-6 questions a fresh reader would ask)
4. Ensure the Investigation Trail documents wrong theories
5. Verify the Root Cause section is concise (3 bullets max, details in Issue sections)

### 2. Final coach review (lower threshold)

Spawn the coach one more time with severity threshold lowered by 2 (to catch clarity issues):

```
This is the FINAL CLARITY REVIEW. The report was previously approved at severity {threshold}.
Now review at severity {threshold - 2} — catch remaining clarity, formatting, and readability issues.
Only produce findings that would genuinely confuse a reader. Do not nitpick.

Report: {report_path}
Worklog: {worklog_path}

VERIFICATION SHORTCUTS: None — this is a clarity-only review. Skip Step 2 (Run Verification Shortcuts).
Focus exclusively on comprehensibility and clarity (Steps 1 and 4 of your review process).
```

If any findings remain, present them to the human as optional improvements — do NOT loop again.

### 3. Output completion

```
# Root Cause Analysis Complete

## Result: APPROVED (Turn {N} of {M})
## Severity threshold: {threshold}

## Report: {report_path}
## Worklog: {worklog_path}

## Turn History
| Turn | Investigation Summary | Coach Findings | Decision |
|------|----------------------|----------------|----------|
{turn_history}

{if sticky_issues}
## Friction Areas
{Issues that took multiple turns to resolve}
{endif}

{if optional_clarity_findings}
## Optional Improvements (from final clarity review)
{findings}
{endif}
```

## Turn Limit Reached

If `turn > max_turns` and the coach hasn't approved:

```
# Root Cause Analysis: Turn Limit Reached

## Result: NOT APPROVED after {M} turns
## Severity threshold: {threshold}

## Report: {report_path} (partial — review before sharing)

## Remaining Issues
{Last coach findings}

## Recommendation
The investigation needs more depth in these areas. Consider:
- Re-running with higher max-turns
- Providing additional evidence access
- Narrowing the investigation scope
```
