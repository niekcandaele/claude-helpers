---
name: rich-page
description: >
  Generate a single self-contained HTML page that is genuinely visual AND
  interactive — charts, diagrams, motion, tabs, comparison toggles,
  click-to-expand, base64-inlined images, opinionated typography. Use
  whenever the user wants ANY rich visual artifact from arbitrary content:
  explainer, research write-up, PRD or spec page, pitch, internal
  one-pager, "make this less boring" rebuild, scroll-snap deck,
  landing-style summary, distilled report. Trigger phrasings: "make me a
  page about X", "turn this PDF/doc into something visual", "build me a
  deck/talk/pitch", "explain Y in a visual way", "make this readable",
  "give it some eye candy", "I want something I can show the team", "less
  boring version of this", "rebuild that page", "redo it with more
  visuals". Output is one .html file that renders identically when DM'd —
  CDN libraries (Tailwind, Chart.js, D3, GSAP, Mermaid, Lucide) load from
  stable jsdelivr/unpkg URLs; every image is base64-inlined. Not for
  plain Markdown docs (use technical-writer), not for code review (use
  reviewer), not for maintainable component code a team will edit over
  time (use frontend-design — rich-page produces one-shot HTML artifacts,
  not living software).
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
metadata:
  group: write
---

# rich-page

Build an opinionated, visually distinctive **single self-contained HTML page** from an arbitrary source — explainer, research write-up, PRD, pitch, one-pager, distilled report, "make this less boring" rebuild. The output is one `.html` file that renders identically when DM'd to anyone: CDN-loaded libraries are allowed (they're stable), but every image is base64-inlined so there are no external file references.

The point of this skill, in the spirit of Google Research's [Generative UI](https://generativeui.github.io/) work: **generate the interface, not just the content.** Most "explainers" written by AI default to prose with a card grid. Reach further. A bar chart with the SLO line called out. A Mermaid sequence of the actual protocol. A scroll-tied walkthrough of how a request travels through the system. A click-to-detail architecture diagram. Typography that signals intent. The visual treatment is the contribution.

This skill is a **four-phase workflow**. The split between Phase 2 (visual plan) and Phase 3 (build) is what keeps the page focused — without it, every section becomes a card grid and the page reverts to AI slop.

## When this skill applies

Trigger for explicit asks ("make me a rich page about X", "turn this PDF into something visual", "build me a deck"), but also for implicit ones:

- "I want something I can show the team about Y"
- "explain Z in a visual way" / "more visual than a doc"
- "make this less boring" / "give it some eye candy"
- "distill our research into a page"
- "I want a one-pager / pitch / PRD page for [thing]"
- "rebuild that page" / "redo it with more visuals"
- "turn this into something I can present"

If the user wants a **plain Markdown doc**, hand off to `technical-writer`. If they want a **review of code or a PR**, use `reviewer`. If they want **maintainable component code a team will edit over time** (React/Vue/Svelte components shipping to production), use `frontend-design` — rich-page produces one-shot HTML artifacts (DM-able files, internal pages, archival reports), not living software. If they show up with a source (PDF, markdown, notes, URL) and ask for a "rich", "visual", "interactive", "less-boring" treatment, this skill fits.

## Workflow at a glance

1. **Intake.** Read the source if there is one. Otherwise collect topic, audience, language, output path. Identify candidate "visual moments" — places where prose would lose the lesson.
2. **Visual plan.** Pick the visual direction (font pair, palette, vibe), draft the section list, and choose 4–7 centerpiece visuals from the catalog with the *technique* named for each. Stop and confirm (unless the user said "just go").
3. **Build the HTML.** Write one self-contained `.html` file: theme CSS, CDN library tags, base64-inlined images, inline SVG diagrams, inline JS for interactivity. No external image references.
4. **Self-check + handoff.** Parse the HTML, confirm self-containment, report the path.

Each phase below says what to do, what supporting file to load, and what output the user should see.

---

## Phase 1 — Intake

