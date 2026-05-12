---
name: explainer-page
description: >
  Generate a self-contained, visually rich, interactive single-page HTML
  explainer from a source brief, document, PDF, research bundle, or topic
  description. Output is one .html file with inline CSS, inline JS, and inline
  SVG — no CDN, no images, no build step. Use whenever the user wants an
  "informational page", "interactive explainer", "rich one-pager",
  "landing-style summary", "distilled research page", "visual breakdown",
  "interactive write-up", or asks to "turn this PDF/doc into a page" — even
  when they don't use those exact words, e.g. "make something I can show the
  team about X", "make this less boring", "give it some eye candy", "explain
  this in a richer way than a doc". Also trigger for conversions ("turn this
  research into a page") and rebuilds ("redo that page"). Distinct from
  slides-generator: that produces a sequential deck; this produces one long
  scrolling page with anchor navigation and embedded interactive diagrams.
---

# explainer-page

Build an opinionated, visually distinctive single-page HTML explainer from a source. The output is one self-contained `.html` file the user can open offline — dark palette, animated hero, sticky nav, scroll-reveal sections, and **4–6 genuinely interactive diagrams** embedded inline (sliders, click-to-detail SVGs, animated process loops, comparison toggles, expandable timelines, aggregations).

This skill is a **four-phase workflow**. The split between Phase 2 (outline + interaction inventory) and Phase 3 (build) is what keeps the page focused — without it, every diagram becomes a slider and the page becomes a toybox.

## When this skill applies

Trigger for explicit asks ("make an interactive HTML page about X", "turn this PDF into a rich page"), but also for implicit ones:
- "I want something I can show the team about Y"
- "explain Z in a more visual way than a doc"
- "make this readable and pretty"
- "give this some eye candy"
- "distill our research into a page people will actually read"
- "I want a one-pager for [feature, project, topic]"
- "rebuild that explainer page"

If the user shows up with a source file (PDF, markdown, notes) and asks for a "rich" or "interactive" or "visual" treatment, this skill fits. If they want a **sequential deck** to present from, use `slides-generator` instead. If they want a **plain doc/report**, use `technical-writer`.

## Workflow at a glance

1. **Intake.** Read the source if there is one. Otherwise collect topic, audience, language, output path. Identify candidate "interactive moments".
2. **Outline + interaction inventory.** Sketch the section list and pick 4–6 centerpiece interactives from the catalog. Stop and confirm (unless the user said "just build it").
3. **Build the HTML.** Copy `references/page-template.html`, delete unused interactives, fill in real content, write one file.
4. **Self-check + handoff.** Parse the HTML, grep for stray network deps, report the path.

Each phase below says what to do, what supporting file to load, and what output the user should see.

---

## Phase 1 — Intake

Goal: understand the source well enough to plan the page. Don't over-interview.

### If a source file is provided

Read it end-to-end with the `Read` tool. For long PDFs (>10 pages), use the `pages` parameter to chunk it — don't skip to the conclusion. You want the table of contents, the figures, the methodology, the limitations, and the conclusion. Note:

- **Title, author, attribution, date** — for the hero block and footer.
- **The source's own visual language** — accent colors, fonts. The default palette in this skill is dark + coral, but if the source uses a distinctive color (e.g. an orange PDF cover), keep it.
- **The source's language** — Dutch source → Dutch page. French source → French page. Keep technical terms in their original language as the source does.
- **Candidate interactive moments.** Scan for any of:
  - **Comparisons** ("with X vs without X", "before/after", "naïve vs optimised") → comparison toggle
  - **Architectures with 3–6 components** → hover/click node diagram
  - **Cyclic processes / loops** → animated process loop
  - **Protocols / sequences** → sequence diagram with clickable payloads
  - **Parameters with non-obvious effects on distributions** → slider + bar chart
  - **Plans, milestones, phased work** → click-to-expand timeline
  - **"We reduced N to M"** → aggregation animation
  - **A section with 4+ sub-views** → tabbed view
- **Hard numbers** for the key-facts strip (page count, sections, sample size, models tested, metrics, etc.).
- **Placeholders the source itself contains** (`[TBD]`, `[to be determined]`, `[forthcoming]`). Mirror them; don't invent data.

### If no source file, only a topic

Call `AskUserQuestion` once with these fields bundled:

