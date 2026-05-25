# Image handling

Load this in Phase 2 if the visual plan calls for raster imagery (hero photography, section dividers, illustrations), and in Phase 3 when you're inlining the resulting image bytes.

The rule is absolute: **every image in the final page is base64-inlined.** No `<img src="https://…">`, no `<img src="images/foo.png">`. The page must render identically when copied to a stranger's machine and opened from disk — that's the contract with the user.

This file covers:
1. When to use raster images vs inline SVG vs nothing
2. The base64-inlining workflow (with file-size targets)
3. AI image generation prompts when you need bespoke imagery

---

## 1. When to use what

| Need | Use |
|---|---|
| Atmospheric hero, section divider, photographic feel | **Raster image (WebP), base64-inlined** |
| Diagram, chart, icon, custom shape | **Inline SVG** (no base64 needed; SVG is XML and goes directly in HTML) |
| Logo or brand mark you already have | **Inline SVG** if vector, base64-inlined PNG/WebP if raster |
| Decoration / texture | **Pure CSS** (gradients, `background-image: linear-gradient(...)`) — no image at all |

The default is **no image**. Most rich pages don't need raster photography; they earn their visual weight through typography, color, charts, and diagrams. Reach for raster only when:

- The source itself has authoritative imagery (a research paper's figures, a product's screenshots)
- The page is editorial/long-form and atmospheric hero/divider images add real warmth
- The topic is inherently visual (architecture photography, product design, a specific physical thing)

If you can't articulate what an image *adds*, don't add it.

---

## 2. Base64-inlining workflow

### File-size targets

Every base64-encoded byte is ~1.37× the binary size. Set hard ceilings so the page stays under 1 MB total:

| Use | Target file size (binary, before base64) | Encoded equivalent |
|---|---|---|
| Hero image (full-width) | ≤ 200 KB | ~275 KB inline |
| Section divider / large illustration | ≤ 120 KB | ~165 KB inline |
| Inline illustration / thumbnail | ≤ 60 KB | ~82 KB inline |
| Icon / small mark | ≤ 10 KB | ~14 KB inline |

A well-built rich page lands at 150–500 KB. Crossing 1 MB usually means too many raster images — re-budget.

### Format choice

