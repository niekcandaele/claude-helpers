# Design system

Load this in Phase 2 when you pick the visual direction, and again in Phase 3 when you write the theme CSS.

The job: end up with a page that looks **specific and deliberate** — like a real designer made a choice — instead of the interchangeable beige-corporate aesthetic that AI tools default to.

This file is part guidance, part reference. The patterns are battle-tested in real published pages. Deviate when the source genuinely calls for it; don't deviate to "be original."

---

## 1. What to avoid — the "AI slop" tells

If your draft has any of these, stop and rework:

- **Inter as the body font.** It's fine, but every AI-made page uses it, so it reads as "AI did this." Pick almost anything else from the catalog below. (No Inter recommendation appears in the catalog — that's deliberate.)
- **Purple-to-blue gradient backgrounds on white.** Instant tell.
- **Three-card feature grid centered below a hero with a "Build the future" headline.** The SaaS template.
- **No emoji in any user-visible text.** No emoji in headings, body, bullets, labels, buttons, or section dividers. A 🚀 anywhere on the page is the single strongest "AI did this" tell. The only exception is when the source itself uses emoji as content (a tweet, a chat log being quoted).
- **Shadow on primary buttons only.** No shadow on cards, panels, sections, hero, fact cards, or anything else — shadow is punctuation, not decoration. A page with shadows on most surfaces reads as a 2014-era SaaS template.
- **Everything centered.** Asymmetry signals intent. Full-width vertical centering looks lazy.
- **Uniform 16px border-radius on every surface.** Vary the radius (cards 16px, pills 999px, small chips 8px).
- **Placeholder-sounding copy.** "Transforming the way you work" / "Empowering teams." If it could be about anything, rewrite it.

---

## 2. Typography — pick one pair and commit

Each pair is a shorthand for a vibe. Don't mix pairs within a page. If the source's tone doesn't obviously match one, pick the closest fit and own the choice.

| Pair | Vibe | Fits sources like |
|------|------|-------------------|
| **Archivo Black + Space Grotesk** | bold editorial, confident | product launches, manifestos, pitches |
| **Fraunces + Work Sans** | literary-modern, warm | long-form arguments, design essays, narrative explainers |
| **JetBrains Mono + IBM Plex Sans** | dev/technical, lo-fi | engineering write-ups, infrastructure, internal eng docs |
| **Bodoni Moda + DM Sans** | high-contrast editorial, magazine | brand decks, case studies, portfolio reviews |
| **Plus Jakarta Sans (solo)** | approachable product, friendly | product updates, onboarding, customer success |
| **Space Grotesk + IBM Plex Mono** | techy-clean, honest | technical pitches, developer tools, API launches |
| **Cormorant Garamond + Source Serif 4** | elegant long-form, thoughtful | research, policy, philosophy-adjacent topics |
| **Syne + Space Mono** | retro-modern, playful | creative pitches, art, new-product brand work |
| **Manrope (solo)** | corporate-clean, neutral | board decks, financial updates, content-is-the-star |
| **Outfit (solo)** | playful, rounded, optimistic | consumer products, kids/education, launches |

