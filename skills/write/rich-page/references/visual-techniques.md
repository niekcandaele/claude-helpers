# Visual techniques

Load this in Phase 2 when you're choosing *how* to render each centerpiece visual, and in Phase 3 when you're wiring CDN libraries into `<head>`.

This file is a decision tree: given the shape of what you're trying to show, which technique reaches for it most efficiently? Plus the CDN snippets to drop in and 10-line worked examples for each.

The asset policy: **CDN libraries are allowed** (they're stable, don't carry user-specific data, and the recipient's browser already caches them). The deal is the page renders identically when DM'd to someone else — that means images are base64-inlined (see `image-handling.md`), but CSS/JS frameworks load from jsdelivr/unpkg/cdnjs and that's fine.

---

## Library decision tree

| You're showing… | Use | Why |
|---|---|---|
| A few bars/lines with annotations | **Chart.js** | Easiest API; reliable defaults; built-in tooltips |
| Small multiples / facets | **Observable Plot** | Declarative grammar; auto-faceting in one line |
| A bespoke custom chart | **D3** | Full control; needed when Chart.js can't express the geometry |
| Sequence diagram, flowchart, state machine, ER | **Mermaid** | Text → SVG; readable source; pages stay editable |
| Architecture or node-and-edge diagram | **inline SVG** | Custom node shapes, click-to-detail, no library overhead |
| Process loop / animated walkthrough | **inline SVG + vanilla JS** | Bespoke timing/script; libraries add weight without value |
| Sliders that update a chart | **vanilla JS + Chart.js** | `chart.data = …; chart.update()` is one line |
| Tab/toggle UI | **vanilla JS** | 6 lines; no library needed |
| Comparison toggle (slider that changes both sides) | **vanilla JS** | Same — no library needed |
| Scroll-tied animation (sequence reveal, morphing) | **GSAP ScrollTrigger** | The only technique that does this well |
| Simple reveal-on-scroll | **IntersectionObserver** | Native; pattern in `assets/base.css` |
| Icons | **Lucide** | Comprehensive, consistent, CDN-loadable, accessible |
| Utility-first styling | **Tailwind via CDN** | Optional — only if you'd otherwise write 200+ lines of utility CSS |
| 3D scene | **Three.js** | Rarely needed; only when the topic genuinely warrants 3D |
| Generative / creative coding | **p5.js** | For sketches, simulations, particle systems |

---

## Chart.js — the default chart library

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.1.0/dist/chartjs-plugin-annotation.min.js"></script>
```

The `annotation` plugin is non-optional — see "Charts must annotate" below.

**Worked example:**

```html
<canvas id="latency-chart" style="max-height: 360px;"></canvas>
<script>
const ctx = document.getElementById('latency-chart');
Chart.register(window['chartjs-plugin-annotation']);
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['p50', 'p75', 'p90', 'p95', 'p99'],
    datasets: [{
      data: [42, 68, 110, 180, 340],
      backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--accent'),
      borderRadius: 6,
    }],
  },
  options: {
    plugins: {
      legend: { display: false },
      annotation: {
        annotations: {
          slo: {
            type: 'line', yMin: 200, yMax: 200,
            borderColor: getComputedStyle(document.documentElement).getPropertyValue('--secondary'),
            borderWidth: 2, borderDash: [6, 6],
            label: { content: '200ms SLO', display: true, position: 'end' },
          },
        },
      },
    },
    scales: {
      y: { beginAtZero: true, title: { display: true, text: 'milliseconds' } },
    },
  },
});
</script>
```

**Style notes:**
- Pull colors from CSS custom properties so the chart inherits the page theme.
- Set `borderRadius: 6` on bars to match the page's rounded vibe.
- Hide the legend when there's one dataset (`legend: { display: false }`); show it for ≥2.
- Annotate the threshold or key value — see below.

### Charts must annotate

A raw Chart.js bar chart is decoration. The same chart with the threshold called out, the spike labeled, the SLO drawn as a dashed line — that's the visual. Always reach for the `annotation` plugin and mark *the thing worth noticing*. If you can't name what's worth noticing, the chart isn't earning its place; rewrite as prose.

---

## Observable Plot — when you need small multiples

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6"></script>
```