- **Topic** — what's the page about? One sentence.
- **Audience** — who reads this? ("the eng team", "a client", "internal stakeholders", "the public")
- **Language** — what language should the page be in? Default to whatever language the user is conversing in.
- **Output path** — where should the file go? Default to `./<topic-slug>.html` in CWD.
- **Source material** — any docs, links, or notes you want me to lean on? (Optional)

Don't ask four separate questions; bundle into one.

---

## Phase 2 — Outline + interaction inventory

Produce two things in one reply: the **section list** and the **interaction inventory**.

### 2a. Section list

A scroll-page rhythm that works for almost any topic:

```
1.  Hero           — title, attribution, scroll cue, link to source
2.  Sticky nav     — anchors to every below section
3.  Key facts      — 5–8 numbers, large type, single row
4.  The problem    — why this exists, plain prose
5–9. Content       — 4–6 sections, each a thematic chunk of the source
10. Limitations    — what doesn't work / open questions (if source has any)
11. Conclusion     — short, the source's takeaway in plain language
12. Footer         — author, attribution, link back to source
```

Mix card grids (`.grid.cols-2 / .cols-3 / .cols-4`) with full-width canvases for the interactives. Don't make every section a card grid — vary the density.

### 2b. Interaction inventory

Load `references/interaction-patterns.md`. Pick **4–6 centerpiece interactives** and 0–2 bonus ones. For each pick, name:

- the **pattern** (e.g. "comparison toggle"),
- the **content** it'll show (specific to this source),
- the **section** it lives in.

Resist the urge to add a seventh. The page works because each interactive carries weight; padding dilutes the impact.

### Pick well

- **One interactive per major conceptual claim**, not one per section.
- **A slider must illustrate something non-obvious.** Don't add a slider that just shows what a knob does — show what it makes possible.
- **Use comparison toggles when the contrast IS the lesson** (e.g. "M×N vs M+N" — the number-of-lines difference is the entire point).
- **Use process loops for genuinely cyclic processes**, not for linear pipelines (use a timeline or sequence diagram instead).
- **The tabbed view is a last resort** for sections with 4+ sub-views; otherwise prefer separate sections.

### End of Phase 2

Close the reply with a single line:

> **Next:** want me to go ahead and build this? (Or change anything in the outline / interactions first.)

If the user already said "just go" or "build it" in their first message, skip the pause and proceed directly to Phase 3 in the same reply.

---

## Phase 3 — Build the HTML

Enter when the user says go.

Load `references/page-template.html` and `references/design-system.md`. The template is a complete working page (~700 lines, ~60 KB) with every interactive pattern from the catalog already wired up. You build the page by **copying the template and deleting interactives you didn't pick**, then **replacing content placeholders**.

### Build steps

1. **Copy the template** to the chosen output path with the `Write` tool.
2. **Replace `{{PLACEHOLDERS}}`** in order:
   - `{{LANG}}` — ISO language code (`nl`, `en`, `fr`, …)
   - `{{TITLE}}`, `{{DESCRIPTION}}` — page metadata
   - `{{HERO_BADGE}}` (e.g. "Bachelorproef · HOGENT · 2025–2026"), `{{HERO_TITLE}}`, `{{HERO_LEDE}}`, `{{META_ROW}}`
   - `{{NAV_LINKS}}` — anchor list
   - `{{FACTS}}` — `<div class="fact"><div class="n">N</div><div class="k">LABEL</div></div>` rows
   - `{{SECTION_*}}` — content for each non-interactive section
   - **For each unused interactive**: delete the `<section>` AND the corresponding JS IIFE at the bottom (each interactive is wrapped in a clearly labeled `(function(){ … })();` block).
3. **Customise the palette** if the source has a distinctive accent. The `--coral` variable in `:root` is the main lever; cyan (`--cyan`) is the secondary accent for "the other side" in comparison diagrams. Don't touch the dark background unless the source is explicitly light-themed.
4. **Fill each kept interactive** with real data from the source — e.g. for the comparison toggle, set the labels and the "with/without" caption; for the process loop, write the actual Thought→Action→Observation script; for the timeline, set the four phase titles and bodies.
5. **Write the file.** Use the `Write` tool with the full content.

### Hard constraints — check before saving

