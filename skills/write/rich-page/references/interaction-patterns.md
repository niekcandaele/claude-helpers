# Interaction patterns

A catalog of reusable visual patterns. Each entry tells you **when to pick it**, **when not to**, and **which technique** to reach for (see `visual-techniques.md` for library specifics).

Pick **4–7 centerpiece visuals** per page, plus 0–2 small accent visuals. More than that and the page becomes a toybox. Each centerpiece should carry the weight of a major conceptual claim from the source.

---

## How to pick

Read the source and ask: what would a reader most likely *misunderstand* if it were prose? That's where a visual goes. Specifically look for:

| Signal in the source | Pattern |
|---|---|
| "X is way better than Y" / "with vs without" / "naïve vs" | **Comparison toggle** |
| A trend, distribution, or quantitative claim ("p99 is 340ms", "throughput dropped 40%") | **Annotated chart** |
| Multiple categories of the same metric ("per region", "per team") | **Small multiples** |
| An architecture with 3–6 named components & data flow | **Hover/click node diagram** |
| A protocol, handshake, request/response dance | **Sequence diagram** |
| A cyclic process (loop, feedback, retry, observe-act) | **Animated process loop** |
| A parameter with non-obvious effect on a distribution | **Slider + live chart** |
| Phases / milestones / time-bound stages | **Click-to-expand timeline** |
| "We collapsed N items into M categories" | **Aggregation animation** |
| A genuinely sequential explanation that benefits from progressive disclosure | **Scroll-tied sequence** |
| A section with 4+ sub-views that don't deserve their own scroll-section | **Tabbed view** |
| A simple flow/state machine you'd otherwise hand-draw | **Mermaid diagram** |

For PRD-shape and spec-shape sources, the SKILL.md Phase 2c includes a more detailed "PRD-shape sources" table mapping content shapes (V1 vs deferred, customer vs operator, etc.) to interactive patterns by default. That table is canonical for those mappings — consult it during visual-inventory pick when the source is a PRD or internal doc.

**Don't force a pattern.** If nothing in the source matches, write more prose and use cards. A page with three deep visuals beats a page with seven shallow ones.

---

## Pattern 1 · Annotated chart (Chart.js)

**What it shows.** A quantitative claim. The numbers themselves are the visual; the annotation tells the reader where to look.

**Use when.** The source contains numbers worth showing — latencies, conversion rates, before/after measurements, distributions, time series. The reader's takeaway is a specific magnitude or shape.

**Don't use when.** The numbers are decorative ("our team grew from 5 to 8"). A sentence handles that.

**Technique.** Chart.js + `chartjs-plugin-annotation`. See `visual-techniques.md` § Chart.js for the CDN tags and a worked example.

**Rules:**
- Always annotate the threshold, the spike, the SLO, the median — whatever the lesson is.
- Hide the legend on single-series charts.
- Pull colors from CSS custom properties so the chart inherits the theme.
- 360px max height; otherwise it dominates the section.

---

## Pattern 2 · Small multiples (Observable Plot)

**What it shows.** The same chart faceted across categories. Lets the reader scan for patterns across (e.g.) regions, teams, products, time buckets.

**Use when.** The source has a metric measured across 3–9 categories, and the comparison across categories *is* the point.

**Don't use when.** There are only 2 categories (use one chart with two series). Or more than 9 (use a heatmap).

**Technique.** Observable Plot's `fy:` faceting. See `visual-techniques.md` § Observable Plot.

---

## Pattern 3 · Comparison toggle

**What it shows.** Two states of the same thing, side by side or toggled. Sliders let the reader change a parameter and watch *both* states respond. The lesson is the contrast.

**Use when.** The whole point of a section is "X vs Y" and the difference is quantitative or structural. Classic cases: "M×N vs M+N integrations", "naive O(n²) vs indexed O(n log n)", "before refactor / after refactor".

**Don't use when.** The contrast is purely qualitative ("Postgres vs MongoDB philosophy") — write prose with two columns. Or when there's no parameter to vary; a static side-by-side is better.

**Technique.** Vanilla JS + inline SVG (or two Chart.js canvases driven by a shared slider). 30-line implementation; no library needed for the toggle itself.

**Rules:**
- Update the live counter on every change. The number ticking is what sells the point.
- Label both sides explicitly ("Naïve: M×N = 56 integrations" / "Indexed: M+N = 15").

