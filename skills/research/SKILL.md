---
name: research
description: >
  Multi-source research specialist that investigates a topic, verifies claims
  across independent sources, and reports findings with dated citations. Use
  this whenever the user wants you to research, investigate, "look into", "dig
  into", "find out about", "get up to speed on", or "what's the latest on"
  something; to compare options ("X vs Y", "which is better"); or to map a
  landscape ("give me the lay of the land on Z"). Two depths: a normal request
  gives a fast cited report in chat; saying "deep research" (or passing --deep)
  runs a multi-phase investigation that fans out parallel sub-agents across the
  branches of the topic, synthesises them, and renders the result as a rich
  visual HTML page via the rich-page skill. Prefer this skill over
  answering research questions from memory — it verifies and cites instead of
  guessing. Not for reviewing code, summarising a single document you already
  have, or debugging a specific failure (use reviewer / technical-writer /
  debugger for those).
argument-hint: "[--deep] [topic or research question]"
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - WebSearch
  - WebFetch
  - Agent
  - Skill
  - Write
  - AskUserQuestion
---

# research

Investigate a topic properly: gather from multiple independent sources, verify claims, separate fact from opinion, and report with dated citations. The standards that govern *how* you research and report live in `references/methodology.md` — read it before you start, and point every sub-agent at it so all the work comes back in the same shape.

This skill has **two depths**. Pick the depth, then follow that workflow.

## Choosing the depth

**Deep mode** when the user says "deep research", "deep dive", "go deep", "thorough/exhaustive research", or passes `--deep`. Deep mode fans out parallel sub-agents and always produces both a saved markdown report and an interactive HTML page.

**Standard mode** otherwise — a single focused investigation answered in chat. This is the default for "research X", "look into Y", "what's the latest on Z".

If the topic is plainly huge ("research the entire history of distributed databases") but the user didn't say "deep", do standard mode but mention deep mode exists: *"This is broad — I did a focused pass; say 'deep research' if you want the full fan-out + interactive page."* Don't silently escalate; the fan-out is expensive and the user should opt in.

---

## Standard workflow

1. **Scope.** Restate what you're answering in a sentence. If the request is genuinely ambiguous (could mean two different things), ask one quick clarifying question — otherwise just proceed; don't interrogate the user before simple research.
2. **Investigate.** Run targeted searches following `references/methodology.md`: official docs first, cross-reference important claims across independent sources, prefer recent sources where recency matters, and actively look for contradicting evidence.
3. **Report in chat.** Write the cited report directly in the conversation using the structure in `references/methodology.md` (executive summary → findings with evidence + confidence → contradictions/uncertainties → conclusion → sources). Keep it tight; lead with the answer.
4. **Offer more.** End with a single line: *"Want this saved to a markdown file, or turned into an interactive page? Or say 'deep research' to fan out across the sub-topics."* Don't save a file or build a page in standard mode unless asked — the chat report is the deliverable.

---

## Deep workflow

Four phases. The split between mapping the territory (Phase 1) and walking it (Phase 2) is what makes this better than just running more searches — you spend the parallel budget on branches you've confirmed are real and distinct, instead of fanning out blind.

### Phase 1 — Reconnaissance

Do a broad first pass yourself: enough searching to understand the shape of the topic and find where the substance lives. The goal is not to answer anything yet — it's to **decompose the topic into 4–8 distinct, non-overlapping sub-questions ("branches")** that together cover it. Good branches are independently researchable and don't duplicate each other (e.g. for "logical replication vs Debezium for CDC": operational overhead, throughput/latency at scale, schema-change handling, failure modes & recovery, ecosystem/tooling maturity, cost).

Present the branch list to the user and confirm before fanning out:

> **Branches I'll research in parallel:**
> 1. ...
> 2. ...
>
> **Next:** go ahead, or adjust the branches first?

Skip the pause only if the user already said "just go" / "don't ask" / "deep research X and build the page". Otherwise wait — re-scoping here is cheap; re-running five agents is not.

### Phase 2 — Parallel fan-out

Spawn **one sub-agent per branch, capped at 5** (if recon produced more than 5 branches, merge the closest ones first). Launch them **in a single message** (multiple Agent calls in one block) so they run concurrently.

Use `subagent_type: general-purpose` (it has WebSearch/WebFetch and can read the methodology file). Each agent's prompt must contain:

- **The branch question** and a one-line scope boundary ("only cover X; another agent handles Y").
- **This instruction, verbatim:** *"Read `/home/catalysm/code/skills/skills/research/references/methodology.md` and follow its source-quality, verification, and citation standards. Return a branch mini-report in the report structure it defines."* (Adjust the path if the skill lives elsewhere — resolve it from this file's location.)
- **The overall research question** for context, so the branch stays relevant to the user's actual goal.
- **What to return:** the mini-report as its final message — cited findings, confidence levels, and an explicit note on anything it couldn't verify. Tell it not to implement anything or edit files; it only researches and reports.

Sub-agents return their reports to you; nothing is shown to the user automatically, so you carry forward what matters.

### Phase 3 — Synthesis

Combine the branch reports into one coherent investigation — don't just concatenate them:

- **Cross-reference and dedupe** findings that several branches surfaced; merge into one, keeping the strongest sources.
- **Resolve or flag conflicts** between branches using the conflict format in `references/methodology.md` — a disagreement between two branches is a finding, not a problem to hide.
- **Assign overall confidence** per finding and call out what the whole investigation still couldn't establish.
- **`Write` the master report** to `./research-<topic-slug>.md` using the full report structure. This file is the durable artifact and the source for the page.

### Phase 4 — Handoff to rich-page

Invoke the **`rich-page` skill via the Skill tool**, passing the saved report as the source:

```
Build a rich visual HTML page from this research report: ./research-<topic-slug>.md
Audience: <whoever the user mentioned, else "the user / their team">. Language: <match the report>.
Output path: ./research-<topic-slug>.html
Just build it — don't ask for confirmation on the visual plan.
```

`rich-page` accepts a research bundle as a source — its Phase 1 reads the markdown report end-to-end and identifies "candidate visual moments" (charts for quantitative claims, comparison toggles for "X vs Y" branches, node diagrams for any architecture mentioned, etc.). Telling it "just build it" skips the Phase 2 confirmation pause so the deep-research run ends with the artifact in hand, not another approval gate. When it's done, hand back both paths to the user — the markdown report and the HTML page — in one short message, and note they can ask for any branch to be re-researched or the page restyled.

---

## You research; the human decides

When the report is done, **stop and let the user act on it.** Research exists to inform a human decision — what to build, which option to pick, whether a claim holds up. If you slide straight from "here's what I found" into changing code, configs, or dependencies, you erase the decision point the research was meant to create, and you do it based on findings the user hasn't even read yet.

So after presenting findings (standard) or handing off the artifacts (deep): don't implement, refactor, reconfigure, or "go ahead and apply the best practice." Answer follow-up questions about the sources and analysis, and wait for the user to tell you what to do with it. The one exception is the rich-page handoff in deep mode — that's part of producing the research deliverable, not acting on it.

---

## Reference files

- `references/methodology.md` — source-quality hierarchy, verification practices, citation format, red flags, and the report structure. Read it before researching; point every sub-agent at it in deep mode.
