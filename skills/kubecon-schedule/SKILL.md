---
name: kubecon-schedule
description: >
  Filter and curate a KubeCon schedule from ICS calendar exports. Parses the raw schedule,
  applies heuristic filters to surface deep dives and high-signal talks, then iteratively
  refines recommendations based on user feedback. Outputs a curated markdown list and a
  filtered ICS file. Use this skill whenever the user mentions KubeCon schedule, KubeCon talks,
  filtering conference sessions, or wants help deciding which KubeCon sessions to attend —
  even if they just say "help me pick talks" or "there are too many sessions."
argument-hint: [optional user context or preferences]
---

# KubeCon Schedule Curator

Filter a KubeCon schedule down to the talks worth attending: $ARGUMENTS

This skill ships with bundled ICS files for the current KubeCon event. Your job is to parse the schedule, apply quality heuristics, and then work with the user in iterative rounds to build a personalized shortlist. The user knows Kubernetes well — they want depth, not introductions.

## Step 1: Parse the ICS files

Two ICS files are bundled in this skill's directory:
- `kubecon.ics` — the main KubeCon conference sessions
- `colocated-events.ics` — co-located events (Cilium Con, Istio Day, BackstageCon, etc.)

Read both files from the skill directory (the same directory as this SKILL.md). If the user provides a different ICS file path, use that instead.

Extract these fields from each VEVENT:

- **Title** (SUMMARY)
- **Description** (DESCRIPTION) — this is where the talk abstract lives
- **Start/End time** (DTSTART/DTEND)
- **Location/Room** (LOCATION)
- **Speaker(s)** — usually embedded in the description or title
- **Track/Category** (CATEGORIES or embedded in description)
- **Level** — look for tags like "Intro", "Deep Dive", "Case Study" in the title, categories, or description

If the ICS is malformed or missing fields, work with what you have. KubeCon's Sched exports are sometimes messy — speaker names might be in the description body rather than a structured field. Do your best to extract them.

Count the total number of sessions parsed and tell the user so they know the scale.

## Step 2: Apply heuristic filters (first pass)

Score each talk using these heuristics. The goal is to separate signal from noise before the user sees anything.

### Strong positive signals (boost)
- **Deep Dive or Case Study** in the title or tags — these are almost always higher quality
- **Maintainer Track** sessions — actual project contributors discussing internals and roadmap
- **Speaker is a known maintainer** of a CNCF project (check if the description mentions they're a maintainer, contributor, or committer)
- **Speaker from a company running k8s at scale** — large SaaS companies, cloud providers, platform engineering teams at scale
- **Title suggests a war story** — phrases like "lessons learned", "how we", "what went wrong", "in production", "at scale", "post-mortem"
- **Specific technical depth** — the abstract mentions concrete technologies, architectures, numbers, or trade-offs rather than vague promises

### Strong negative signals (deprioritize)
- **"Introduction to"**, **"Getting Started"**, **"101"**, **"Beginner"** — the user already knows the basics
- **Sponsored Session** or **Sponsor Showcase** — almost always marketing
- **Two or more speakers from the same vendor** discussing their own product — likely a product demo
- **Vague buzzword-heavy abstract** — "unlock the power of", "revolutionize your", "seamless integration" with no concrete details
- **Lightning talks** about very narrow vendor-specific tools (not general lightning talks, which can be great)

### Neutral — let the user decide
- **Panel discussions** — hit or miss, depends on the panelists
- **BoF (Birds of a Feather)** — valuable for networking, less for content
- **Keynotes** — mixed quality but the user might want to attend for the spectacle

### What NOT to filter on
Don't filter by topic area yet. The user hasn't told you what they're interested in — that's what the iterative rounds are for. Apply only quality heuristics in this pass, not topic preferences.

## Step 3: Present the first batch

Show the user 10-15 of the highest-scored talks. For each talk, present:

```
### [Talk Title]
**Speaker(s):** Name (Company)
**Track:** Deep Dive / Case Study / etc.
**When:** Day, Time — Time
**Room:** Location

> [2-3 sentence summary of the abstract — what the talk is actually about, not the marketing fluff]

**Why this made the cut:** [brief reason — e.g., "maintainer of Cilium discussing eBPF internals" or "production war story from a team running 2000 nodes"]
```

Group the batch by day/time slot if possible so the user can see their schedule taking shape.

If any recommended talks overlap in time, flag it clearly:

```
> [!warning] Schedule conflict
> This talk overlaps with [Other Talk Title] (same time slot). Both are recommended — pick one to attend live and catch the other on YouTube later.
```

After presenting, ask the user for feedback. Something like: "Which of these look good? Which aren't interesting? Any topics you want to see more or less of?"

## Step 4: Learn and refine

Based on the user's feedback, infer their preferences:

- If they consistently reject networking/service-mesh talks → deprioritize that topic area
- If they love the platform engineering talks → surface more of those
- If they say "too basic" about something you rated as deep → calibrate your depth threshold higher
- If they flag a speaker they know is good → look for other talks by that speaker

Apply the learned preferences and present the next batch. Keep batches to ~10 talks to avoid overwhelming the user.

Repeat until:
- The user says they're happy with their list
- You've covered all the high-quality talks in the schedule
- The user has enough talks to fill their days

Throughout the rounds, maintain a running list of accepted talks so you can:
- Flag new conflicts with already-accepted talks
- Avoid re-recommending rejected talks
- Track how full each day is getting

## Step 5: Generate outputs

When the user is satisfied, produce two outputs:

### Markdown schedule

Save to `Fleeting/` in the vault (or wherever the user specifies) as `YYYY-MM-DD_kubecon-schedule.md`:

```markdown
---
date: YYYY-MM-DD
tags:
  - area/tech/kubernetes
  - resource/conference
---

# KubeCon YYYY — Curated Schedule

## Day 1 — [Date]

### [Time Slot]

**[Talk Title]**
Speaker(s) | Track | Room
> [Brief summary]

[If there's a conflict, show both talks with a note:]
*Also interested in: [Conflicting Talk Title] — catch recording later*

### [Next Time Slot]
...

## Day 2 — [Date]
...

## Talks to Watch Later

These talks looked interesting but conflicted with something better, or didn't fit the schedule:

- [Talk Title] — [one-line reason it's worth watching]
- ...
```

### Filtered ICS file

Generate a valid ICS file containing only the accepted talks. This lets the user import their curated schedule into Google Calendar, Apple Calendar, or whatever they use.

The ICS should preserve the original VEVENT data (times, locations, descriptions) from the source file. Write it to the same directory as the markdown file, named `kubecon-YYYY-curated.ics`.

ICS format reminder:
```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//KubeCon Curator//EN
BEGIN:VEVENT
DTSTART:20260316T090000Z
DTEND:20260316T093000Z
SUMMARY:Talk Title
DESCRIPTION:Talk description
LOCATION:Room Name
END:VEVENT
...
END:VCALENDAR
```

Make sure to preserve timezone information from the original file.

## Step 6: Post-processing

After saving, run vault maintenance agents:
1. **link-enricher**: Add wikilinks to the markdown file
2. **daily-note-keeper**: Log that a KubeCon schedule was curated

## Tips for better results

- Both bundled ICS files are parsed by default — ask the user if they want to exclude co-located events
- KubeCon EU vs NA vs China have different track structures — adapt accordingly
- The "hallway track" is real — suggest leaving 1-2 gaps per day for spontaneous conversations
- Remind the user that all talks get recorded — conflicting good talks aren't lost, just deferred