---

## Pattern 4 · Hover/click node diagram

**What it shows.** An architecture: 3–6 named components with directional relationships. Clicking a node reveals its detail in a side panel; edges connecting that node light up.

**Use when.** The source has a named architecture (e.g. "Agent–Planner–Executor–Memory–Feedback Loop", "frontend / API / queue / worker / DB"). The reader should study one piece at a time without losing the whole.

**Don't use when.** There are more than 7 components — diagram gets crowded; split or simplify. Or when relationships are non-directional (use a card grid).

**Technique.** Inline SVG with `<g class="node" data-id="…">` per component. See `visual-techniques.md` § Inline SVG.

**Rules:**
- Position nodes on a coarse grid; don't try fancy radial layouts in handwritten SVG.
- Side panel sits to the right of (or below, on mobile) the diagram.
- Default panel state shows an overview, not a blank.

---

## Pattern 5 · Sequence diagram

**What it shows.** A protocol or handshake. Vertical client/server columns. Each row is a message in one direction; clicking it reveals the actual payload.

**Use when.** The source documents a protocol, API handshake, request/response dance. Payloads matter — they're not noise, they're the lesson.

**Don't use when.** The protocol is just "client calls server" with no interesting state (a card with two paragraphs is faster).

**Technique.** Two options:
- **Mermaid** if the sequence is simple and payloads aren't shown — one terse text block (see `visual-techniques.md` § Mermaid).
- **Custom HTML** with clickable rows revealing `<pre>` payloads if the payloads matter, or when you want tighter visual control than Mermaid's defaults. A worked CSS-grid sequence pattern is in `visual-techniques.md` § Custom HTML sequence.

**Rules:**
- 4–6 rows max. Each payload fits ~10 lines of monospace.
- Write *real-looking* payloads, not `// …`.

---

## Pattern 6 · Animated process loop

**What it shows.** A genuinely cyclic process — Thought → Action → Observation → Thought. Play/Step/Reset buttons walk through a scripted example, active node highlighted, log on the side.

**Use when.** The source describes a loop and the *specific sequence* matters. ReAct, retry-with-reflection, observe-orient-decide-act, event-loop tick. Each step has concrete content.

**Don't use when.** The "loop" is actually a linear pipeline — use a timeline or sequence diagram. Or steps are abstract and you can't write a real example.

**Technique.** Inline SVG (3-5 nodes in a polygon) + vanilla JS for the step controller + a `<div>` log.

**Rules:**
- 10-step script is the sweet spot. <6 and the loop doesn't loop visibly. >14 and readers tune out.
- Script entries should be real: pull a concrete example from the source.

---

## Pattern 7 · Slider + live chart

**What it shows.** How one or two parameters reshape a distribution, curve, or value set. Sliders update a chart in real time via deterministic JS.

**Use when.** The source explains a parameter whose effect is *non-obvious* without seeing it (temperature, top-p, learning rate, sampling threshold). The reader benefits from playing with it.

