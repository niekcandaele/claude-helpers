---
name: root-cause-analysis
description: >
  Conducts structured root cause investigations for production issues using an adversarial
  investigation loop. An investigator agent gathers evidence from logs, metrics, traces, and
  source code while a critic agent pushes for depth and rigor. Produces a grounded investigation
  report with charts, evidence citations, and actionable fix recommendations.
  Use when investigating bugs, outages, performance degradation, or any production issue that
  needs systematic analysis. Also use when the user mentions "root cause", "investigate",
  "why is this slow", "what caused the outage", "post-mortem", or "incident analysis".
argument-hint: "[--max-turns=N] [--severity=N] [--context=skill-or-file] [problem description]"
---

# Root Cause Analysis

An adversarial investigation loop that produces grounded, evidence-based root cause reports. The loop runs an investigator agent (evidence gathering, hypothesis testing, report writing) against a critic agent (depth, evidence grounding, completeness, clarity) until the report meets quality standards.

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
1. **Investigator** gathers evidence, tests hypotheses, updates the report
2. **Critic** reviews the report and produces severity-scored findings
3. **Orchestrator** decides: findings above threshold → loop; none → approved

The investigator gets fresh context each turn (no accumulated hallucination). The critic is read-only (never modifies files).

### Phase 2: Finalization

After approval: charts generated, evidence links verified, anticipated questions written, final clarity review.

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
"The app is slow" is a symptom. "Function X runs a redundant GROUP BY query 3000 times/min, consuming 40% of the database budget" is a root cause. The critic pushes until the report reaches actionable depth.

### Honest about what it doesn't know
If evidence was inaccessible, the report says so. If a hypothesis couldn't be fully verified, it's marked as plausible, not confirmed. Wrong theories are documented in the Investigation Trail so others don't repeat them.

### Actionable
Fix recommendations include code-level changes, not just "increase resources." The report explains the mechanism so developers know exactly what to change and why.

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--max-turns` | 8 | Maximum investigation iterations |
| `--severity` | 7 | Minimum critic finding severity to require re-investigation (1-10) |
| `--context` | auto-discover | Skill name or file path with environment access instructions |

## Critic Severity Scale

| Range | Category | Example |
|-------|----------|---------|
| 8-10 | **Depth** | Stopped at symptom, didn't explain why; available evidence not used |
| 7-9 | **Evidence** | Claim without data; source code without runtime verification |
| 5-7 | **Completeness** | Untested hypotheses; infrastructure-only fixes |
| 3-5 | **Clarity** | Overloaded sections; jargon without context; bad chart titles |

## Evidence Retry Policy

Transient failures (timeouts, connection resets) are retried 3 times. Persistent failures (auth denied, not found) are blockers — the investigation pauses and asks the human for access. The system never works around missing evidence by guessing or writing "to be verified later."