Goal: understand the source well enough to plan the page. Don't over-interview.

### If a source file is provided

Read it end-to-end with the `Read` tool. For long PDFs (>10 pages), use the `pages` parameter to chunk it — don't skip to the conclusion. You want the table of contents, the figures, the methodology, the limitations, the conclusion. Note:

- **Title, author, attribution, date** — for the hero block and footer.
- **The source's own visual language** — accent colors, fonts. The default palette is dark + coral; override if the source uses a distinctive color (e.g. orange thesis cover, a brand identity).
- **The source's language** — Dutch source → Dutch page. French source → French page. Keep technical terms in their original language as the source does.
- **Candidate visual moments.** Scan for any of (with the matching pattern from `references/interaction-patterns.md`):
  - **Quantitative claims, distributions, time series** → annotated chart (Chart.js)
  - **Same metric across categories** → small multiples (Observable Plot)
  - **"With X vs without X" / "naïve vs"** → comparison toggle
  - **Architecture with 3–6 components** → hover/click node diagram (inline SVG)
  - **Protocol / handshake / API dance** → sequence diagram (Mermaid or custom)
  - **Cyclic processes (loop, retry, observe-act)** → animated process loop
  - **Parameters with non-obvious effects** → slider + live chart
  - **Phases / milestones / staged work** → click-to-expand timeline
  - **"We reduced N to M"** → aggregation animation
  - **A genuinely sequential walkthrough** → scroll-tied sequence (GSAP)
  - **A section with 4+ sub-views** → tabbed view
- **Hard numbers** for the key-facts strip (page count, sections, sample size, metrics).
- **Placeholders the source contains** (`[TBD]`, `[forthcoming]`). Mirror them; don't invent data.

### If no source file, only a topic

Bundle one `AskUserQuestion` call covering:

- **Topic** — what's the page about? One sentence.
- **Audience** — who reads this?
- **Language** — default to whatever the user is writing in.
- **Output path** — default to `./<topic-slug>.html` in CWD.
- **Source material** — any docs, links, or notes? (Optional)

Don't ask four separate questions. Bundle into one.

### Escape hatch — "just go" phrases

If the user's first message contains any of these phrases, **skip the Phase 2 pause** and move directly through Phase 2 + Phase 3 in the same reply:

`"just go"` · `"just build it"` · `"build it"` · `"don't ask"` · `"skip the plan"` · `"go ahead"` · `"do it"`

Use sensible defaults for anything you'd otherwise have asked about. Still emit a **3–5 line prose summary** of your decisions (direction + sections + visuals, in flat prose, no tables, no section list, no inventory block) at the top of the reply so the user can see what you decided before scrolling to the artifact — they just don't have to approve it. The structured Phase 2 outputs (visual direction paragraph, section list, visual inventory table) belong to the gated path; in escape-hatch mode you produce the artifact directly and the summary substitutes for them. Phase 2 below references this same canonical list.

---

## Phase 2 — Visual plan

Produce three things in one reply: **visual direction**, **section list**, **visual inventory**.

### 2a. Visual direction (one short paragraph)

Name the font pair, the OKLCH palette (3 colors), the overall vibe, the target page shape. Something like:

> **Direction.** Bold editorial — Archivo Black display paired with Space Grotesk body. Palette: deep slate `oklch(0.18 0.02 260)` background, off-white `oklch(0.94 0.01 260)` text, saturated coral `oklch(0.70 0.18 40)` accent. Cyan `oklch(0.82 0.14 195)` as the "other side" in comparisons. Long scrolling page (~7 sections), sticky nav, animated conic-gradient hero, sparse motion (fade-up on reveal only).

Load `references/design-system.md`. It has the font pair catalogue, OKLCH primer, layout primitives, hero recipe, and the AI-slop avoid list. Pick a direction that fits the source's tone — don't default to "modern corporate" for every page.

### 2b. Section list

A scroll-page rhythm that works for most topics:

