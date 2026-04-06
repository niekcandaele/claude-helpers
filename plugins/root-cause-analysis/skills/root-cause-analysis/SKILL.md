---
name: root-cause-analysis
description: >
  Root cause investigation with adversarial coach review. Investigates directly in the main
  context, spawns a coach to spot-check evidence and push for depth. Produces grounded reports
  with charts, citations, and actionable fixes. Use for bugs, outages, performance issues,
  post-mortems, or any "why is this broken" question.
argument-hint: "[--max-turns=N] [--severity=N] [--context=skill-or-file] [problem description]"
---

# Root Cause Analysis

A structured investigation loop that produces grounded, evidence-based root cause reports. The investigation runs directly in the main context window for full evidence continuity, then spawns an adversarial coach agent with fresh eyes to review the report and push back on gaps — until the report meets quality standards.

## Quick Start

```
/root-cause-analysis "throughput dropping on production cluster since 11am"
/root-cause-analysis --context=my-project:operations "API latency spike affecting tenant X"
/root-cause-analysis --max-turns=12 --severity=5 "database deadlocks during batch processing"
```

## How It Works

### Phase 0: Evidence Access Discovery

Before investigating, the system surveys what evidence is available:
- Observability APIs (logs, metrics, traces)
- Source code repositories
- Database access
- Cloud provider metrics
- Project-specific skills or MCP servers

If critical evidence sources are inaccessible, it stops and asks for help rather than producing a half-grounded report.

### Phase 1: Investigation Loop

Each turn:
1. **Investigate** directly in the main context — gather evidence, test hypotheses, update the report. The main context retains full investigation history across turns, so no evidence is lost and no re-orientation is needed.
2. **Prepare verification shortcuts** — compile pre-baked commands the coach can run to quickly spot-check key claims.
3. **Coach** reviews the report with completely fresh eyes, runs verification commands, and produces severity-scored findings. The coach gets fresh context each turn, ensuring an unbiased adversarial perspective.
4. **Decision gate** — findings above threshold mean loop; none above threshold means approved.

### Phase 2: Finalization

After approval: charts generated, evidence links verified, anticipated questions written, final clarity review by the coach at a lower threshold.

## Environment Access

The skill itself is environment-agnostic. It knows HOW to investigate but not WHERE your evidence lives.

Provide environment-specific access via `--context`:

- **A project skill**: `--context=my-engineering:operations` (provides cluster access, query patterns, etc.)
- **A CLAUDE.md file**: `--context=~/code/my-project/CLAUDE.md` (contains observability patterns)
- **Omit it**: The investigator will discover available skills, MCP servers, and CLAUDE.md files automatically, and ask for help if it can't find what it needs

## What Makes a Good Report

The loop is designed to produce reports that a senior engineer who wasn't part of the investigation can read and understand. Key quality properties:

### Evidence-grounded
Every claim cites its source — the exact query, command, or code reference. A reader can click a link or run a command to independently verify any finding.

### Deep, not shallow
"The app is slow" is a symptom. "Function X runs a redundant GROUP BY query 3000 times/min, consuming 40% of the database budget" is a root cause. The coach pushes until the report reaches actionable depth.

### Verified by an adversary
The coach doesn't just check that evidence is cited — it actually runs verification commands to confirm that the evidence matches the report's claims. Claims that don't hold up under spot-checking get flagged.

### Honest about what it doesn't know
If evidence was inaccessible, the report says so. If a hypothesis couldn't be fully verified, it's marked as plausible, not confirmed. Wrong theories are documented in the Investigation Trail so others don't repeat them.

### Scrubbed of sensitive data
Passwords, API keys, tokens, PII, and connection strings are redacted before they enter the report. Evidence keeps its structure (query patterns, config shapes, log formats) but credentials and personal data are replaced with descriptive `[REDACTED-*]` placeholders. The coach flags any sensitive data that slips through as severity 9-10.

### Actionable
Fix recommendations include code-level changes, not just "increase resources." The report explains the mechanism so developers know exactly what to change and why.

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--max-turns` | 8 | Maximum investigation iterations |
| `--severity` | 7 | Minimum coach finding severity to require re-investigation (1-10) |
| `--context` | auto-discover | Skill name or file path with environment access instructions |

## Coach Severity Scale

| Range | Category | Example |
|-------|----------|---------|
| 8-10 | **Depth** | Stopped at symptom, didn't explain why; available evidence not used |
| 7-9 | **Evidence** | Claim without data; source code without runtime verification; verification command contradicts report |
| 5-7 | **Completeness** | Untested hypotheses; infrastructure-only fixes |
| 3-5 | **Clarity** | Overloaded sections; jargon without context; bad chart titles |

## Evidence Retry Policy

Transient failures (timeouts, connection resets) are retried 3 times. Persistent failures (auth denied, not found) are blockers — the investigation pauses and asks the human for access. The system never works around missing evidence by guessing or writing "to be verified later."
