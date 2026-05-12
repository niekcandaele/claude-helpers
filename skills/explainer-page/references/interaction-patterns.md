# Interaction patterns

A catalog of reusable interactive diagrams. Each pattern has a working implementation in `page-template.html` — this file tells you **when to pick it**, **when not to**, and **what the matching block looks like** so you can lift it cleanly.

Pick **4–6 centerpiece interactives** per page, plus 0–2 bonus ones. More than that and the page becomes a toybox. Each interactive should carry the weight of a major conceptual claim from the source.

---

## How to pick

Read the source and ask: what would a reader most likely *misunderstand* if it were prose? That's where an interactive goes. Specifically look for:

| Signal in the source                                      | Pattern              |
| --------------------------------------------------------- | -------------------- |
| "X is way better than Y" / "with vs without" / "naïve vs"  | Comparison toggle    |
| An architecture with 3–6 named components & data flow      | Hover/click node     |
| A cyclic process (loop, feedback, retry, observe-act)      | Animated loop        |
| A protocol, handshake, request/response dance              | Sequence diagram     |
| A parameter that's non-obviously affecting a distribution  | Distribution sliders |
| Phases / milestones / time-bound stages                    | Click-to-expand timeline |
| "We collapsed N items into M categories"                   | Aggregation animation |
| A section with 4+ sub-views (e.g. "evaluation" with many cuts) | Tabbed view      |

**Don't force a pattern.** If nothing in the source matches the eight patterns, write more prose and use cards. A page with three deep interactives beats a page with seven shallow ones.

---

## Pattern 1 · Comparison toggle

**What it shows.** Two states of the same thing, side by side or toggled. Sliders let the reader change a parameter and watch *both* states respond. The lesson is the contrast.

**Use when.** The whole point of a section is "X vs Y" and the difference is quantitative or structural. Classic cases: "M×N vs M+N integrations", "naive O(n²) vs indexed O(n log n)", "stdio transport vs Streamable HTTP", "before refactor / after refactor".

**Don't use when.** The contrast is purely qualitative ("Postgres vs MongoDB philosophy") — just write prose with two columns. Or when there's no parameter to vary; a static side-by-side is better.

**Template block.** Look for `1) M×N → M+N diagram` in the `<script>` of `page-template.html`. The matching HTML is the section with `id="mxn"` and `<svg id="mxn-svg">`. Customise:
- Slider min/max/labels.
- Node labels (`M1, M2 …` and `T1, T2 …` → whatever the source calls them).
- The center node label ("MCP" → your equivalent).
- The two formula strings.

**Rule of thumb.** Update the live counter on every change. The number ticking down is what sells the point.

---

## Pattern 2 · Hover/click node diagram

**What it shows.** An architecture: 3–6 named components with directional relationships. Clicking a node reveals its detail in a side panel; edges connecting that node light up.

**Use when.** The source has a named architecture (e.g. "Agent–Planner–Executor–Memory–Feedback Loop", "frontend / API / queue / worker / DB"). The reader should be able to study one piece at a time without losing the overall shape.

**Don't use when.** There are more than 7 components — the diagram gets crowded; split into two diagrams or simplify. Or when the relationships are non-directional (use a card grid).

**Template block.** `3) Agent architectuur diagram` in the JS, with `<svg id="agent-svg">` in HTML. Customise:
- The `nodes` array: `id`, `x`, `y`, `w`, `h`, `title`, `desc`.
- The `edges` array: pairs of node ids.
- The side-panel default copy.

**Rule of thumb.** Position nodes on a grid; don't try fancy radial layouts in SVG. The clean rectangles are what makes it readable.

---

## Pattern 3 · Animated process loop

**What it shows.** A genuinely cyclic process — Thought → Action → Observation → Thought again. Play/Step/Reset buttons walk a reader through a *scripted* example, with the active node highlighted and a log on the side.

**Use when.** The source describes a loop and the *specific sequence of events* matters. ReAct, retry-with-reflection, observe-orient-decide-act, event-loop tick. Each step has concrete content (a thought, a tool call, an observed result).

**Don't use when.** The "loop" is actually a linear pipeline — use a timeline or sequence diagram. Or when the steps are abstract and you can't write a real scripted example for them.

**Template block.** `4) ReAct loop animation` in JS, `<svg id="react-svg">` + `<div id="react-log">` in HTML. Customise:
- The `nodes` array — typically 3 in a triangle, but works for 2, 4, or 5.
- The `script` array — `{k, v}` pairs that drive the log. Make it real: pull a concrete example from the source.

**Rule of thumb.** A 10-step script is the sweet spot. Less than 6 and the reader doesn't get to see the loop loop. More than 14 and they tune out before Play finishes.

---

## Pattern 4 · Sequence diagram with clickable payloads

**What it shows.** A protocol or handshake. Vertical client / server columns. Each row is a message in one direction; clicking it reveals the actual JSON/text payload below.

**Use when.** The source documents a protocol, an API handshake, a request/response dance. The payloads matter — they're not implementation noise, they're the lesson.