```
1.  Hero           — title, attribution, scroll cue, link to source
2.  Sticky nav     — anchors to every below section
3.  Key facts      — 5–8 numbers, large type, single row
4.  The problem    — why this exists, plain prose
5–9. Content       — 4–6 thematic sections, each a chunk of the source
10. Limitations    — what doesn't work / open questions (if source has any)
11. Conclusion     — short, the source's takeaway in plain language
12. Footer         — author, attribution, link back to source
```

For **short pages (≤ 5 sections)**, drop the sticky nav — it's overhead the reader doesn't need when the whole page fits in 2–3 viewports. Same for the limitations section if the source doesn't have any.

Vary the density. Mix card grids (`.grid.cols-2/3/4`) with full-width canvases for visuals, with plain prose blocks for narrative. A page that's six card grids stacked is dead — at least three different section shapes.

### 2c. Visual inventory

Load `references/interaction-patterns.md` and `references/visual-techniques.md`. Pick **4–7 centerpiece visuals** plus 0–2 small accents.

**Two hard rules that prevent the AI-slop failure mode:**

1. **Interactive minimum: at least half of your centerpiece visuals must be interactive** — the reader changes state by clicking, hovering, dragging, scrolling, or toggling. Static SVG diagrams and rendered charts count as visuals but **NOT** as interactive. Tabs, comparison toggles, sliders, click-to-expand timelines, scroll-tied sequences, animated process loops, and hover/click node diagrams DO count. A page with 5 visuals where all 5 are static SVG is failing this rule; ship at least 3 interactive ones in a 5-visual page.

2. **Card-grid cap: at most 3 `.grid.cols-N` card grids per page.** When you reach for a fourth card grid, you've defaulted to AI slop — instead, **replace it** with one of: a tabbed view (the cards are actually sub-views of one topic), a comparison toggle (two cards are a contrast), an interactive timeline (the cards are phased), or merge two sections. This rule has teeth: Phase 4 self-check #5 actually counts them, and if the count is >3 you have to fix it before handoff.

### PRD-shape sources: default to interactives, not card grids

**Consult this table BEFORE picking centerpiece visuals when the source is a spec, PRD, or internal doc.** PRD-style content has natural shapes that map directly to interactives. When you see these signals, default to the interactive pattern instead of the card-grid version — this prevents the most common failure mode for this skill:

| Source signal | Default to | Don't default to |
|---|---|---|
| "What's in V1 vs deferred" | comparison toggle OR tabbed view | two card grids |
| "Customer flow vs operator flow" | tabbed view | two card grids |
| "What we can change vs cannot change" | comparison toggle | two card grids |
| "Multiple personas / audiences" | tabbed view per persona | per-persona card grid |
| "Scope list with rationale per item" | click-to-expand timeline OR `<details>` accordion | static list of cards |
| "Decision + alternatives considered" | tabbed view (decision + each alt as a tab) | card grid |
| "Before refactor / after refactor" | comparison toggle | side-by-side cards |
| "Phased plan with deliverables per phase" | click-to-expand timeline | static list |

This table is canonical — the reduced "How to pick" table in `interaction-patterns.md` points back here for PRD-shape mappings.

### Inventory format

For each pick, name:

- The **pattern** (e.g. "annotated chart", "comparison toggle", "scroll-tied sequence")
- The **technique** — which library/approach from `visual-techniques.md` (e.g. "Chart.js with annotation plugin", "inline SVG + vanilla JS", "Mermaid sequenceDiagram")
- The **content** it'll show — specific to the source
- The **section** it lives in
- Whether it's **interactive** (yes/no) — so you can sanity-check the interactive minimum

Example (a page with 6 centerpiece visuals, 4 interactive — passes the rules):

