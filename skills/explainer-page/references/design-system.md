# Design system

The design language for an explainer page. The default is **dark + coral on slate**; this works for almost any technical or research topic. Override the accent if the source has a strong existing palette (a corporate brand, a thesis cover color, a product identity).

The proven full CSS lives at the top of `page-template.html`. This file explains the *why* behind each block so you can edit confidently.

---

## 1. Palette

Set on `:root` and used via `var(--name)` everywhere. Edit these and the whole page follows.

```css
:root{
  /* surfaces — keep dark unless the source mandates light */
  --bg:        #0F1419;   /* page background */
  --bg-2:      #0B1016;   /* deeper inset (hero secondary) */
  --panel:     #171C24;   /* card / canvas surface */
  --panel-2:   #1E2530;   /* raised card / SVG node fill */

  /* lines & accents */
  --line:      rgba(245,138,92,.22);  /* coral, low alpha — borders & dividers */
  --coral:     #F58A5C;               /* PRIMARY accent */
  --coral-soft:#F58A5C33;             /* primary at 20% alpha — pills, tags */
  --cyan:      #5CE1E6;               /* SECONDARY — "the other side" in compares */
  --cyan-soft: #5CE1E633;
  --violet:    #A18CFF;               /* TERTIARY — third element in process loops */

  /* text */
  --text:      #E8ECF1;
  --muted:     #8C95A8;

  /* status (used sparingly) */
  --ok:        #7BD389;
  --warn:      #F2C26B;
  --err:       #E07B7B;

  /* font stacks */
  --mono: ui-monospace,"SFMono-Regular",Menlo,Monaco,Consolas,monospace;
}
```

### When to override

- **Source has a strong brand color.** Set `--coral` to it. Recalculate `--coral-soft` (same hex + `33` for ~20% alpha) and `--line` (same hex with `.22` alpha). Don't change `--cyan` unless the source uses a specific second accent.
- **Light theme.** Flip `--bg` to `#F7F8FA`, `--panel` to `#FFFFFF`, `--text` to `#0F1419`, `--muted` to `#5A6373`. Audit the hero background (the conic gradient is designed for dark) — you'll likely need to drop the gradient opacity. Avoid light theme unless explicitly requested; the design works better dark.
- **Don't introduce a fourth accent.** Stick to coral/cyan/violet. More colors → marketing-brochure look.

---

## 2. Typography

```css
body{
  font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI",
        Roboto, Helvetica, Arial, sans-serif;
}
```

System stack only — no Google Fonts, no `@font-face`. The page must work offline.

### Scale

| Element            | Rule                                            |
| ------------------ | ----------------------------------------------- |
| Hero title         | `clamp(2.2rem, 5.5vw, 4.2rem)`                  |
| Section heading    | `clamp(1.5rem, 2.6vw, 2.2rem)`                  |
| Card heading       | `1.15rem`                                       |
| Body               | `1rem` (16px)                                   |
| Lede / supporting  | `1.15rem`, color `#C9D1DE` (slightly brighter than `--text`) |
| Muted / labels     | `0.78rem`, uppercase, `letter-spacing: .12em`, color `var(--coral)` |
| Mono / code        | `0.85em`, `var(--mono)`, on dark inset `#0c1117` |

### Heading gradient

The hero title uses a coral-to-white gradient via `background-clip:text`:

```css
.hero h1.title{
  background: linear-gradient(180deg, #fff 0%, #FFD8C2 55%, var(--coral) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
```

Don't apply the gradient to section headings — keep them solid coral. The hero is the one place where extra polish earns its weight.

---

## 3. Layout primitives

```css
.wrap   { max-width: 1180px; margin: 0 auto; padding: 0 24px; }
section { padding: 96px 0; border-top: 1px solid #1a1f28; }
section:first-of-type { border-top: none; }
```

### Responsive grid

```css
.grid          { display:grid; gap:18px; }
.grid.cols-2   { grid-template-columns:repeat(2,1fr); }
.grid.cols-3   { grid-template-columns:repeat(3,1fr); }
.grid.cols-4   { grid-template-columns:repeat(4,1fr); }
@media (max-width:880px){
  .grid.cols-2, .grid.cols-3, .grid.cols-4 { grid-template-columns:1fr; }
}
```

