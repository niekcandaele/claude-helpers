---
name: slides-generator
description: >
  Generate a polished single-file HTML slide deck from a topic brief, and
  produce detailed image-generation prompts the user can feed to any AI
  image generator (DALL-E, Flux, Imagen, Midjourney, Ideogram, SDXL, etc.)
  to illustrate the deck. The final deck references the generated images
  directly. Use this skill whenever the user wants slides, a deck, a
  presentation, a talk, a pitch, a demo, a keynote, or any kind of
  slide-based visual artifact — even when they don't say "slides"
  explicitly, e.g. "explain X in a visual way", "build me a talk about Y",
  "make something I can present Monday", "walk the team through Z on
  screen". Also trigger for conversions ("turn this doc into slides") and
  rebuilds ("redo these slides"). Output is one self-contained HTML file
  plus a numbered list of image prompts for the user to generate externally.
---

# slides-generator

Build an opinionated, distinctive HTML slide deck from a brief — and hand the user a shopping list of image prompts so they can parallelize AI image generation while the deck is being drafted.

This skill is a **four-phase workflow**. Don't skip phases. The split between "draft outline + image prompts" (Phase 2) and "build the final HTML" (Phase 3) is the whole point — it lets the user generate images in parallel with no wait.

## When this skill applies

Trigger for explicit asks ("make me slides about X"), but also for implicit ones: "walk me through Y", "explain Z visually", "build a deck / talk / pitch / keynote / demo", "turn this into a presentation". If the user shows up with a rich brief already in hand, skip the intake question and jump straight to Phase 2.

If the user asks for something adjacent that is *not* slides — a single poster, a README, a doc, a landing page — hand off to a more appropriate skill.

## Workflow at a glance

1. **Intake.** Collect topic, audience, tone, goal, length, and any hard style constraints.
2. **Outline + image prompts.** Write the slide-by-slide outline, decide the visual style, and emit a numbered list of detailed image prompts for the user to generate. **Stop and wait.**
3. **Build the HTML.** Once the user reports that images are ready, assemble the final single-file HTML deck with the images wired in.
4. **Handoff.** Tell the user where the file is and what knobs to turn if they want changes.

Each phase below says what to do, what supporting file to load, and what output the user should see.

---

## Phase 1 — Intake

Goal: get just enough to draft a real outline. Don't over-interview — one bundled question is plenty.

If the user already gave a rich brief in the conversation ("make me a 10-minute talk for my eng team about rolling out feature flags, focus on the rollout process, I want it to feel practical and a bit irreverent"), skip the question entirely. Restate what you heard in two sentences and ask only about the gaps. Otherwise:

Call `AskUserQuestion` once with these fields bundled into the options or as a single multi-part question:

- **Topic** — what's the deck about? One sentence.
- **Audience** — who sees this? ("internal eng team", "investors", "a design class", "customers at a launch event")
- **Goal** — what should the audience do / feel / remember afterward?
- **Tone** — 1–2 adjectives ("practical and irreverent", "precise and technical", "optimistic and warm", "serious and restrained").
- **Length** — short (5–8 slides), medium (9–14), or long (15–20). Default to medium if unspecified.
- **Hard constraints** — brand colors? Must-use fonts? Anything off-limits? (Most decks have none.)

If the user names a topic but gives you nothing else, pick reasonable defaults and state them out loud rather than asking four follow-up questions.

---

## Phase 2 — Outline + image prompts

This is the longest phase and the one users see most. Produce three things, in this order, in a single reply:

### 2a. Chosen style (one short paragraph)

Name the font pair, the three-color palette (with OKLCH values), and the overall vibe in 2–3 sentences. Something like:

> **Style.** Bold editorial — Archivo Black display paired with Space Grotesk body. Palette: deep graphite `oklch(0.2 0.02 260)` background, off-white `oklch(0.96 0.01 80)` text, and a single saturated coral `oklch(0.65 0.2 30)` accent. Flat backgrounds, generous whitespace, staggered bullet reveals, minimal motion.

Load `references/design-heuristics.md` for the font pair catalogue, the color rules, and the things-to-avoid list. Pick a direction that fits the brief's tone — don't default to "modern corporate" for every deck.

### 2b. Slide outline

One entry per slide:

```
Slide N — <type>
Headline: <the claim or label>
Content: <1–3 supporting points OR quote text OR stat>
Notes: <1–2 sentences the presenter would say>
Image: image_K.png  (or: none)
```

Types to mix across the deck: `title`, `content`, `image-led`, `split`, `quote`, `section-divider`, `stats`, `closer`. Keep ≤ 6 bullets per content slide. Use the layout rhythm guidance in `references/design-heuristics.md` (roughly 40% content, 20% image-led, 15% dividers, 10% stats, 10% quotes/specialty, plus title and closer).

### 2c. Image prompt list

This is the differentiator — the whole reason the skill exists in this shape.

Load `references/image-prompt-guide.md` before drafting prompts. Then for every slide that benefits from imagery (title, closer, section dividers almost always; image-led slides; split slides; concept slides where a visual metaphor genuinely aids understanding), emit a prompt.