> **Visual inventory:**
> - § Key facts: 6-cell fact strip — 1.7M tokens, 83% preference rate, 5 phases, 4 sub-agents. *Static.*
> - § The problem: annotated Chart.js bar chart, user-preference scores, GenUI bar labeled "+8 ELO". *Static.*
> - § Architecture: inline SVG node diagram (5 nodes) with click-to-detail side panel. *Interactive.*
> - § Pipeline: tabbed view (4 tabs: Plan / Generate / Post-process / Render), each with the per-phase prompt/output. *Interactive.*
> - § Evaluation: comparison toggle (Markdown vs Generative UI), slider for preference threshold. *Interactive.*
> - § How it works: GSAP scroll-tied 5-step walkthrough of the planning loop. *Interactive.* (One per page max.)

### Resist filler

- **One visual per major conceptual claim**, not one per section. If a section's claim doesn't need a visual, write prose.
- **A slider must illustrate something non-obvious.** Don't add a slider that shows what a knob does — show what it makes possible.
- **A chart must annotate.** A raw Chart.js bar chart is decoration. Mark the threshold, the SLO, the spike — whatever the lesson is.
- **Every interactive carries meaningful state.** If a tab's content is one sentence, it doesn't deserve a tab — fold it back into prose. If a comparison toggle's two sides differ by one word, write the contrast inline instead.

### End of Phase 2

Close the reply with an explicit stop:

> **Waiting for your go-ahead.** Adjust anything above — direction, sections, visuals — or say "build it" / "just go" to proceed.

Don't phrase the closer as a yes/no question ("want me to go ahead?") — those invite self-continuation. The explicit "Waiting" framing is harder to accidentally proceed past.

**Skip this pause entirely** if the user's first message contained one of the canonical "just go" phrases listed in Phase 1's "Escape hatch" section. Re-scoping here is cheap; rebuilding the HTML is not.

---

## Phase 3 — Build the HTML

Enter when the user says go (or when you skipped the pause).

Build the page as **one self-contained `.html` file**. The asset contract is non-negotiable:

- **CDN libraries are allowed** — Tailwind, Chart.js, D3, GSAP, Mermaid, Lucide, etc. They load from `cdn.jsdelivr.net` / `unpkg.com` / `cdnjs.cloudflare.com`. These are stable URLs that the recipient's browser caches.
- **Google Fonts via CDN link** is allowed for the same reason.
- **Every image is base64-inlined.** No `<img src="https://…">`, no `<img src="images/foo.png">`. See `references/image-handling.md`.
- **No build step, no framework runtime to install.** Pure HTML/CSS/JS, served straight from disk.

### Build steps

1. **Write the skeleton.** `<!doctype html>`, `<head>` with `<title>`, meta charset/viewport, OpenGraph tags if the page is share-worthy, Google Fonts `<link>` for the font pair, CDN `<script>` / `<link>` tags for the libraries you picked in Phase 2.

2. **Inline `assets/base.css` verbatim** at the top of the `<style>` block. Read the file and paste its full contents. This provides: modern reset, reveal-on-scroll baseline, stagger pattern, `prefers-reduced-motion` handling, 880px breakpoint helpers, `@media print` rules. Do not edit it.

3. **Append the theme CSS** after the base. Set `--bg`, `--text`, `--accent`, `--font-sans`, etc. as CSS custom properties on `:root` per `references/design-system.md`. Then per-section layout rules (hero, sticky nav, cards, canvases, specialty patterns).

4. **Render each section.** Hero, sticky nav, key facts, content sections, conclusion, footer. Wrap animatable elements in `.reveal` (or `.reveal.stagger` for sequenced lists). Use the primitives from `design-system.md` (`.wrap`, `.grid.cols-N`, `.card`, `.canvas`, `.fact`, `.limit`, `.pill`, `.mono`).

5. **Wire each centerpiece visual.** For each visual from Phase 2's inventory:
   - Drop the CDN tag(s) for its library in `<head>` if not already there.
   - Add the markup in the relevant section (e.g. `<canvas id="latency">`, `<div class="mermaid">…</div>`, `<svg viewBox=…>…</svg>`).
   - Add the init JS at the bottom of `<body>`, pulling colors from CSS custom properties so the visual inherits the theme. See `references/visual-techniques.md` for worked examples of each technique.