All load from Google Fonts. Use `display=swap` to avoid FOIT. Example link:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
```

Note the Google Fonts URL uses `+` for spaces and the CSS uses the quoted real name (`"Archivo Black"`, `"Space Grotesk"`). Mismatches silently fall back to serif.

### Type scale

| Element | Rule |
|---|---|
| Hero title | `clamp(2.4rem, 5.5vw, 4.4rem)` |
| Section heading | `clamp(1.6rem, 2.6vw, 2.4rem)` |
| Card heading | `1.15rem` |
| Body | `1rem` (16px), `line-height: 1.55` |
| Lede / supporting | `1.15rem`, slightly brighter than body |
| Muted / labels | `0.78rem`, uppercase, `letter-spacing: .12em`, accent color |
| Mono / code | `0.85em`, mono stack, on dark inset |

### Hero title gradient (optional, signature move)

The hero title earns extra polish via `background-clip: text`:

```css
.hero h1 {
  background: linear-gradient(180deg, #fff 0%, #FFD8C2 55%, var(--accent) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
```

Don't apply the gradient to section headings — they stay solid. The hero is the one place where extra polish earns its weight.

---

## 3. Color — pick three, not ten

A coherent page has **three colors** that carry weight:

1. **Dominant background** — 70%+ of the visual field. Usually a deep neutral (`oklch(0.18 0.02 260)`, `oklch(0.95 0.02 80)` warm cream) or a strong brand color if the source mandates one.
2. **Primary text** — high contrast against the background. Not pure `#000` on pure `#fff` — soften one side.
3. **Accent** — one saturated color used sparingly for headlines, underlines, links, key highlights. This is the punch.

Optionally a fourth **muted** tone for hairlines and tertiary text, and a fifth **secondary accent** only for "the other side" in comparison diagrams.

### OKLCH, not HSL or bare hex

Use `oklch(L C H)` because lightness is *perceptual* — easier to pick balanced colors across a palette. Quick reference:

- Lightness: `0.18` → near-black, `0.5` → mid, `0.95` → near-white
- Chroma: `0` → gray, `0.15` → saturated, `0.3` → vivid
- Hue: `0` red, `60` yellow, `120` green, `180` cyan, `240` blue, `320` magenta

A dark + coral default that works for most technical sources:

```css
:root {
  --bg:        oklch(0.18 0.02 260);   /* deep slate */
  --bg-2:      oklch(0.14 0.02 260);   /* deeper inset */
  --panel:     oklch(0.22 0.02 260);   /* card surface */
  --text:      oklch(0.94 0.01 260);
  --muted:     oklch(0.62 0.02 260);
  --accent:    oklch(0.70 0.18 40);    /* coral */
  --accent-soft: oklch(0.70 0.18 40 / 0.20);
  --secondary: oklch(0.82 0.14 195);   /* cyan, for comparisons only */
  --line:      oklch(0.70 0.18 40 / 0.22);
}
```

A warm-light alternative for editorial sources:

```css
:root {
  --bg:        oklch(0.96 0.02 80);    /* cream */
  --bg-2:      oklch(0.92 0.02 80);
  --panel:     oklch(0.99 0.00 0);     /* white */
  --text:      oklch(0.20 0.02 260);
  --muted:     oklch(0.50 0.02 260);
  --accent:    oklch(0.55 0.20 25);    /* burnt orange */
  --accent-soft: oklch(0.55 0.20 25 / 0.15);
}
```

### Avoid

- Four-stop rainbow gradients (unless the source is *about* something maximalist).
- Blue and orange together unless intentionally doing the action-movie-poster thing.
- Low-contrast text on colored backgrounds. Check WCAG AA — many brand colors fail.
- Introducing a fourth or fifth accent. More than three accents = marketing brochure.

---

## 4. Layout primitives

```css
.wrap   { max-width: 1180px; margin: 0 auto; padding: 0 24px; }
section { padding: 96px 0; border-top: 1px solid color-mix(in oklch, var(--text) 8%, transparent); }
section:first-of-type { border-top: none; }
```

### Responsive grid

```css
.grid          { display: grid; gap: 18px; }
.grid.cols-2   { grid-template-columns: repeat(2, 1fr); }
.grid.cols-3   { grid-template-columns: repeat(3, 1fr); }
.grid.cols-4   { grid-template-columns: repeat(4, 1fr); }
@media (max-width: 880px) {
  .grid.cols-2, .grid.cols-3, .grid.cols-4 { grid-template-columns: 1fr; }
}
```

**Single breakpoint at 880px.** Don't add more; pages are intentionally simple. Wider screens get columns; narrower stacks everything.

### Vary the density

Don't make every section a card grid. Alternate:

- **Card grids** for lists of equal-weight items (features, principles, team)
- **Full-width canvases** for centerpiece interactives (charts, diagrams, comparisons)
- **Plain prose blocks** for narrative, conclusions, the problem statement
- **Two-column splits** for image-and-text pairs

A page that's six card grids stacked is dead. Mix at least three section shapes.

### Cards

```css
.card {
  background: linear-gradient(180deg,
    color-mix(in oklch, var(--panel) 95%, transparent),
    color-mix(in oklch, var(--bg) 95%, transparent));
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  border-radius: 16px;
  padding: 22px;
}
.card:hover { border-color: var(--line); }
.card .label {
  font-size: .72rem; color: var(--accent);
  letter-spacing: .12em; text-transform: uppercase; font-weight: 700;
}
```

### Canvas (interactive/diagram container)

Every centerpiece interactive sits inside `.canvas`. The radial-gradient halo at the top is a subtle "this is interactive" affordance.

```css
.canvas {
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  border-radius: 16px;
  background:
    radial-gradient(600px 300px at 50% 0%,
      color-mix(in oklch, var(--accent) 8%, transparent), transparent 70%),
    var(--panel);
  padding: 18px;
}
.canvas svg, .canvas canvas { display: block; width: 100%; height: auto; }
```

---

## 5. Hero recipe

The hero is the page's first impression. The recipe (dark-theme variant — adapt for light):

```css
.hero {
  position: relative; overflow: hidden;
  min-height: 92vh;
  padding: 120px 0 80px;
  isolation: isolate;
}

/* animated conic-gradient blur — ambient light */
.hero::before {
  content: ""; position: absolute; inset: -20%;
  background:
    conic-gradient(from 220deg at 70% 30%,
                   color-mix(in oklch, var(--accent) 25%, transparent),
                   transparent 30% 70%,
                   color-mix(in oklch, var(--secondary) 18%, transparent)),
    radial-gradient(800px 400px at 30% 80%,
                    color-mix(in oklch, var(--accent) 16%, transparent), transparent 60%);
  filter: blur(50px);
  animation: float 18s ease-in-out infinite alternate;
  z-index: -2;
}

/* faint grid mask — gives depth */
.hero::after {
  content: ""; position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 48px 48px;
  /* Both prefixed and unprefixed for Safari parity. */
  -webkit-mask-image: radial-gradient(ellipse at 50% 40%, black 30%, transparent 75%);
          mask-image: radial-gradient(ellipse at 50% 40%, black 30%, transparent 75%);
  z-index: -1;
}

@keyframes float {
  0%   { transform: translate3d(0,0,0) scale(1); }
  50%  { transform: translate3d(-20px,10px,0) scale(1.04); }
  100% { transform: translate3d(20px,-10px,0) scale(1); }
}
```

**Don't speed up the float.** 18s is intentionally slow so it reads as ambient, not distracting. Under 10s and the reader notices it moving.

---

## 6. Sticky nav

```css
nav.sticky {
  position: sticky; top: 0; z-index: 50;
  backdrop-filter: blur(14px);
  background: color-mix(in oklch, var(--bg) 70%, transparent);
  border-bottom: 1px solid color-mix(in oklch, var(--text) 8%, transparent);
}
nav.sticky ul {
  display: flex; gap: 8px; flex-wrap: wrap; list-style: none;
  margin: 0 auto; padding: 10px 24px; max-width: 1180px;
}
nav.sticky a {
  color: var(--muted); padding: 6px 10px; border-radius: 8px;
  font-size: .85rem; transition: all .15s ease; text-decoration: none;
}
nav.sticky a:hover  { color: var(--text); background: color-mix(in oklch, var(--text) 4%, transparent); }
nav.sticky a.active { color: var(--text); background: var(--accent-soft); border: 1px solid var(--line); }
```

Drive `.active` from scroll position vs `section.offsetTop` with a 120px lead. Pattern in `base.css`.

---

## 7. Reveal-on-scroll

Pure progressive enhancement: works without JS, just less animated.

```css
.reveal {
  opacity: 0; transform: translateY(16px);
  transition: opacity .7s ease, transform .7s ease;
}
.reveal.in { opacity: 1; transform: none; }

@media (prefers-reduced-motion: reduce) {
  .reveal { opacity: 1; transform: none; transition: none; }
}
```

```js
const io = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }
}, { threshold: .12 });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));
```

**Fade-up only.** No slide-from-side, no rotation, no scale-in. Multiple animation types in one page feel chaotic.

---

## 8. Motion discipline

- **One entrance motion per section.** Fade-up via `.reveal`. Don't mix types.
- **Stagger lists.** Bullets reveal 80–120ms apart. Pattern in `base.css`. Don't go above 6 children.
- **No looping animations.** No pulsing dots, no sweeping shimmers — they steal attention.
- **GSAP/Motion One scroll-tied reserved for genuine sequence reveals** (a multi-step explanation that benefits from progressive disclosure). One per page max.
- **Honor `prefers-reduced-motion`.** Base CSS handles it; don't override.

---

## 9. Buttons

```css
.btn {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 11px 18px; border-radius: 12px;
  background: linear-gradient(180deg,
    color-mix(in oklch, var(--accent) 90%, white),
    var(--accent));
  color: oklch(0.15 0.02 30);
  font-weight: 600; border: 1px solid color-mix(in oklch, var(--accent) 80%, black);
  box-shadow: 0 6px 24px color-mix(in oklch, var(--accent) 35%, transparent),
              inset 0 1px 0 rgba(255,255,255,.4);
  cursor: pointer; transition: transform .15s ease; text-decoration: none;
}
.btn:hover { transform: translateY(-1px); }
.btn.ghost {
  background: transparent; color: var(--text);
  border: 1px solid var(--line); box-shadow: none;
}
```

The glow on primary buttons is what makes "primary" feel primary. Don't drop the box-shadow.

---

## 10. Specialty cards

### Fact card (key-facts strip — 5–8 numbers across the top)

```css
.fact {
  text-align: center; padding: 18px 10px;
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  border-radius: 14px;
  background: color-mix(in oklch, var(--panel) 60%, transparent);
}
.fact .n {
  font-size: 2rem; font-weight: 800; line-height: 1;
  background: linear-gradient(180deg, var(--text), var(--accent));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.fact .k {
  margin-top: 6px; font-size: .78rem; color: var(--muted);
  letter-spacing: .06em; text-transform: uppercase;
}
```

Use 5–8 facts in a single row. Less than 5 looks lonely; more than 8 wraps awkwardly.

### Limit card (problem + mitigation)

For "what doesn't work" sections:

```css
.limit { padding: 18px; border: 1px solid color-mix(in oklch, var(--text) 10%, transparent); border-radius: 14px; }
.limit .tag {
  display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .72rem;
  background: color-mix(in oklch, var(--accent) 15%, transparent);
  color: var(--accent); border: 1px solid var(--line); margin-bottom: 8px;
}
.limit .mit {
  margin-top: 10px; padding: 10px;
  border-left: 2px solid var(--secondary);
  background: color-mix(in oklch, var(--bg-2) 70%, transparent);
  font-size: .9rem; border-radius: 0 8px 8px 0;
}
```

The cyan left-border signals "this is the answer, not the problem."

---

## 11. Tabs

Minimal — no animation, no underlines.

```css
.tabs    { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
.tab     { padding: 8px 14px; border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
           border-radius: 10px; background: var(--panel); color: var(--muted);
           cursor: pointer; font-size: .88rem; font-weight: 600; }
.tab.active { background: var(--accent); color: oklch(0.15 0.02 30); border-color: var(--accent); }
.tabpanel       { display: none; padding: 18px; border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
                  border-radius: 14px; background: var(--panel); }
.tabpanel.active { display: block; }
```

---

## 12. Code & inline data

```css
code {
  font-family: var(--font-mono, ui-monospace, "SFMono-Regular", Menlo, monospace);
  background: var(--bg-2); border: 1px solid color-mix(in oklch, var(--text) 12%, transparent);
  color: color-mix(in oklch, var(--accent) 80%, white);
  padding: 1px 6px; border-radius: 6px; font-size: .9em;
}
.mono { font-family: var(--font-mono); }
.pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 12px; border-radius: 999px;
  background: var(--bg-2); border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
  font-family: var(--font-mono); font-size: .85rem; color: color-mix(in oklch, var(--accent) 80%, white);
}
```

---

## 13. Focus & a11y

```css
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 8px; }
```

- All interactives are keyboard-reachable (buttons, sliders, tabs).
- All buttons have visible text labels (no icon-only).
- Honor `prefers-reduced-motion`. Hero `float` and any GSAP scroll-tied animation must be guarded:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .hero::before { animation: none; }
  }
  ```
- Color contrast: text against background must clear WCAG AA (4.5:1 normal, 3:1 large).

---

## 14. Copy heuristics

- **Headlines are claims, not labels.** `"Our users trust us"` is a label. `"92% ship faster after week one"` is a claim.
- **First word of bullets carries weight** — verb or noun, not a conjunction. If every bullet starts with "The" or "We", rewrite.
- **No trailing periods on bullets or headlines.** They read better without.
- **Cut adverbs first.** "Really fast", "very scalable" — delete "really" and "very".
- **Mirror the source's language.** If the source is in Dutch, the page is in Dutch. Technical terms stay in their original language.

---

## 15. What to skip

- **No box-shadow on everything.** Only primary buttons get glow.
- **No rounded everything.** 16px on cards, 12px on small elements, 999px on pills.
- **No back-to-top button.** Sticky nav serves this role.
- **No "page progress" bar at the top.** Competes with sticky nav.
- **No carousel.** Scroll is the navigation; if a concept needs a carousel, it's two sections.
- **No dark/light toggle.** Pick one based on the source and ship it.

---

## 16. Self-check before handoff

- [ ] Page uses one font pair (no surprise fonts in CSS).
- [ ] At most three colors carry weight. Accent is used, not shouted.
- [ ] Section shapes vary across the page — no stretch of 3+ identical layouts.
- [ ] Every centerpiece visual carries a real conceptual claim, not decoration.
- [ ] Every image is base64-inlined; no external `<img src="…">` references.
- [ ] Copy doesn't contain placeholder phrases or empty marketing verbs.
- [ ] Page renders identically after `cp page.html /tmp/copy.html && xdg-open /tmp/copy.html`.