**Worked example — facets:**

```html
<div id="multiples"></div>
<script>
const data = [/* {region, week, value}, … */];
const plot = Plot.plot({
  height: 320,
  fy: { label: null },
  marks: [
    Plot.lineY(data, { x: "week", y: "value", fy: "region", stroke: "var(--accent)" }),
    Plot.dotY(data, { x: "week", y: "value", fy: "region", fill: "var(--accent)", r: 2 }),
  ],
});
document.getElementById('multiples').append(plot);
</script>
```

Use when one chart isn't enough — you want N similar charts, one per category, to let the reader scan across. Plot does this in one `fy:` line; Chart.js would require N canvases.

---

## D3 — only when nothing else fits

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
```

Reach for D3 when:
- The geometry is bespoke (a beeswarm, a Sankey, a custom force-directed graph)
- You need fine control over enter/update/exit transitions
- The visual *is* the page (one big custom diagram, not a chart-among-many)

Otherwise Chart.js or Plot will get you there faster. D3 is powerful but verbose; budget more lines and more debugging time.

---

## Mermaid — for sequence/flow/state/ER diagrams

**CDN:**

```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  // Wait until CSS custom properties are applied — getComputedStyle at
  // ESM-import time can return empty strings before the stylesheet parses,
  // and Mermaid will throw on empty theme values.
  window.addEventListener('DOMContentLoaded', () => {
    const css = getComputedStyle(document.documentElement);
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      themeVariables: {
        primaryColor:       css.getPropertyValue('--panel').trim()  || '#1a1f2b',
        primaryTextColor:   css.getPropertyValue('--text').trim()   || '#e8ecf1',
        primaryBorderColor: css.getPropertyValue('--accent').trim() || '#f58a5c',
        lineColor:          css.getPropertyValue('--accent').trim() || '#f58a5c',
        fontFamily:         css.getPropertyValue('--font-sans').trim() || 'system-ui',
      },
    });
    mermaid.run();
  });
</script>
```

Note: `startOnLoad: false` is deliberate. With `startOnLoad: true`, Mermaid would render once at script-evaluation time (before CSS custom properties are applied — diagrams come out with Mermaid's default purple-on-grey theme) and then again when our handler fires (now themed correctly). That double-render produces a visible flash of un-themed diagrams. Setting `startOnLoad: false` means our `mermaid.run()` is the only render call, and it always uses the resolved theme.

**Worked example — sequence diagram:**

```html
<div class="mermaid">
sequenceDiagram
    participant C as Client
    participant API as API
    participant DB as Postgres
    C->>API: POST /orders
    API->>DB: INSERT order
    DB-->>API: order_id
    API-->>C: 201 Created
</div>
```

**When Mermaid wins:** the diagram is textually describable. Sequences, simple flowcharts, state machines, ER, gantt — all are one terse code block. The page stays readable in source form.

**When inline SVG wins:** custom node shapes, click-to-detail interactions, anything where you want to escape Mermaid's defaults.

---

## Custom HTML sequence — when Mermaid isn't enough

Sometimes you want a sequence diagram with specific styling, clickable payloads, or tight pixel control that Mermaid won't give you. Hand-roll it with CSS Grid:

```html
<style>
  .seq { display: grid; grid-template-columns: 1fr auto 1fr; gap: 8px 16px;
         align-items: center; padding: 18px; }
  .seq .col-h { font-weight: 700; text-transform: uppercase; letter-spacing: .12em;
                font-size: .78rem; color: var(--accent); text-align: center; padding-bottom: 8px; }
  .seq .arrow { font-family: var(--font-mono); color: var(--accent); text-align: center; }
  .seq .arrow.l-to-r::after { content: " →"; }
  .seq .arrow.r-to-l::before { content: "← "; }
  .seq .label { font-family: var(--font-mono); font-size: .85rem;
                padding: 6px 10px; border-radius: 8px; background: var(--bg-2);
                border: 1px solid var(--line); cursor: pointer; }
  .seq .label[aria-expanded="true"] + .seq-payload { display: block; }
  .seq-payload { display: none; grid-column: 1 / -1; padding: 10px;
                 background: var(--bg-2); border-radius: 8px; margin: 0 0 8px;
                 font-family: var(--font-mono); font-size: .82rem; white-space: pre; overflow-x: auto; }
