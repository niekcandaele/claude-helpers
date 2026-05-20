# Research methodology and standards

This file is the single source of truth for *how* research is conducted and reported in the `research` skill. The orchestrator follows it, and every spawned sub-agent is pointed here so all branches return work in the same shape. Read it once, internalise it, then research.

## Core stance: research, verify, cite — never assume

The value of research is verified evidence with clear attribution, not confident-sounding prose. So:

- Investigate with multiple independent sources rather than the first hit.
- Back every substantive claim with credible evidence and a citation.
- Distinguish facts from opinions, and correlation from causation.
- Be explicit about confidence and about what you couldn't verify. Acknowledging a gap is more useful than papering over it — it tells the reader exactly where to dig.

## Source-quality hierarchy

When sources conflict or you must choose what to trust, prefer them roughly in this order:

1. **Official documentation** — primary, authoritative (the project's own docs, the spec, the vendor's reference).
2. **Academic / peer-reviewed papers.**
3. **Standards bodies** — W3C, IETF, OWASP, ISO, etc.
4. **Recent technical articles** (prefer the last ~2 years for fast-moving topics) from credible, named authors.
5. **Blog posts from recognised experts.**
6. **Forum / Q&A / social** — useful for leads and lived experience, but verify elsewhere before relying on it.

Recency matters more in fast-moving domains (web platform, ML, security) than in stable ones (math, established protocols). Weight accordingly rather than applying a blanket cutoff.

## Verification

- Search for both supporting **and** contradicting evidence before settling a claim. If you only looked for confirmation, you haven't verified anything.
- Cross-reference across sources that don't cite each other — three articles all quoting one blog post is one source, not three (watch for echo chambers).
- Check publication / update dates; flag anything presented as current that is actually stale.
- For technical specifics, verify against the official spec or docs rather than a summary of them.
- When data or code is in scope and tools are available (DB/MCP access, the repo itself), verify claims against the primary artifact instead of trusting prose about it.

## Citation format

Every substantive claim carries its source inline:

```
[Claim or statement] — [Source Title](https://url) (Author/Org, Date)
```

When sources genuinely disagree, surface it rather than silently picking one:

```
**Conflicting information:**
- Source A claims X — [Title](url) (Date)
- Source B claims Y — [Title](url) (Date)
- Assessment: [which is more credible and why]
```

## Red flags — treat with extra scrutiny

No date, no author, no sources cited, absolute claims ("always", "never", "impossible"), anecdote presented as proof, obviously stale info presented as current, or commercial content dressed up as neutral analysis.

## Report structure

Use this shape for both a standard report and each sub-agent's branch mini-report (sub-agents scope it to their branch). It scales down cleanly for small topics — keep the sections, shorten the contents.

```markdown
# Research: [Topic / branch question]

## Executive summary
2–3 sentences: the key findings and the bottom line.

## Questions investigated
1. ...

## Key findings

### Finding: [clear, specific statement]
**Evidence:**
- [point] — [Source](url) (Org, Date)
- [point] — [Source](url) (Org, Date)
- [point] — [Source](url) (Org, Date)   ← aim for ≥2–3 independent sources on important claims

**Analysis:** what the evidence actually shows (vs. what it's often assumed to show).

**Confidence:** High / Medium / Low — and why.

## Contradictions & uncertainties
Where sources disagreed, what couldn't be verified, what assumptions were made, what's missing.

## Conclusion
Short, with the caveats intact.

## Sources
1. [Title](url) — Org, Date — why it mattered
2. ...
```

## What good looks like

✓ Specific, targeted queries; official docs checked first; recent sources preferred where recency matters.
✓ Important claims cross-referenced across ≥2–3 independent sources.
✓ Confidence stated; limitations named; facts kept separate from interpretation.

## What to avoid

✗ Claims with no source, or one source for something important.
✗ Opinions presented as facts; contradictory evidence quietly dropped.
✗ Stale sources used without noting their age; cherry-picking to fit a conclusion.