6. **Inline images.** For each raster image (hero, divider, illustration):
   - Optimize first (`cwebp -q 80 -resize 1600 0 hero.jpg -o hero.webp`).
   - Encode (`base64 -w0 hero.webp`).
   - Embed as `<img src="data:image/webp;base64,…" width="…" height="…" loading="lazy" alt="…">`.
   - Target sizes per `references/image-handling.md` (hero ≤ 200KB binary, divider ≤ 120KB).

7. **Add the IntersectionObserver for `.reveal`** at the end of `<body>`:

   ```js
   const io = new IntersectionObserver((es) => {
     for (const e of es) if (e.isIntersecting) {
       e.target.classList.add('in'); io.unobserve(e.target);
     }
   }, { threshold: .12 });
   document.querySelectorAll('.reveal').forEach(el => io.observe(el));
   ```

8. **Write the file** with the `Write` tool.

### File location

Default to `./<topic-slug>.html` in CWD. If the user specified a path, use that. Slugify the topic (lowercase, hyphens for spaces, strip punctuation). If the topic contains non-ASCII characters, transliterate first: `ë` → `e`, `ñ` → `n`, `ç` → `c`, `ø` → `o`, `ä` → `a`. ASCII-only filenames travel best across the systems people DM files to.

### Hard constraints — check before saving

- **One file only.** No external `<img src>`, no local `<script src>` or `<link href>` to relative files. The only allowed external `src=` / `href=` are CDN URLs (`https://cdn.jsdelivr.net/…`, `https://unpkg.com/…`, `https://cdnjs.cloudflare.com/…`, `https://fonts.googleapis.com/…`, `https://fonts.gstatic.com/…`) and the optional relative link back to the source PDF/doc.
- **Every image is `src="data:image/…;base64,…"`** — no exceptions.
- **No framework build runtime.** No React/Vue/Svelte/Next that requires bundling. CDN libs are runtime-only.
- **SVG diagrams use `viewBox` + `preserveAspectRatio`.** No hard-coded pixel widths.
- **Responsive at 880px.** Multi-column grids collapse to single column (base CSS handles `.grid.cols-N`).
- **Don't invent data.** Mirror `[TBD]`-style placeholders if the source has them. Don't fabricate numbers for the key-facts strip — pull from the source.
- **Every centerpiece carries content.** If you can't think of meaningful labels for a slider, delete it — don't ship empty interactivity.
- **`prefers-reduced-motion` respected.** Base CSS handles it; don't override.

### File-size sanity

Depends heavily on what CDN libraries and how much content. A lean page (a few sections, Chart.js + maybe one other lib, no rasters) lands at **20–80 KB**. A substantial page (many sections, several visuals, inline SVG diagrams, no rasters) lands at **80–300 KB**. With 2–3 base64-inlined images, add 200–500 KB. Crossing 1 MB usually means too many images or unoptimized images. Over 2 MB → re-budget.

Smaller is fine if you used few libraries — don't pad to hit a size target. The contract is "renders identically when DM'd", not "is at least N kilobytes".

---

## Phase 4 — Self-check + handoff

Run four verifications. Don't skip any.

1. **File exists and is reasonable size:**
   ```bash
   ls -la <path>
   ```

2. **HTML parses cleanly:**
   ```bash
   python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('<path>').read()); print('parsed ok')"
   ```