</style>
<div class="seq">
  <div class="col-h">Client</div><div></div><div class="col-h">Server</div>
  <div class="label" data-payload="0">CONNECT</div>
  <div class="arrow l-to-r"></div>
  <div></div>
  <pre class="seq-payload">CONNECT host=example.com port=5432
user=alice ssl=require</pre>
  <!-- … more rows … -->
</div>
<script>
document.querySelectorAll('.seq .label').forEach(el => {
  el.addEventListener('click', () => {
    const open = el.getAttribute('aria-expanded') === 'true';
    el.setAttribute('aria-expanded', String(!open));
  });
});
</script>
```

**When this wins over Mermaid:**
- Payloads are part of the lesson (Mermaid notes are cramped).
- You want bidirectional arrow rows that don't all start from the left.
- The diagram is going to be more than 6 rows and Mermaid's auto-layout starts producing awkward gaps.

---

## Inline SVG — for bespoke node/architecture diagrams

When you need a diagram with custom shapes, click-for-detail, or specific positioning, write the SVG by hand:

```html
<svg viewBox="0 0 800 400" preserveAspectRatio="xMidYMid meet" class="arch-diagram">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0,0 L10,5 L0,10 Z" fill="var(--accent)" />
    </marker>
  </defs>
  <g class="node" data-id="api">
    <rect x="50" y="160" width="160" height="80" rx="12" fill="var(--panel)" stroke="var(--line)" />
    <text x="130" y="205" text-anchor="middle" fill="var(--text)" font-weight="600">API</text>
  </g>
  <!-- more nodes … -->
  <line x1="210" y1="200" x2="290" y2="200" stroke="var(--accent)" stroke-width="2" marker-end="url(#arrow)" />
</svg>
<script>
  document.querySelectorAll('.arch-diagram .node').forEach(n => {
    n.style.cursor = 'pointer';
    n.addEventListener('click', () => {
      document.getElementById('detail').textContent = `Selected: ${n.dataset.id}`;
    });
  });
</script>
```

**Rules:**
- Always `viewBox` + `preserveAspectRatio` — never fixed pixel widths. The diagram must reflow at 880px.
- Position nodes on a coarse grid. Fancy radial/organic layouts in handwritten SVG are a trap.
- Pull stroke/fill colors from CSS custom properties so the diagram inherits the theme.
- Wrap each clickable group in `<g class="node" data-id="…">` so JS can wire interactions cleanly.

---

## GSAP — for scroll-tied animation only

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/ScrollTrigger.min.js"></script>
```

**Worked example — pin a section while a sequence reveals:**

```html
<section id="story" style="height: 300vh;">
  <div class="pinned">
    <h2>How a request flows through the system</h2>
    <div class="step" data-step="1">1. Client sends HTTPS request</div>
    <div class="step" data-step="2">2. Load balancer routes to worker</div>
    <div class="step" data-step="3">3. Worker hits cache, then DB</div>
    <div class="step" data-step="4">4. Response streams back</div>
  </div>
</section>
<script>
gsap.registerPlugin(ScrollTrigger);
const steps = gsap.utils.toArray('#story .step');
gsap.set(steps, { opacity: 0.2 });
ScrollTrigger.create({
  trigger: '#story',
  start: 'top top',
  end: 'bottom bottom',
  scrub: true,
  pin: '#story .pinned',
  onUpdate: (self) => {
    const i = Math.floor(self.progress * steps.length);
    steps.forEach((s, idx) => s.style.opacity = idx <= i ? 1 : 0.2);
  },
});
</script>
```

