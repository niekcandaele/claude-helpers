# HTML template reference

Load this file when you reach Phase 3 (building the final HTML).

The deck is a **single self-contained HTML file**. No external JS libraries. No build step. It must open on any modern browser from a file:// URL and work offline.

## Top-level skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{{DECK_TITLE}}</title>

  <!-- Google Fonts — swap for the pair you picked in design-heuristics.md -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family={{DISPLAY_FONT}}&family={{BODY_FONT}}&display=swap" rel="stylesheet" />

  <style>
    /* ============================================================
       BASE — paste the ENTIRE contents of assets/viewport-base.css
       here verbatim. Do not edit it. Do not inline-compress it.
       ============================================================ */
    /* (viewport-base.css goes here) */

    /* ============================================================
       THEME — style-specific rules. Define CSS custom properties
       first so the base picks them up, then add per-slide layouts.
       ============================================================ */
    :root {
      --color-bg:     /* dominant background */;
      --color-text:   /* primary text color */;
      --color-accent: /* single strong accent */;
      --color-muted:  /* tertiary text / hairlines */;
      --font-display: '{{DISPLAY_FONT_NAME}}', serif;  /* or sans */
      --font-body:    '{{BODY_FONT_NAME}}', sans-serif;
    }

    /* Per-slide-type layout variations go here (see snippets below). */
  </style>
</head>
<body>
  <div class="deck-progress" aria-hidden="true"><div class="fill"></div></div>

  <main class="slides">
    <!-- SLIDE 1 — title -->
    <section class="slide slide--title" id="s1">...</section>

    <!-- SLIDE 2 — content -->
    <section class="slide slide--content" id="s2">...</section>

    <!-- etc -->
  </main>

  <script>
    /* SlidePresentation class — see below. Paste verbatim. */
  </script>
</body>
</html>
```

## Per-slide-type snippets

All slides use `<section class="slide slide--{TYPE}">` so theme CSS can target each type. Wrap reveal elements in `.reveal` (or `.stagger` for lists) so the IntersectionObserver animates them.

### Title slide

```html
<section class="slide slide--title" id="s1">
  <div class="reveal">
    <p class="eyebrow">{{EYEBROW}}</p>
    <h1>{{TITLE}}</h1>
    <p class="subtitle">{{SUBTITLE}}</p>
    <p class="byline">{{AUTHOR}} &middot; {{DATE}}</p>
  </div>
</section>
```

### Content slide (headline + bullets)

```html
<section class="slide slide--content" id="s2">
  <h2 class="reveal">{{HEADLINE}}</h2>
  <ul class="stagger">
    <li>{{POINT_1}}</li>
    <li>{{POINT_2}}</li>
    <li>{{POINT_3}}</li>
  </ul>
</section>
```

Cap bullets at **6 per slide**. If you have more, split into two slides.

### Image-led slide (hero image + short caption)

```html
<section class="slide slide--image" id="s3">
  <figure class="reveal">
    <img src="images/image_1.png" alt="{{ALT_TEXT}}" />
    <figcaption>{{CAPTION}}</figcaption>
  </figure>
</section>
```

`{{ALT_TEXT}}` must describe the image — use the same noun phrase that anchored the image prompt, not "illustration" or "figure".

### Split slide (image left, content right)

```html
<section class="slide slide--split" id="s4">
  <div class="split__media reveal">
    <img src="images/image_2.png" alt="{{ALT_TEXT}}" />
  </div>
  <div class="split__body">
    <h2 class="reveal">{{HEADLINE}}</h2>
    <ul class="stagger">
      <li>{{POINT_1}}</li>
      <li>{{POINT_2}}</li>
    </ul>
  </div>
</section>
```

Theme CSS must set `.slide--split { flex-direction: row; gap: 3rem; }`. Any responsive stacking for narrow screens must be scoped to `screen` so it doesn't leak into print — e.g. `@media screen and (max-width: 800px) { .slide--split { flex-direction: column; } }`. An unscoped `@media (max-width: 800px)` will fire during PDF export and break split/image-led slides (see gotcha #9 below).

### Quote slide

```html
<section class="slide slide--quote" id="s5">
  <blockquote class="reveal">
    <p>&ldquo;{{QUOTE}}&rdquo;</p>
    <cite>&mdash; {{ATTRIBUTION}}</cite>
  </blockquote>
</section>
```

Use sparingly — one quote per deck max is usually right.

### Section divider

```html
<section class="slide slide--divider" id="s6">
  <div class="reveal">
    <p class="section-number">Part {{N}}</p>
    <h2>{{SECTION_TITLE}}</h2>
  </div>
</section>
```

Dividers are a great place for an atmospheric background image (CSS `background-image` on the section), not a foreground `<img>`.

### Data / stats slide

```html
<section class="slide slide--stats" id="s7">
  <h2 class="reveal">{{HEADLINE}}</h2>
  <div class="stats stagger">
    <div class="stat">
      <strong class="stat__value">{{NUMBER}}</strong>
      <span class="stat__label">{{LABEL}}</span>
    </div>
    <!-- up to 3 stat blocks -->
  </div>
</section>
```

### Closer slide

```html
<section class="slide slide--closer" id="sN">
  <div class="reveal">
    <h2>{{CALL_TO_ACTION}}</h2>
    <p class="contact">{{CONTACT_INFO}}</p>
  </div>
