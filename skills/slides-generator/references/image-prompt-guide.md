# Image prompt guide

Load this when you're drafting the image prompt list in Phase 2.

The prompts go to the user, not to a model directly — the user pastes them into whatever image generator they prefer (DALL-E, Flux, Imagen, Midjourney, Ideogram, Stable Diffusion, etc.). Write them so they work across these models: **descriptive prose, no model-specific flags or syntax**.

## Prompt anatomy

A good prompt names these things in this order:

1. **Subject** — what literally is in the image (one person reading, a stack of books, a city street).
2. **Action / composition** — what they're doing and how they're framed (close-up, wide shot, from above, centered).
3. **Setting** — where they are.
4. **Style / medium** — the single biggest lever. "Editorial photograph" vs. "flat vector illustration" vs. "3D isometric render" vs. "ink and watercolor" — be specific.
5. **Lighting** — warm low-angle sun, cold overhead studio, single candle, soft window diffuse.
6. **Palette** — pull from the deck's theme so images match the slides (e.g. "muted earth tones with a single coral accent").
7. **Aspect / framing hint** — landscape 16:9, square, portrait 9:16.
8. **Negative note if needed** — "no text, no letters, no logos" is the most common one. Most generators render words poorly.

## Do this

- **Be literal, not metaphorical.** Models handle "two ropes tied in a knot" better than "the idea of connection". If the concept is abstract, pick an evocative concrete scene that points at it.
- **Anchor on one medium.** "Editorial ink illustration" has a different look than "photograph" — don't mix.
- **Describe light.** Saying how a scene is lit adds more character than any other single word. "Late afternoon rim light" > no lighting info.
- **Tie palette to the deck.** If the deck uses `oklch(0.6 0.2 30)` (warm coral) as accent, say "muted off-whites with coral accents" so images don't clash.
- **Say "no text" when it matters.** Anywhere a sign, label, or screen might appear, add "no text, no letters".
- **Pick aspect upfront.** Most slides want **landscape 16:9** (1920×1080 or 1792×1024). Icons/portraits want **1:1**. Full-bleed section dividers sometimes want **portrait 9:16**, but only for very specific layouts.

## Don't do this

- **Don't stack adjectives.** "Beautiful stunning amazing cinematic" doesn't stack — it dilutes. Pick one adjective that carries weight.
- **Don't ask for text in the image.** Almost always comes out garbled.
- **Don't include model-specific flags.** No `--ar 16:9`, no `::` weights, no `<lora:...>`. The user may be using a model that doesn't support them, and they're easy for them to add if they want.
- **Don't prescribe impossible specifics.** "Exactly seven birds" will give you six or eight. Keep counts vague ("a handful of birds", "a few figures") unless a count matters.
- **Don't over-specify character appearance.** "A 34-year-old woman with short brown hair wearing a navy cardigan" over-constrains the model. "A person mid-laugh, warmly lit" usually beats it.

## Aspect ratios

| Purpose | Aspect | Typical pixels | Notes |
|---|---|---|---|
| Title hero | 16:9 landscape | 1920×1080 | Wide enough to sit above a headline. |
| Split-slide media | 4:5 or 1:1 | 1080×1350 or 1024×1024 | Fits a tall media column without dominating. |
| Section divider | 16:9 landscape | 1920×1080 | Often used full-bleed behind text. |
| Icon illustration | 1:1 | 1024×1024 | Small accents next to a headline. |
| Full-bleed portrait | 9:16 | 1080×1920 | Rare — only for specific layouts. |

## Worked examples

Use these as templates for the format your prompts should take.

### Example 1 — Title hero

**Slide 1 — title of a talk on network congestion**

> `image_1.png` · slide 1 · hero
> A tangled network of glowing fiber-optic cables converging into a single dense knot at the center of the frame, resting on a matte concrete surface. Shot as an editorial close-up photograph, shallow depth of field, moody low-key lighting with cold cyan highlights against deep charcoal shadows. Palette: charcoal black, soft graphite, one saturated cyan accent on the brightest fibers. Landscape 16:9, roughly 1920×1080. No text, no logos.

### Example 2 — Concept metaphor

**Slide 5 — illustrating "backpressure" in a data pipeline**

> `image_2.png` · slide 5 · metaphor
> A hand-drawn editorial illustration of a thick water pipe overflowing at a crimped section, with water backing up into a reservoir behind it. Side-on view, flat perspective, visible pen strokes and ink texture. Palette: warm off-white paper background, deep ink black line work, a single muted teal fill used sparingly for the water. Square 1:1, roughly 1024×1024. No text.

### Example 3 — Section divider

**Slide 8 — divider opening Part Two: "Handling failure"**

> `image_3.png` · slide 8 · section divider
> A wide, atmospheric photograph looking up at a single street lamp on a foggy night, the light diffusing into a soft halo against black sky, one dark silhouette walking away at the edge of the frame. Cinematic long-lens composition, heavy atmosphere, film grain. Palette: near-black, warm amber halo, a thin strip of deep blue at the horizon. Landscape 16:9, roughly 1920×1080. No text, no lettering on the lamp.

## Output format the user sees

In Phase 2, emit the prompts as a numbered fenced block so the user can copy-paste them one at a time or all at once. Header each entry with:

```
image_N.png · slide K · <role>
<single-paragraph prompt, 3-6 sentences>
```

One blank line between entries. Keep each prompt a single paragraph — most generators dislike multi-paragraph input. End with an "aspect / pixels" line when useful.

Also tell the user: *"Save each generated image as the filename shown (`image_1.png`, `image_2.png`, …) into a folder called `images/` next to where you'd like the slides saved. When you're done, tell me and I'll build the deck."*