- **One file only.** No external `<link>` or `<script src="…">`. The only allowed external href is the optional relative link back to the source PDF/doc.
- **No images.** All visuals are inline SVG or CSS gradients.
- **No frameworks, no build.** Vanilla HTML/CSS/JS.
- **No `http://` or `https://` in `src=` or `href=`** anywhere except the sibling source-file link.
- **Match the source language.** Section titles, body copy, button labels.
- **Don't invent data.** Mirror `[TBD]`-style placeholders if the source has them. Don't fabricate numbers for the key-facts strip — pull them from the source.
- **Every interactive carries content.** If you can't think of meaningful labels for a slider, delete it.
- **SVG diagrams use `viewBox` + `preserveAspectRatio`.** No hard-coded pixel widths; they reflow.
- **Responsive at 880px.** Grids collapse to one column; the agent-architecture and ReAct two-column layouts stack vertically.

### File size sanity

A well-built page typically lands at **80–140 KB**. Under 60 KB usually means the content is thin; over 200 KB means there's padding. Don't pad with filler prose to "fill out" sections — fewer, denser sections beat more, sparser ones.

---

## Phase 4 — Self-check + handoff

Run three verifications:

1. **File exists and is reasonable size**:
   ```bash
   ls -la <path>
   ```
2. **HTML parses cleanly**:
   ```bash
   python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('<path>').read()); print('parsed ok')"
   ```
3. **No stray network deps**:
   ```bash
   grep -nE 'src="http|href="http' <path>
   ```
   Should return nothing, or only the optional sibling source link (which is fine).

If any check fails, fix and re-run before handing off.

### Handoff message

One short message:

- Where the file is and how to open it (`xdg-open <path>` on Linux, `open <path>` on macOS, double-click on Windows).
- A brief list of what's in it — the centerpiece interactives by name.
- A one-line offer: "Want a different palette, a different interactive, or any section rewritten? Say what you'd change and I'll update."

Don't recap section-by-section — the user just saw the outline in Phase 2.

### Optional: visual check

If `mcp__playwright__browser_navigate` is available **and** the user wants a visual smoke-test (or you suspect a layout issue), open the file via `file://` and take a snapshot. Don't run this by default — it adds latency and the user can just open the file themselves.

---

## Iteration — what to do when the user comes back

- **"Change the accent color to X"** — edit the `--coral` (or `--cyan` for secondary) custom property in `:root` and any `#F58A5C`-style hardcodes inside SVGs.
- **"Add an interactive for [thing]"** — open the template, copy the matching pattern's HTML + JS block, customise. Don't rebuild from scratch.
- **"Reorder sections / add a section"** — edit the HTML directly. Don't re-run Phase 2.
- **"Make it lighter / less dark"** — change `--bg`, `--bg-2`, `--panel`, `--text`, `--muted` in `:root`. The rest of the design system follows.
- **"Translate the page"** — find/replace section titles and body copy; the structure stays. Don't translate technical English terms the source itself leaves in English.
- **"Different topic, same style"** — go to Phase 1 with the new source. The skill is the recipe; each output is fresh.

---

## Heuristics & gotchas

- **One accent color.** Coral by default; cyan only as the "other side" in comparison diagrams; violet only for tertiary highlights inside process loops. More than three accents and the page looks like a marketing brochure.
- **Reveal-on-scroll is fade-up only.** No spinning, no sliding-from-the-side. The IntersectionObserver pattern in the template handles it; don't override.
- **Don't animate the hero gradient too aggressively.** The default conic-gradient blur drifts on an 18-second loop. Faster than that and it distracts from reading.
- **Sticky nav active-state** uses scroll position vs. section `offsetTop` with a 120px lead — already in the template.
- **`viewBox="0 0 W H"` on every SVG.** Diagrams reflow with the container width; never set `width="800"` directly.
- **Code/JSON inside the page uses the proven `.mono` and `.pill` classes**, not raw `<code>` — those carry the palette.
- **Don't add a back-to-top button.** The sticky nav does this work; an extra widget is clutter.

---

## Reference files

- `references/page-template.html` — full working page scaffold. Copy this in Phase 3, then strip and fill. Contains every pattern from the catalog already wired up.
- `references/design-system.md` — palette, typography, layout primitives, hero recipe, sticky nav, reveal, buttons, cards, tabs. Load in Phase 3 when customising.
- `references/interaction-patterns.md` — catalog of 8 reusable interactive diagrams with when-to-use, when-NOT, and a code-skeleton pointer to the matching block in `page-template.html`. Load in Phase 2b.