**Default guidance on image count**: err toward richer, not sparser. A 10-slide deck usually wants 4–7 images. Don't ask for one per slide (it'll feel overwrought) and don't limit yourself to one or two (the deck will feel flat). If in doubt, ask the user how many images they're willing to generate and scale accordingly.

Format each entry as:

```
image_N.png · slide K · <role>
<single-paragraph prompt, 3–6 sentences: subject, composition, setting, medium/style, lighting, palette tied to the deck theme, aspect/pixels, negative hints if needed>
```

Prompts must be **model-agnostic prose** — no `--ar`, no `::` weights, no LoRA tags. The user picks their generator. Always include an aspect-ratio hint and "no text, no letters" when a scene might otherwise render words.

Match the image palette to the deck palette you declared in 2a — that's what makes the images feel like they belong to this deck, not a stock library.

### End of Phase 2

Close the reply with an explicit handoff line like:

> **Next:** save each image as its filename (`image_1.png`, `image_2.png`, …) into an `images/` folder next to where you'd like `slides.html` to live. Tell me when they're ready (or if you want me to revise the outline or any prompts first) and I'll build the deck.

**Do not continue to Phase 3 in the same reply.** The user needs time to generate images. Wait.

---

## Phase 3 — Build the HTML

Enter this phase only when the user says the images are ready (or gives you a folder path, or says "skip images and use placeholders").

Load `references/html-template.md`. It contains:
- The full HTML skeleton.
- The `SlidePresentation` JS controller (keyboard, touch, wheel, progress bar, nav dots, reveal observer) — paste it verbatim.
- Per-slide-type HTML snippets.
- A gotchas list — read it before writing CSS.

Then produce the HTML by:

1. **Writing the skeleton** with the Google Fonts link for the font pair you picked in Phase 2.
2. **Inlining `assets/viewport-base.css`** verbatim into the `<style>` block — read the file and paste its full contents. Do not edit it. This enforces viewport-fit, scroll-snap, responsive typography, and reduced-motion behavior.
3. **Appending theme CSS** after the base: set the `--color-*` and `--font-*` custom properties on `:root`, then add per-slide-type layout rules (e.g. `.slide--split { flex-direction: row; ... }`).
4. **Rendering each slide** using the snippets from `html-template.md`. Wrap animated elements in `.reveal` or `.stagger`.
5. **Referencing images** by relative path: `<img src="images/image_1.png" alt="…">`. The `alt` text should describe what's literally in the image, not "figure" or "illustration".
6. **Appending the `SlidePresentation` script** verbatim at the end of `<body>`.

### File location

Default to `./slides.html` in the current working directory, with images expected at `./images/image_N.png`. If the user specified a path, use that. If they asked for a different filename (e.g. `product-launch.html`), use it.

### Hard constraints — check before you save

- Every slide fits the viewport at common laptop heights (800px / 900px / 1080px). No internal scroll.
- ≤ 6 bullets per content slide, ≤ 1 hero image per slide.
- All Google Fonts referenced in the `<link>` are also referenced in CSS (Google Fonts URL uses `+` for spaces, CSS uses quoted real names — mismatches silently fall back to serif).
- Negated CSS length functions use `calc(-1 * clamp(...))`, not `-clamp(...)` (the latter is silently dropped).
- No external JS framework. Pure vanilla.
- Animations degrade correctly under `prefers-reduced-motion` (the base CSS handles this — don't override).

### Write the file

Use the `Write` tool. A well-built 12-slide deck typically lands at 40–80 KB.

---

## Phase 4 — Handoff

One short message:

- Where the file is and how to open it (`open slides.html` on macOS, double-click from file manager elsewhere).
- How the navigation works: arrow keys, space, page up/down, touch swipe, scroll wheel, or click a nav dot.
- A one-line offer: "Want to swap the palette, redo an image, reorder slides, or add/remove any slide? Say what you'd change and I'll update."

Don't recap what you built in detail — the user just saw it.

---

## Iteration — what to do when the user comes back

Common asks after Phase 4 and how to handle them:

- **"Change the accent color to X"** — edit only the `--color-accent` line (and anywhere else the color appears hardcoded) and re-save.
- **"Redo image 3"** — rewrite just that prompt from Phase 2's format. Don't rebuild the HTML; the user regenerates and replaces the file at the same path.
- **"Reorder / add / remove slides"** — edit the HTML directly. Don't re-run Phase 2.
- **"Different style entirely"** — go back to Phase 2a (chosen style) and rework theme CSS + image prompts together. Images may need regenerating if the palette shifts.
- **"Add speaker notes"** — add a `<details>` or a side-panel key in the HTML, or offer a separate `speaker-notes.md` if the user wants to present from a second screen.

---

## Reference files

- `references/html-template.md` — HTML skeleton, JS controller, per-slide-type snippets, gotchas. Load in Phase 3.
- `references/design-heuristics.md` — font pairs, color rules, layout rhythm, the "AI slop" avoid-list. Load in Phase 2a and Phase 3.
- `references/image-prompt-guide.md` — prompt anatomy, do/don't, aspect ratios, 3 worked examples. Load in Phase 2c.
- `assets/viewport-base.css` — mandatory base CSS. Inline verbatim in Phase 3.