3. **No external file references** (only CDN libs and data URLs). Use `grep -P` (Perl regex) — GNU `grep -E` does NOT support negative lookahead and will silently match every `src=`/`href=` line:
   ```bash
   grep -Pn 'src="(?!data:|https://)|href="(?!#|https://|mailto:|tel:)' <path>
   ```
   Should return nothing. If it returns the optional sibling source-file link (e.g. `href="./source.pdf"`), that's fine — but flag it to the user. If your system lacks PCRE grep, fall back to: `grep -nE 'src="[^"]*"|href="[^"]*"' <path> | grep -vE '"(data:|https://|#|mailto:|tel:)'`.

4. **All `<img>` tags are base64-inlined:**
   ```bash
   grep -oE '<img[^>]*src="[^"]{0,30}' <path>
   ```
   Every match should be `<img … src="data:image/…`. Any `https://` or relative path = bug. If the page has no `<img>` tags (everything is inline SVG or CSS), the command returns nothing — that's also fine.

5. **Card-grid density check** (catches the AI-slop failure mode). Uses PCRE so it matches `grid cols-N` and `grid-cols-N` (Tailwind) regardless of class-attribute order:
   ```bash
   grep -cP 'class="[^"]*\b(grid\s+cols-|grid-cols-)' <path>
   ```
   If the count is **> 3**, the page is in card-grid-sprawl territory. Before declaring done, replace at least one card grid with an interactive (tab / toggle / click-to-expand / accordion) or merge two sections into one. This rule pairs with the interactive-minimum from Phase 2c — a page that's mostly card grids has almost certainly under-invested in interactives.

6. **Interactive-density check** (catches static-only output). PCRE again, broad enough to match: tab/tabpanel/toggle/accordion/phase with any class-modifier (e.g. `class="tab active"`), `data-comparison`/`data-tab`/`data-expand`/`data-collapse`, ARIA tab markup (`role="tab"`, `aria-selected`, `aria-expanded`), native `<details>`, slider inputs, scroll-tied JS, and hover/click node diagrams (`class="node"` with `data-id`):
   ```bash
   grep -cP 'class="(tab|tabpanel|toggle|accordion|phase|node)\b|data-(comparison|tab|expand|collapse|id)|role="tab"|aria-(selected|expanded)|<details\b|<input[^>]+type="range"|ScrollTrigger\.create' <path>
   ```
   Count of interactive markers should be **≥ ⌈N / 2⌉** where N is the centerpiece visual count from your Phase 2c inventory (you wrote it down — use that number, don't re-count from the file). If lower, the visual inventory was too static — go back and convert at least one diagram/chart into an interactive variant (a static node diagram becomes click-to-detail with `<g class="node" data-id="…">`; a static chart becomes a slider-driven chart).

   **Distribution check** (catches single-widget over-distribution — runnable, not just prose):

   Count distinct interactive widget *roots* — a tab group is 1 root, a comparison toggle is 1 root, a slider is 1 root, a click-to-expand timeline is 1 root, a click-to-detail node diagram is 1 root. Markers from one root all collapse to 1. For any page with **≥ 4 centerpieces**, this distinct-root count must be **≥ 2**. A 7-visual page where 6 are static SVG and 1 is a 5-tab inspector has 1 root and fails this check, even though the marker grep above will show 10+ tokens.

   **What "interactive" means** (this is the spirit, the greps approximate it). Reader can change state by clicking, hovering, dragging, scrolling, or toggling. Static SVG, static Mermaid, static charts are visuals but NOT interactive. Animated process loops with Play/Step/Reset controls ARE interactive. A diagram that has a hover tooltip but no click-to-change-content is NOT (the tooltip is decoration). When the grep and the spirit disagree, the spirit wins — don't farm markers to satisfy a grep that's missed the point.

If any check fails, fix and re-run before handing off.

### Handoff message

One short message — under ~80 words. Three elements only:

- Where the file is and how to open it (`xdg-open <path>` on Linux, `open <path>` on macOS, double-click on Windows).
- A brief list of what's in it — the centerpiece visuals by name (not the section list — the user already saw that in Phase 2).
- One-line offer: "Want a different palette, a different visual, or any section rewritten? Say what you'd change and I'll update."

**Worked example** — copy this shape:

> Done — `./atlas-prd.html`. Open with `xdg-open` (Linux) or `open` (macOS).
>
> **What's in it:** annotated cost-comparison chart (calls out the ~85% reduction), tabbed view per migration phase (4 tabs), click-to-expand timeline for the 6-month rollout, north-star fact strip with 4 metrics.
>
> Want a different palette, a different visual, or any section rewritten? Say what you'd change.

Mention `scripts/export-pdf.sh` only if the user said something like "send", "share with the board", "leave behind", "archive", or "PDF" — not just because the artifact looks pitch-shaped.

Don't recap section-by-section — the user just saw the outline in Phase 2.

---

## Iteration — common follow-ups

- **"Change the accent color to X."** Edit `--accent` (and `--accent-soft`, `--line` derivatives) on `:root`. The whole page follows.
- **"Swap chart for diagram."** Remove the chart's `<canvas>` + JS block, add the new visual per `visual-techniques.md`. Don't rebuild the whole page.
- **"Add a section for [thing]."** Edit the HTML directly — copy a similar section's markup, customize content, add anchor to sticky nav. Don't re-run Phase 2.
- **"Make it lighter / less dark."** Switch to the warm-light palette variant in `design-system.md`. Verify hero gradient still works at lower opacity.
- **"Translate the page."** Find/replace headings and body copy; structure stays. Don't translate technical English terms the source itself leaves in English.
- **"Different topic, same style."** Go to Phase 1 with the new source. The skill is the recipe; each output is fresh.
- **"Export to PDF."** Run `scripts/export-pdf.sh <path>` (requires Chromium or Chrome installed).

---

## Heuristics & gotchas

- **Generate the interface, not the content.** Every section asks: "what's the most visual form this can take?" before defaulting to prose.
- **Typography is the fastest exit from AI slop.** Pick a real font pair from `design-system.md`. Inter is banned unless the source explicitly mandates it.
- **OKLCH for color, never HSL or bare hex.** Perceptual lightness produces palettes that don't muddy.
- **One accent + one secondary + neutral background.** More than three accents = marketing brochure.
- **Charts must annotate.** A raw Chart.js bar chart is decoration; with the threshold called out, it's the visual. Use `chartjs-plugin-annotation`.
- **Diagrams use `viewBox`, never fixed pixel widths.** Reflow is a hard requirement at 880px.
- **Motion is purposeful.** Reveal-on-scroll = fade-up only. No spinning, no slide-from-side. GSAP scroll-tied reserved for genuinely sequenced reveals — one per page max.
- **No "Build the future" hero.** No three-card-grid summary below it. No uniform 16px-radius card sprawl. These are the AI-slop tells.
- **One visual per claim.** If a section has no claim worth visualising, it's a prose section.
- **Base64-inline every image, every time.** It's the contract with the user — DM the file, recipient sees the same thing.

---

## Reference files

- **`references/design-system.md`** — font-pair catalog, OKLCH palette rules, type scale, layout primitives, hero recipe, sticky nav, cards, buttons, fact/limit/tab/code patterns, the AI-slop avoid list. Load in Phase 2a (visual direction) and Phase 3 (theme CSS).
- **`references/interaction-patterns.md`** — catalog of 12 visual patterns (annotated chart, small multiples, comparison toggle, node diagram, sequence, process loop, slider+chart, timeline, aggregation, scroll-tied, tabs, Mermaid). When-to-use and when-NOT for each. Load in Phase 2c (visual inventory).
- **`references/visual-techniques.md`** — library decision tree (Chart.js vs D3 vs Plot, Mermaid vs inline SVG, GSAP vs CSS), CDN tags, 10-line worked examples per technique. Load in Phase 2c and Phase 3.
- **`references/image-handling.md`** — when to use raster vs SVG vs nothing, file-size targets, base64-inlining workflow, AI image-generation prompt anatomy. Load in Phase 2 if the plan calls for images and in Phase 3 when inlining.
- **`assets/base.css`** — mandatory base CSS. Inline verbatim at the top of `<style>` in Phase 3. Provides reset, reveal-on-scroll, stagger pattern, `prefers-reduced-motion` handling, `@media print` defaults.
- **`scripts/export-pdf.sh`** — zero-dependency PDF exporter (headless Chrome). Usage: `bash scripts/export-pdf.sh <page.html> [-o out.pdf]`. Requires Chromium or Google Chrome.