**Single breakpoint at 880px.** Don't add more; the page is intentionally simple. Wider screens get the columns; narrower stacks everything.

### Cards

The base card carries the visual identity:

```css
.card{
  background: linear-gradient(180deg, rgba(30,37,48,.7), rgba(23,28,36,.7));
  border: 1px solid #232a36;
  border-radius: 16px;
  padding: 22px;
}
.card:hover { border-color: var(--line); }
.card .label{
  font-size:.72rem; color:var(--coral);
  letter-spacing:.12em; text-transform:uppercase; font-weight:700;
}
```

### Canvas (diagram container)

Every interactive sits inside `.canvas`. The radial-gradient halo at the top is a subtle "this is interactive" affordance.

```css
.canvas{
  border: 1px solid #232a36; border-radius: 16px;
  background:
    radial-gradient(600px 300px at 50% 0%, rgba(245,138,92,.06), transparent 70%),
    #11161e;
  padding: 18px;
}
.canvas svg { display: block; width: 100%; height: auto; }
```

---

## 4. Hero recipe

The hero is the page's first impression. The recipe:

```css
.hero{
  position:relative; overflow:hidden;
  min-height: 92vh;
  padding: 120px 0 80px;
  isolation: isolate;
}

/* animated conic-gradient blur — the "ambient light" */
.hero::before{
  content:"";
  position:absolute; inset:-20%;
  background:
    conic-gradient(from 220deg at 70% 30%,
                   rgba(245,138,92,.25), transparent 30% 70%, rgba(92,225,230,.18)),
    radial-gradient(800px 400px at 30% 80%, rgba(161,140,255,.16), transparent 60%);
  filter: blur(50px);
  animation: float 18s ease-in-out infinite alternate;
  z-index:-2;
}

/* faint grid mask — gives the hero "depth" */
.hero::after{
  content:""; position:absolute; inset:0;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at 50% 40%, black 30%, transparent 75%);
  z-index:-1;
}

@keyframes float{
  0%   { transform: translate3d(0,0,0)    scale(1);    }
  50%  { transform: translate3d(-20px,10px,0) scale(1.04); }
  100% { transform: translate3d(20px,-10px,0) scale(1);    }
}
```

**Don't speed up the float animation.** 18s is intentionally slow so it's ambient, not distracting. Anything under 10s and the reader will notice it moving.

### Scroll cue

A small pulsing line below the meta-row:

```css
.scroll-cue .line{
  width:1px; height:48px;
  background: linear-gradient(180deg, var(--coral), transparent);
  animation: cue 1.6s ease-in-out infinite;
}
@keyframes cue{
  0%,100% { opacity:.4; transform: scaleY(.6); }
  50%     { opacity:1;  transform: scaleY(1);  }
}
```

---

## 5. Sticky nav

A backdrop-blur strip that hides under itself.

```css
nav.sticky{
  position: sticky; top: 0; z-index: 50;
  backdrop-filter: blur(14px);
  background: rgba(15,20,25,.7);
  border-bottom: 1px solid #1a1f28;
}
nav.sticky ul{
  display:flex; gap:8px; flex-wrap:wrap; list-style:none;
  margin: 0 auto; padding: 10px 24px; max-width: 1180px;
}
nav.sticky a{
  color: var(--muted); padding: 6px 10px; border-radius: 8px;
  font-size: .85rem; transition: all .15s ease;
}
nav.sticky a:hover  { color:#fff; background: rgba(255,255,255,.04); }
nav.sticky a.active { color:#fff; background: var(--coral-soft); border: 1px solid var(--line); }
```

The `.active` state is driven by JS — see "Sticky nav active-state" in `page-template.html`.

---

## 6. Reveal-on-scroll

Pure progressive enhancement: works without JS, just less animated.