**Don't use when.** The protocol is just "client calls server" with no interesting state — a card with two paragraphs is faster.

**Template block.** `5) MCP handshake sequence` in JS, `<div class="seq">` in HTML. Customise:
- The number of rows and direction (`l-to-r` vs `r-to-l`).
- The label of each row (a method name, typically).
- The `payloads` array of strings. Write real-looking payloads, not `// …`.

**Rule of thumb.** 4–6 rows. Each payload should fit ~10 lines of monospace; longer than that and the reader stops reading.

---

## Pattern 5 · Distribution sliders

**What it shows.** How one or two parameters reshape a probability distribution, latency curve, or any value-by-category set. Sliders update a bar chart in real time via deterministic JS — no real model call.

**Use when.** The source explains a parameter whose effect is *non-obvious* without seeing it (temperature, top-p, learning rate, sampling threshold). The reader benefits from playing with it.

**Don't use when.** The parameter's effect is obvious from the name ("max retries"). Or when "play with it" would be misleading because the real distribution depends on context.

**Template block.** `2) Sampling distribution` in JS, `<div id="barchart">` in HTML. Customise:
- The `tokens` array — `[label, logit]` pairs. 8–12 entries.
- The math (the template uses softmax + top-p nucleus). Swap for whatever your parameter affects.
- Slider min/max/step.

**Rule of thumb.** Always include a "legend row" explaining what the dim bars mean. Without that, "why are some bars gray?" stops the reader.

---

## Pattern 6 · Click-to-expand timeline

**What it shows.** Sequential phases / milestones. Horizontal strip with a numbered circle per phase, connected by a gradient line. Clicking a phase expands its body in place.

**Use when.** The source describes phased work (literature → analysis → build → evaluate), a multi-stage process, or a "before/during/after" narrative. The phases are *temporally ordered*.

**Don't use when.** The "stages" are actually parallel (use a card grid). Or when there are more than 6 phases (use a vertical list instead).

**Template block.** `6) Methodologie timeline` in JS, `<div class="tl">` in HTML. Customise:
- The `<div class="phase">` blocks — usually 4. Each has `.num`, `<h4>`, `.when`, `.body`.
- The phase bodies — use `<ul>` lists for deliverables, **bold** for key tech choices.

**Rule of thumb.** Keep the phase number in the order it ran. Don't sort by "which the user is curious about most"; the temporal order is part of the meaning.

---

## Pattern 7 · Aggregation animation

**What it shows.** "We reduced N to M." Many small SVG dots representing the raw set, that collapse into M clustered bubbles on a button press. Each cluster is clickable to reveal its members.

**Use when.** A core point of the source is *consolidation* or *abstraction* — "100 REST endpoints → 36 tools", "200 tests → 12 test suites", "50 services → 8 bounded contexts".

**Don't use when.** The "aggregation" is trivial (grouping by date). Or when the numbers aren't large enough to make the visual impactful (15 → 5 isn't dramatic).

**Template block.** `7) Tool aggregation animation` in JS, `<svg id="agg-svg">` in HTML. Customise:
- The `categories` array — `{id, label, count, tools}` entries.
- The `ROWS × COLS` grid that controls how many "raw" dots are drawn (template uses 6×18 = 108 dots).

**Rule of thumb.** The "Aggregeer" button label and the "X+ endpoints → Y tools" caption are the lesson. Write them carefully — they're the headline, not the dots.

---

## Pattern 8 · Tabbed view

**What it shows.** A single section with 4+ sub-views that don't deserve their own scroll section. Click a tab, the panel below swaps.

**Use when.** An "evaluation" section needs cases / criteria / methodology / models / metrics — five subtopics that're all worth showing but none individually big enough for a full section.

**Don't use when.** You have only 2 sub-views (just put them side by side). Or when the user is likely to want to *compare* tabs (then use a card grid so both are visible).

**Template block.** `8) Evaluation tabs` in JS, `<div class="tabs">` + `<div class="tabpanel">` blocks in HTML. Customise:
- The `<div class="tab">` labels and `data-tab` ids.
- The `<div class="tabpanel">` contents, each with a matching `data-panel`.

**Rule of thumb.** First tab is the default-active one. Keep the first tab's content as the most-likely-skimmed (e.g. testcases overview, not deep methodology).

---

## Bonus considerations

### Combining patterns

A section can use one pattern *or* combine two (e.g. a comparison toggle whose nodes are also clickable for detail). Don't combine more than two — readers can only juggle so many affordances at once.

### When to skip interactivity entirely

Some sections work best as plain prose with a single great illustration card. The conclusion is usually one of these. The "Het probleem" intro is usually one of these. Don't feel obligated to make every section interactive — three deep + several plain beats seven shallow.

### Mobile

At <880px, the design system collapses everything to single-column. Pattern 1 (comparison) and pattern 4 (sequence) reflow gracefully; pattern 5 (sliders) needs no special handling; the others reflow because their SVGs use `viewBox`. **Test by resizing the browser window** before handing off.
