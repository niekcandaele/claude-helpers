---
name: improve-codebase-architecture
description: Find deepening opportunities in a codebase, informed by the domain language in CONTEXT.md and the decisions in docs/adr/. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
metadata:
  group: design
  requires: [codebase-design]
  optional: [rich-page, grill-me]
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

This skill is built on a shared design vocabulary and _informed_ by the project's domain model:

- The `codebase-design` skill holds the architecture vocabulary — **module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality** — and its principles: the deletion test, "the interface is the test surface", "one adapter = hypothetical seam, two = real". Read it before you scan, and use those terms exactly in every suggestion.
- `CONTEXT.md` gives names to good seams; ADRs in `docs/adr/` record decisions this skill should not re-litigate. Both formats are documented in the `grill-me` skill, if it's installed alongside: [CONTEXT-FORMAT.md](../grill-me/CONTEXT-FORMAT.md), [ADR-FORMAT.md](../grill-me/ADR-FORMAT.md).

## Process

### 1. Explore

**Scope before you scan.** Deepening a module pays off by making future changes to it easier, so weight the parts of the codebase that keep moving. Decide *where* to look before you look:

- If the user named a direction — a module, a subsystem, a pain point — take it, and skip the inference below.
- Otherwise walk back a good stretch of `git log --oneline` for the codebase's hot spots — the files and areas that keep coming up — and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.

Read the existing documentation for that area first:

- `CONTEXT.md` (or `CONTEXT-MAP.md` + each `CONTEXT.md` in a multi-context repo)
- Relevant ADRs in `docs/adr/` (and any context-scoped `docs/adr/` directories)

If any of these files don't exist, proceed silently — don't flag their absence or suggest creating them upfront.

Then send a read-only exploration sub-agent to walk the codebase (on Claude Code, the `Explore` agent type). Don't follow rigid heuristics — explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Present candidates

Each candidate gets:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Solution** — plain English description of what would change
- **Benefits** — explained in terms of locality and leverage, and also in how tests would improve
- **Recommendation strength** — `Strong`, `Worth exploring`, or `Speculative`

End with a **top recommendation**: which candidate you'd tackle first, and why.

Architecture is graph-shaped, and a before/after picture of a deepening lands harder than a paragraph about it. If `rich-page` is available, build the candidate list as a self-contained HTML report — a card per candidate with a **before/after diagram** showing the shallowness and the deepening, and the strength as a badge — written to a temp path outside the repo, and open it for the user. Otherwise present the same fields as a numbered list in chat.

**Use CONTEXT.md vocabulary for the domain, and `codebase-design` vocabulary for the architecture.** If `CONTEXT.md` defines "Order," talk about "the Order intake module" — not "the FooBarHandler," and not "the Order service."

**ADR conflicts**: if a candidate contradicts an existing ADR, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly (e.g. _"contradicts ADR-0007 — but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

Do NOT propose interfaces yet. Ask the user: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation — the `grill-me` skill if it's installed. Walk the design tree with them: constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize — keep the domain model current as you go, the same discipline `ubiquitous-language` applies:

- **Naming a deepened module after a concept not in `CONTEXT.md`?** Add the term to `CONTEXT.md` (see [CONTEXT-FORMAT.md](../grill-me/CONTEXT-FORMAT.md)). Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `CONTEXT.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR, framed as: _"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"_ Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing — skip ephemeral reasons ("not worth it right now") and self-evident ones. See [ADR-FORMAT.md](../grill-me/ADR-FORMAT.md).
- **Want to explore alternative interfaces for the deepened module?** Use `codebase-design`'s design-it-twice pattern.

---

*Derived from [mattpocock/skills](https://github.com/mattpocock/skills), MIT © 2026 Matt Pocock. Keep this line if you copy this file.*