```css
.reveal{
  opacity: 0; transform: translateY(16px);
  transition: opacity .7s ease, transform .7s ease;
}
.reveal.in{ opacity:1; transform:none; }
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

## 7. Buttons

Primary (coral, glowing) and ghost (outlined).

```css
.btn{
  display: inline-flex; align-items: center; gap: 10px;
  padding: 11px 18px; border-radius: 12px;
  background: linear-gradient(180deg, #F89B72, #E8693E); color: #1a1108;
  font-weight: 600; border: 1px solid #c2552a;
  box-shadow: 0 6px 24px rgba(245,138,92,.35),
              inset 0 1px 0 rgba(255,255,255,.4);
  cursor: pointer; transition: transform .15s ease;
}
.btn:hover { transform: translateY(-1px); text-decoration: none; }
.btn.ghost { background: transparent; color: var(--text);
             border: 1px solid var(--line); box-shadow: none; }
```

The glow on primary buttons is what makes "primary" feel primary. Don't drop the box-shadow.

---

## 8. Specialty cards

### Fact card (key-facts strip)

```css
.fact{
  text-align:center; padding: 18px 10px;
  border: 1px solid #232a36; border-radius: 14px;
  background: linear-gradient(180deg, rgba(30,37,48,.6), rgba(23,28,36,.6));
}
.fact .n{
  font-size: 2rem; font-weight: 800; line-height: 1;
  background: linear-gradient(180deg, #fff, #F8B79A);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.fact .k{
  margin-top: 6px; font-size: .78rem; color: var(--muted);
  letter-spacing: .06em; text-transform: uppercase;
}
```

Use 5–8 facts in a single row. Less than 5 looks lonely; more than 8 wraps awkwardly.

### Limit card (problem + mitigation)

For "what doesn't work and how we work around it" sections:

```css
.limit { padding:18px; border:1px solid #232a36; border-radius:14px; background:#11161e; }
.limit .tag{
  display:inline-block; padding:2px 10px; border-radius:999px; font-size:.72rem;
  background:#3a2118; color:#FFB89A; border:1px solid #5a2f1f; margin-bottom:8px;
}
.limit .mit{
  margin-top:10px; padding:10px;
  border-left: 2px solid var(--cyan); background:#0c1117;
  font-size:.9rem; color:#C9D1DE; border-radius: 0 8px 8px 0;
}
```

The cyan left-border on the mitigation strip visually signals "this is the answer, not the problem".

---

## 9. Tabs

Minimal — no animation, no underlines.

```css
.tabs   { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:14px; }
.tab    {
  padding: 8px 14px; border: 1px solid #232a36; border-radius: 10px;
  background: #11161e; color: var(--muted); cursor: pointer;
  font-size: .88rem; font-weight: 600;
}
.tab.active { background: var(--coral); color: #1a1108; border-color: var(--coral); }
.tabpanel  { display:none; padding:18px; border:1px solid #232a36; border-radius:14px; background:#11161e; }
.tabpanel.active { display:block; }
```

---

## 10. Code & inline data

```css
code{
  font-family: var(--mono);
  background: #0c1117; border: 1px solid #1f2733;
  color: #f0d6c4; padding: 1px 6px; border-radius: 6px; font-size: .9em;
}
.mono { font-family: var(--mono); }
.pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 12px; border-radius: 999px;
  background: #0c1117; border: 1px solid #232a36;
  font-family: var(--mono); font-size: .85rem; color: #F8B79A;
}
```

---

## 11. Focus & a11y

```css
:focus-visible { outline: 2px solid var(--coral); outline-offset: 2px; border-radius: 8px; }
```

- All interactives are keyboard-reachable (buttons, sliders).
- All buttons have visible labels (no icon-only).
- The page works with `prefers-reduced-motion` — the only animations that fight this are the hero `float` and the scroll-cue pulse. If the user has `prefers-reduced-motion: reduce` in their OS, add `@media (prefers-reduced-motion: reduce) { .hero::before, .scroll-cue .line { animation: none; } }` — it's in the template.

---

## 12. What to skip

- **No box-shadow on everything.** Only primary buttons get a glow; cards stay flat.
- **No rounded everything.** 16px on cards/canvas, 12px on small elements, 999px on pills/badges. Don't introduce 24px or larger; it starts to feel "kids' app".
- **No back-to-top button.** The sticky nav serves this role.
- **No "page progress" bar at the top.** It competes visually with the sticky nav.
- **No carousel.** Scroll is the navigation; if a concept needs a carousel, it's two sections.
- **No dark/light toggle.** Pick one based on the source and ship it. A toggle requires maintaining both themes well.