**Don't use when.** The parameter's effect is obvious from the name ("max retries"). Or when "play with it" would be misleading (the real distribution depends on context that isn't in the page).

**Technique.** HTML `<input type="range">` + Chart.js. Update via `chart.data.datasets[0].data = recomputed; chart.update('none');` on each `input` event.

**Rules:**
- Show a "legend row" explaining what dim/gray bars mean if you have multiple series.
- Anchor the slider with min/max labels showing what extreme values mean.

---

## Pattern 8 · Click-to-expand timeline

**What it shows.** Sequential phases or milestones. Horizontal strip with a numbered circle per phase, connected by a gradient line. Clicking a phase expands its body.

**Use when.** Source describes phased work, a multi-stage process, or a temporal "before/during/after."

**Don't use when.** Stages are actually parallel (use a card grid). Or there are more than 6 phases (use a vertical list).

**Technique.** Pure CSS + vanilla JS. ~40 lines.

**Markup contract** (required for Phase 4 self-check #6 to count it as interactive):
- Native HTML: wrap each phase in `<details><summary>Phase N · title</summary>…body…</details>`. The `<details>` element gives free click-to-expand with no JS.
- Or custom: use `data-expand` (or `data-collapse`) on the click target + `class="phase"` on the phase wrapper + a JS handler that toggles an `aria-expanded` attribute.

**Rules:**
- Keep phase numbers in temporal order. Don't sort by "most interesting."
- Each phase body has a `<h4>` + a short `<ul>` of deliverables + a date/duration.

---

## Pattern 9 · Aggregation animation

**What it shows.** "We reduced N to M." Many small SVG dots collapse into M clustered bubbles on a button press. Each cluster is clickable to reveal its members.

**Use when.** A core point of the source is *consolidation* or *abstraction* — "100 REST endpoints → 36 tools", "200 tests → 12 suites", "50 services → 8 contexts."

**Don't use when.** The aggregation is trivial (grouping by date). Or the numbers aren't large enough for impact (15 → 5 isn't dramatic).

**Technique.** Inline SVG (grid of `<circle>` dots) + vanilla JS animation using `requestAnimationFrame` or GSAP for smooth transitions.

**Rules:**
- The "Aggregate" button label and the caption ("N endpoints → M tools") are the lesson. Write them carefully.
- 6×18 dot grid (108 dots) is a reliable starting size for "many."

---

## Pattern 10 · Scroll-tied sequence

**What it shows.** A sequential explanation that progressively reveals as the reader scrolls. The page pins a section and steps light up one by one.

**Use when.** The topic is genuinely sequential and progressive disclosure adds understanding. Walking a packet through a stack. Building up a formula one term at a time. Showing how an algorithm's state evolves.

**Don't use when.** The order doesn't matter. Or the reader needs to compare steps side-by-side (use a static diagram instead).

**Technique.** GSAP ScrollTrigger with `pin: true, scrub: true`. See `visual-techniques.md` § GSAP.

**Rules:**
- **One per page max** — this technique is heavy on attention.
- Always include a `prefers-reduced-motion` fallback that just renders all steps visible.
- Section height = `300vh` for 4 steps; scale by step count.

---

## Pattern 11 · Tabbed view

**What it shows.** A single section with 4+ sub-views that don't deserve their own scroll section.

**Use when.** An "evaluation" section needs cases / criteria / methodology / models / metrics — five subtopics worth showing, none individually big enough for a full section.

**Don't use when.** Only 2 sub-views (use a comparison toggle instead, which contrasts the two states more sharply than tabs). For multi-audience PRD-shape content where the reader needs to compare audiences (customer vs operator, V1 vs deferred), the tabbed view still wins over a card grid — the perspective-switch IS the value, even when the reader will visit both tabs.

**Technique.** CSS class-toggle on `.tab.active` + `.tabpanel.active`. ~10 lines of JS.

**Rules:**
- First tab is the default-active one. Make it the most-likely-skimmed content.
- Tab labels are short (2-3 words).

---

## Pattern 12 · Mermaid flow/state/ER

**What it shows.** A simple flowchart, state machine, or entity-relationship diagram you'd otherwise hand-draw.

**Use when.** The shape is *describable in text* and you don't need custom node styling or interactions.

**Don't use when.** You want clickable nodes or bespoke layout — use inline SVG.

**Technique.** Mermaid. See `visual-techniques.md` § Mermaid.

**Rules:**
- Theme Mermaid to inherit your page's CSS custom properties (see Mermaid section in `visual-techniques.md`).
- One diagram per Mermaid block. Don't try to cram two diagrams into one.

---

## Combining patterns

A section can use one pattern *or* combine two (e.g. a comparison toggle whose nodes are also clickable for detail). Don't combine more than two — readers can only juggle so many affordances at once.

---

## When to skip interactivity entirely

Some sections work best as plain prose with a single great illustration card or pull-quote:

- The conclusion is usually one of these.
- The "Het probleem" / problem-statement intro is usually one of these.
- A section that's quoting the source's own voice is usually one of these.

Don't feel obligated to make every section visual. Three deep visuals + several plain prose sections beats seven shallow visuals everywhere.

---

## Mobile

At <880px, the design system collapses everything to single-column. Most patterns reflow gracefully because their SVGs use `viewBox`. Specific notes:

- **Comparison toggle**: stack the two sides vertically.
- **Hover/click node diagram**: side panel moves below the diagram.
- **Sequence diagram**: client/server columns stay; reduce padding.
- **Slider + chart**: chart shrinks to ~280px height.
- **Scroll-tied sequence**: works the same; pin section still pins.

**Test by resizing the browser window** before handing off.