**When this earns its weight:** the topic is *genuinely sequential* and progressive disclosure adds real understanding. Walking a packet through a stack. Showing how a function's state evolves. The history of something step-by-step.

**One per page max.** Scroll-tied animation is heavy on reader attention. Two on a page and they overload.

**Always honor reduced-motion:**

```js
if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
  steps.forEach(s => s.style.opacity = 1);
} else {
  /* GSAP setup */
}
```

---

## Lucide — for icons

**CDN:**

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
```

**Use:**

```html
<i data-lucide="zap"></i> Fast queries
<i data-lucide="shield-check"></i> Safe by default

<script>lucide.createIcons();</script>
```

Lucide has ~1,500 line-style icons. Consistent stroke width, accessible, easy to style via CSS (`stroke="var(--accent)"`). Don't use raster icon fonts (FontAwesome via CDN, etc.) — they're heavier and the rendering is worse.

---

## Tailwind via CDN — optional

**CDN:**

```html
<script src="https://cdn.tailwindcss.com"></script>
```

**When this is worth it:** the page has a lot of variation in layout — many one-off `flex`/`grid` combinations, dozens of utility-style adjustments. Tailwind saves you from writing repetitive CSS.

**When it isn't:** the page has 8–12 sections that share a consistent design system (which is the common case). Then write CSS once with custom properties and skip Tailwind — your CSS will be smaller than Tailwind's tree-shaken output and the source will be more readable.

Default: skip Tailwind unless you catch yourself writing the same `style="display: flex; align-items: center; gap: 12px;"` for the fifth time.

If you do use Tailwind, set the theme to inherit from your CSS custom properties so the palette stays consistent:

```html
<script>
tailwind.config = {
  theme: {
    extend: {
      colors: {
        accent: 'var(--accent)',
        bg: 'var(--bg)',
        muted: 'var(--muted)',
      },
    },
  },
};
</script>
```

---

## Less common — only when truly needed

### Three.js (3D)

```html
<script type="module">
  import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.module.js';
</script>
```

For genuinely-3D topics (planetary orbits, molecular structure, architectural massing). Not for "make a card pop up." File size and rendering cost are high; budget one Three.js scene per page.

### p5.js (creative coding)

```html
<script src="https://cdn.jsdelivr.net/npm/p5@1.11.2/lib/p5.min.js"></script>
```

For generative sketches, simulations (Conway's Life, flocking, cellular automata), particle systems used as ambient illustration. Pair with a "Restart" button so the reader can re-trigger.

### Vega-Lite (declarative dashboards)

```html
<script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
```

When you need many small declarative charts driven by a shared dataset (a dashboard-style section). Heavier than Plot but more expressive.

---

## Picking the smallest set

Each CDN you add is more weight on the page and more cognitive load on you while building. Pick the smallest set that does the job:

- A page with two bar charts and a sequence diagram = **Chart.js + Mermaid** (two libs).
- A page with a custom architecture diagram and a slider that updates it = **inline SVG + vanilla JS** (zero libs).
- A page with a 4-step scroll-tied walkthrough = **GSAP** (one lib).

If you find yourself wanting 5+ libraries on one page, the page is doing too much. Cut the visual inventory back to the 4–7 centerpiece rule.

---

## Loading-order gotchas

- **GSAP plugins** (`ScrollTrigger`) must load *after* the GSAP core in the `<head>`.
- **Mermaid** uses ESM (`type="module"`) — don't load it alongside non-module scripts that depend on it.
- **Tailwind via CDN** is a runtime JIT compiler — slow on first paint. Don't use for above-the-fold styling; let custom CSS handle the hero.
- **Lucide** needs `lucide.createIcons()` to run *after* `<i data-lucide>` elements are in the DOM. Put the script tag at the bottom of `<body>` or wrap in `DOMContentLoaded`.
- **Pulling CSS custom properties** in JS (`getComputedStyle(document.documentElement).getPropertyValue('--accent')`) returns a string with leading whitespace — `.trim()` it before passing to Chart.js / Mermaid configs.