</section>
```

## JavaScript controller — paste verbatim

The controller is ~90 lines of vanilla JS. No dependencies. Drop it at the end of `<body>`.

```html
<script>
  class SlidePresentation {
    constructor() {
      this.slides = Array.from(document.querySelectorAll('section.slide'));
      this.progressFill = document.querySelector('.deck-progress .fill');
      this.current = 0;
      this.buildNav();
      this.bindKeyboard();
      this.bindTouch();
      this.bindWheel();
      this.bindScroll();
      this.observeReveal();
    }

    buildNav() {
      const nav = document.createElement('nav');
      nav.className = 'deck-nav';
      nav.setAttribute('aria-label', 'Slide navigation');
      // Build all dots in a fragment, then drop them in as a single
      // atomic update. Using replaceChildren() with the freshly built
      // buttons means re-renders never double up dots.
      const frag = document.createDocumentFragment();
      this.slides.forEach((slide, i) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.setAttribute('aria-label', `Go to slide ${i + 1}`);
        btn.addEventListener('click', () => this.goTo(i));
        frag.appendChild(btn);
      });
      nav.replaceChildren(frag);
      document.body.appendChild(nav);
      this.navButtons = Array.from(nav.querySelectorAll('button'));
      this.updateNav();
    }

    updateNav() {
      this.navButtons.forEach((btn, i) => {
        if (i === this.current) btn.setAttribute('aria-current', 'true');
        else btn.removeAttribute('aria-current');
      });
    }

    goTo(index) {
      const clamped = Math.max(0, Math.min(this.slides.length - 1, index));
      this.slides[clamped].scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    bindKeyboard() {
      window.addEventListener('keydown', (e) => {
        const forward = ['ArrowRight', 'ArrowDown', 'PageDown', ' '];
        const back = ['ArrowLeft', 'ArrowUp', 'PageUp'];
        if (forward.includes(e.key)) { e.preventDefault(); this.goTo(this.current + 1); }
        else if (back.includes(e.key)) { e.preventDefault(); this.goTo(this.current - 1); }
        else if (e.key === 'Home') { e.preventDefault(); this.goTo(0); }
        else if (e.key === 'End') { e.preventDefault(); this.goTo(this.slides.length - 1); }
      });
    }

    bindTouch() {
      let startY = 0;
      window.addEventListener('touchstart', (e) => { startY = e.touches[0].clientY; }, { passive: true });
      window.addEventListener('touchend', (e) => {
        const dy = e.changedTouches[0].clientY - startY;
        if (Math.abs(dy) < 50) return;
        this.goTo(this.current + (dy < 0 ? 1 : -1));
      }, { passive: true });
    }

    bindWheel() {
      // Debounce wheel events — trackpads fire many small deltas per
      // gesture; without a lockout, one swipe advances multiple slides.
      let locked = false;
      window.addEventListener('wheel', (e) => {
        if (locked) return;
        if (Math.abs(e.deltaY) < 30) return;
        locked = true;
        this.goTo(this.current + (e.deltaY > 0 ? 1 : -1));
        setTimeout(() => { locked = false; }, 700);
      }, { passive: true });
    }

    bindScroll() {
      const updateProgress = () => {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
        if (this.progressFill) this.progressFill.style.width = `${pct}%`;
        // Find which slide is most visible
        let best = 0, bestRatio = 0;
        this.slides.forEach((slide, i) => {
          const rect = slide.getBoundingClientRect();
          const ratio = Math.max(0, Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0)) / window.innerHeight;
          if (ratio > bestRatio) { bestRatio = ratio; best = i; }
        });
        if (best !== this.current) { this.current = best; this.updateNav(); }
      };
      window.addEventListener('scroll', updateProgress, { passive: true });
      updateProgress();
    }

    observeReveal() {
      const io = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('visible');
        });
      }, { threshold: 0.3 });
      this.slides.forEach((s) => io.observe(s));
    }
  }

  document.addEventListener('DOMContentLoaded', () => new SlidePresentation());
</script>
```

## Gotchas — read before you ship

1. **Negated CSS functions silently fail.** `margin-left: -clamp(1rem, 2vw, 2rem)` produces nothing. Write `margin-left: calc(-1 * clamp(1rem, 2vw, 2rem))` instead. Same trap with `-min()` / `-max()`.

2. **`scroll-snap-type` must be on `<html>`, not `<body>`.** Putting it on body creates a second scrolling container and snap stops working on iOS.

3. **Google Fonts CSS name ≠ CSS `font-family` value.** The URL param uses `+` for spaces (`Space+Grotesk`), but the CSS needs quotes and real spaces (`font-family: 'Space Grotesk'`). Getting this wrong gives you silent fallback to `serif`.

4. **`100vh` on iOS Safari includes URL bar reserves.** Use both `100vh` and `100dvh` (dynamic viewport height). The base CSS does this already — don't override with just `100vh`.

5. **Images must use relative paths.** `src="images/image_1.png"` works when the user double-clicks the HTML. Absolute filesystem paths break on everyone else's machine.

6. **Don't set `overflow: auto` on a slide.** It breaks the no-scroll-within-slide contract. If content doesn't fit, split the slide.

7. **Reveal animations need `.reveal` or `.stagger` — no implicit wrapping.** The base CSS only animates elements with those classes. Forgotten wrappers are the #1 reason a slide looks dead.

8. **Don't override `@media print`.** The base CSS's print block forces 1280×720 pages, hides nav chrome, and snaps reveal elements into their final state so PDF exports (via `Ctrl/⌘+P` or `scripts/export-pdf.sh`) are deterministic. Adding your own print rules on top is almost always a mistake — theme CSS should stay out of the print media query.

9. **Scope responsive breakpoints to `screen`.** A rule like `@media (max-width: 800px) { ... }` applies to *all* media types including print, and headless Chrome's print mode can evaluate media queries against its window viewport (not the `@page` size). That's why PDF exports of split/image-led slides can stack into column layout and clip. Always write `@media screen and (max-width: 800px) { ... }` in theme CSS. The base CSS's `@media print { ... }` block is the only place rules should apply to print.
