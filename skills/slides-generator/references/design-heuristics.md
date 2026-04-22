# Design heuristics

Load this when you're picking the deck's visual direction (Phase 2) or writing theme CSS (Phase 3).

The job here is to end up with a deck that looks **specific and deliberate** — like a real designer made a choice — instead of the interchangeable beige-corporate aesthetic that AI tools default to.

## What to avoid (the "AI slop" tells)

If your draft has any of these, stop and rework:

- **Inter as the body font.** It's fine, but every AI-made page uses it, so it reads as "AI did this." Pick almost anything else.
- **Purple-to-blue gradient backgrounds on white.** Instant tell.
- **Three-card feature grid centered below a hero.** The SaaS template.
- **Emoji as decoration.** 🚀 on a title slide screams "ChatGPT wrote this."
- **Drop shadows on every element.** Modern design uses shadow as punctuation, not a default.
- **Everything centered.** Asymmetry signals intent. Full-width vertical centering looks lazy.
- **Placeholder-sounding copy.** "Transforming the way you work" / "Empowering teams." If it could be about anything, rewrite it.

## Font pairs — pick one and commit

Each pair is a shorthand for a vibe. Don't mix pairs across a deck. If the user's brief doesn't obviously match one, pick the closest fit and own the choice.

| Pair | Vibe | Fits briefs like |
|------|------|------------------|
| **Archivo Black + Space Grotesk** | bold editorial, confident | product launches, manifestos, rally-the-team |
| **Fraunces + Work Sans** | literary-modern, warm | long-form arguments, design talks, narrative decks |
| **JetBrains Mono + Inter** | dev/technical, lo-fi | engineering talks, infra, internal eng reviews |
| **Bodoni Moda + DM Sans** | high-contrast editorial, magazine | brand decks, case studies, portfolio reviews |
| **Plus Jakarta Sans (solo)** | approachable product, friendly | product updates, onboarding, customer success |
| **Space Grotesk + IBM Plex Mono** | techy-clean, honest | technical pitches, developer tools, API launches |
| **Cormorant Garamond + Source Serif 4** | elegant long-form, thoughtful | research, policy, philosophy-adjacent decks |
| **Syne + Space Mono** | retro-modern, playful | creative pitches, brand-new products, art |
| **Manrope (solo)** | corporate-clean, neutral | board decks, financial updates, when the content is the star |
| **Outfit (solo)** | playful, rounded, optimistic | consumer products, kids/education, launches |

All of these load from Google Fonts. Use `display=swap` to avoid FOIT.

## Color — pick three, not ten

A coherent deck has **three colors** that carry weight:

1. **Dominant background** — 70%+ of the visual field. Usually a deep neutral (off-black `oklch(0.18 0.02 260)`, warm cream `oklch(0.95 0.02 80)`) or a strong brand color if one was given.
2. **Primary text** — high-contrast against the background. Not pure `#000` on pure `#fff` — soften one side.
3. **Accent** — one saturated color used sparingly for headlines, underlines, links, the progress bar. This is the punch.

Optionally a fourth **muted** tone for hairlines and tertiary text (e.g. dividers, metadata, timestamps).

Use **OKLCH** values (`oklch(L C H)`) so lightness is perceptual — easier to pick colors that look balanced across the palette. Online OKLCH pickers are fine, but once you know the pattern, you can write values directly:

- Lightness: `0.18` → near-black, `0.5` → mid, `0.95` → near-white.
- Chroma: `0` → gray, `0.15` → saturated, `0.3` → vivid.
- Hue: 0 = red, 60 = yellow, 120 = green, 180 = cyan, 240 = blue, 320 = magenta.

Avoid:
- Four-stop rainbow gradients as backgrounds (unless the deck's *about* something maximalist).
- Blue and orange together unless you're intentionally doing the action-movie-poster thing.
- Low-contrast text on colored backgrounds. Check WCAG AA against both #000 and #fff eyes — many brand colors fail.

## Layout rhythm — vary the shape

A 12-slide deck where every slide is "headline + three bullets centered" is dead before it starts. Mix slide types by type share:

- **~40%** content slides (headline + bullets / numbered list).
- **~20%** image-led or split slides (image + short text).
- **~15%** section dividers (full-bleed, minimal copy, often with an atmospheric image).
- **~10%** data/stats slides.
- **~10%** quotes, code, or specialty layouts.
- **2 slides** — title at the start, closer at the end.

When a content slide appears three times in a row, break the pattern: insert a quote, a stat, or an image. The rhythm is as important as the content.

## Motion — one idea, well-executed

Animation should feel like a single pencil stroke, not a firework:

- **One entrance motion per slide.** Fade-up is reliable; slide-from-left, scale-in, blur-to-clear are good swaps. Don't mix three on one slide.
- **Stagger lists.** Bullets reveal in order, 80–120ms apart. The base CSS provides `.stagger` for this. Don't go above 6 items or it drags.
- **No looping animations.** No pulsing dots, no sweeping shimmers. They steal attention from whoever's presenting.
- **Honor `prefers-reduced-motion`.** The base CSS disables animation when the user's system asks — don't override it.

## Backgrounds — decide upfront

Three patterns, pick one for the deck:

1. **Flat color.** The default. Strong color does the work. Minimal, modern, holds up.
2. **Subtle texture.** A light paper grain, fine dot grid, or 1-2% noise overlay. Adds warmth without shouting. CSS-only (no external images).
3. **Per-slide atmospheric.** Section dividers get full-bleed generated imagery as `background-image: url(...)`; content slides are flat. High impact, but only if the image prompts are strong.

Don't mix. A deck with flat content slides and gradient dividers feels like two decks glued together.

## Hero images — one per slide, max

A slide should have at most one dominant image. Two images compete; three is chaos. If a concept needs multiple visuals, split across slides.

Give hero images room to breathe — at least 40% of the slide should be empty space (either whitespace or solid color). Cramped images read as clipart.

## Copy — write with verbs

- **Headlines are claims, not labels.** `"Our users trust us"` is a label. `"92% ship faster after week one"` is a claim.
- **Bullets start with a strong word** — usually a verb or a noun, not a conjunction. Scan the first word of each bullet; if they're all "The", "A", "We", rewrite.
- **No trailing periods on bullets or headlines.** They read better without.
- **Cut adverbs first.** "Really fast", "very scalable" — delete "really" and "very".

## Self-check before handoff

- [ ] The deck uses one font pair. No surprise fonts in CSS.
- [ ] At most three colors carry weight. Accent is used, not shouted.
- [ ] Slide types vary across the deck; no stretch of 3+ identical layouts.
- [ ] Every image has a real `alt` value that names the subject.
- [ ] Every slide fits the viewport without scrolling (open and eyeball it).
- [ ] Copy doesn't contain placeholder phrases or empty marketing verbs.