- **WebP** is the default. ~30% smaller than equivalent JPEG; supported by every modern browser.
- **JPEG** is fine for photographic content if WebP isn't available.
- **PNG** only when the image needs transparency or sharp edges (logos, screenshots).
- **Never GIF.** If you want motion, use a CSS animation or `<video>` (but `<video>` doesn't base64 well — avoid).

### Optimize before encoding

The image you encode is the image the page ships. Optimize aggressively:

```bash
# Convert + compress in one step (cwebp from libwebp)
cwebp -q 80 -resize 1600 0 hero.jpg -o hero.webp

# Or for photos, mozjpeg
cjpeg -quality 80 -progressive hero.jpg > hero.jpg.opt && mv hero.jpg.opt hero.jpg

# For PNGs (logos, screenshots)
pngquant --quality=70-90 --strip --output logo.png --force logo.png
```

`-q 80` is the sweet spot for WebP — visually indistinguishable from lossless for most content, ~5× smaller. Resize to the *display* width, not the source width: a 3000px-wide source displayed at 1200px in the layout is 6× bigger than it needs to be.

### Encode and inline

Once the image is optimized and sized:

```bash
# Produce a data URL ready to paste into HTML
echo "data:image/webp;base64,$(base64 -w0 hero.webp)"
```

Then in the HTML:

```html
<img
  src="data:image/webp;base64,UklGRlw…"
  alt="The actual subject — descriptive, not 'figure 1'"
  width="1600" height="900"
  loading="lazy"
  decoding="async"
  style="display: block; max-width: 100%; height: auto;"
>
```

**Always set `width` and `height` attributes** so the browser reserves layout space and the page doesn't reflow when the image decodes. The CSS overrides them to keep it responsive.

**`loading="lazy"`** is fine even on inlined images — it just defers decode work for off-screen images.

### `alt` text

Describe the *subject*, not "image" or "figure":

```html
<!-- Bad -->
<img alt="hero image" …>
<img alt="figure 1" …>

<!-- Good -->
<img alt="A network of glowing fiber-optic cables converging into a single dense knot on a matte concrete surface" …>
```

If the image is purely decorative (a texture, a gradient overlay), use `alt=""` — screen readers will skip it.

### Workflow when you need many images

For a page with 3–5 images, do them inline as above. For more, consider:

1. Generate or collect all images first into a working directory (e.g. `/tmp/page-assets/`).
2. Optimize each one (`cwebp -q 80 ...`).
3. Inline them one at a time as you write the HTML, using `base64 -w0` to produce each data URL.

Don't write a script that auto-inlines — it's easy to lose the optimize step and ship a 4MB page.

---

## 3. AI image generation prompts

If the visual plan calls for bespoke imagery that doesn't exist in the source (atmospheric heroes, conceptual metaphors, section dividers), generate them.

You have two paths:

### Path A — the user generates externally and hands you the file

For pages where the user wants editorial control over the imagery, emit prompts in Phase 2 and pause:

> **Next:** generate each image using your preferred tool (DALL-E, Flux, Imagen, Midjourney, Ideogram, etc.), save them to a folder, and tell me when they're ready. I'll optimize, base64-encode, and inline them in Phase 3.

### Path B — you generate them yourself with an image MCP

If an image-generation MCP is available in the session (check tool list), generate inline. Saves user a step.

### Prompt anatomy

Whether the user or you runs the prompt, the prompt is the same. Write prose, no model-specific flags. A good prompt names these things in this order:

1. **Subject** — what literally is in the image (one person reading, a stack of books, a city street).
2. **Action / composition** — what they're doing and how they're framed (close-up, wide shot, from above, centered).
3. **Setting** — where they are.
4. **Style / medium** — the single biggest lever. "Editorial photograph" vs "flat vector illustration" vs "3D isometric render" vs "ink and watercolor" — be specific.
5. **Lighting** — warm low-angle sun, cold overhead studio, single candle, soft window diffuse.
6. **Palette** — pull from the page's OKLCH palette so images match. "Muted earth tones with a single coral accent."
7. **Aspect / framing hint** — landscape 16:9, square 1:1, portrait 9:16.
8. **Negative note if needed** — "no text, no letters, no logos" is the most common. Most generators render words poorly.

### Do this

- **Be literal, not metaphorical.** Models handle "two ropes tied in a knot" better than "the idea of connection." For abstract concepts, pick an evocative concrete scene.
- **Anchor on one medium.** Don't mix "editorial photograph" with "ink illustration."
- **Describe light.** Saying how a scene is lit adds more character than any other single word.
- **Tie palette to the page.** If the page uses `oklch(0.65 0.18 30)` (coral) as accent, say "muted off-whites with coral accents" so images don't clash.
- **Say "no text" when it matters.** Anywhere a sign, label, or screen might appear.
- **Pick aspect upfront.** Heroes/dividers: 16:9 (1920×1080). Squares: 1:1 (1024×1024). Portraits: 9:16 (rare).

### Don't do this

- **Don't stack adjectives.** "Beautiful stunning amazing cinematic" dilutes. Pick one weight-carrying adjective.
- **Don't ask for text in the image.** Almost always comes out garbled.
- **Don't include model-specific flags** — no `--ar 16:9`, no `::` weights, no `<lora:…>` tags. The user picks their model.
- **Don't prescribe impossible specifics.** "Exactly seven birds" gives you six or eight. Keep counts vague unless they matter.
- **Don't over-specify characters.** "A 34-year-old woman with short brown hair in a navy cardigan" over-constrains. "A person mid-laugh, warmly lit" usually beats it.

### Aspect ratios

| Purpose | Aspect | Typical pixels | Notes |
|---|---|---|---|
| Hero | 16:9 landscape | 1920×1080 | Wide enough to sit above a headline |
| Section divider | 16:9 landscape | 1920×1080 | Often used full-bleed behind text |
| Split-section media | 4:5 or 1:1 | 1080×1350 or 1024×1024 | Fits a tall media column |
| Icon illustration | 1:1 | 1024×1024 | Small accents next to a headline |
| Full-bleed portrait | 9:16 | 1080×1920 | Rare — only specific layouts |

### Worked examples

**Example 1 — Hero**

> A tangled network of glowing fiber-optic cables converging into a single dense knot at the center of the frame, resting on a matte concrete surface. Shot as an editorial close-up photograph, shallow depth of field, moody low-key lighting with cold cyan highlights against deep charcoal shadows. Palette: charcoal black, soft graphite, one saturated cyan accent on the brightest fibers. Landscape 16:9, roughly 1920×1080. No text, no logos.

**Example 2 — Concept metaphor**

> A hand-drawn editorial illustration of a thick water pipe overflowing at a crimped section, with water backing up into a reservoir behind it. Side-on view, flat perspective, visible pen strokes and ink texture. Palette: warm off-white paper background, deep ink black line work, a single muted teal fill used sparingly for the water. Square 1:1, roughly 1024×1024. No text.

**Example 3 — Section divider**

> A wide, atmospheric photograph looking up at a single street lamp on a foggy night, the light diffusing into a soft halo against black sky, one dark silhouette walking away at the edge of the frame. Cinematic long-lens composition, heavy atmosphere, film grain. Palette: near-black, warm amber halo, a thin strip of deep blue at the horizon. Landscape 16:9, roughly 1920×1080. No text, no lettering on the lamp.

---

## 4. Self-check

**SKILL.md Phase 4 is the canonical self-check.** This section is a reminder of the asset contract from this file's domain only — the actual blocking checks (with the correct PCRE regex) live in SKILL.md.

After Phase 3, before handoff:

```bash
# No external image references should exist anywhere. PCRE required —
# GNU grep -E does NOT support negative lookahead and will silently match
# every src= line. Use grep -P (PCRE) on Linux/macOS:
grep -Pn 'src="(?!data:|https://)' page.html
# (https:// is allowed for CDN libs only — confirm any matches are CDN links)

grep -oE 'src="[^"]{0,40}' page.html | head -20
# Sanity-check what's actually there

# Total file size
ls -la page.html
# Reasonable budget depends on libs + images. With raster images, 300 KB – 1 MB
# is normal. Over 1 MB → image budget exceeded.
```
