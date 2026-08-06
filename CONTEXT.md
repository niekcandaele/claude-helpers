# Skills

A source repository of reusable agent skills, published for anyone to install or copy. The skills encode one engineer's opinionated development flow; several only make sense installed together.

## Language

**Harness**:
The program that loads and runs a skill.
_Avoid_: agent, client, runtime, tool

**Skill**:
A directory containing a `SKILL.md` and any supporting files, describing a procedure a harness can follow.
_Avoid_: command, prompt, plugin

**Suite**:
A set of skills that only work correctly when installed together.
_Avoid_: group (collides with `skills.sh.json`'s `groupings` field), bundle, pack

**Standalone**:
A skill that works with no other skill from this repository installed.
_Avoid_: independent, self-contained

**Harness-neutral**:
Written so it works on any harness, with no reference to a specific harness's tool names, directory layout, or features.
_Avoid_: generic, portable, degrades gracefully

**Engineer skill**:
A per-repository skill describing how to build, test, and run that repository, which other skills read for project-specific context.
_Avoid_: project skill, repo skill, local skill

## Relationships

- A **Suite** contains two or more **Skills**; a **Skill** may belong to several
  (`tester` is required by both the verify and review-pr suites)
- A **Skill** required by no other **Skill**, and requiring none, is **Standalone**
- A **Suite** may itself be a member of another **Suite** (`verify` is a suite, and
  `player-coach` requires it)
- Several **Skills** read the **Engineer skill** of the repository they run against
- A **Skill** is **Harness-neutral** or it names the **Harness** it requires

## Example dialogue

> **Dev:** "Does `verify` still work if I only install `verify`?"
> **Author:** "No — `verify` is a **Suite**. It fans out to the reviewer **Skills**, so those have to be installed too. `catchup` is **Standalone**, that one you can take on its own."
>
> **Dev:** "And it needs Claude Code?"
> **Author:** "It's **Harness-neutral** — it doesn't name a **Harness** anywhere. A **Harness** without sub-agents runs the reviewers one at a time instead of in parallel."

## Flagged ambiguities

- "agent" was used to mean both the **Harness** and a sub-agent it spawns — resolved: the **Harness** is the program; the things it spawns are sub-agents.
- "degrade" was used for running on a less capable **Harness** — rejected as pejorative and inaccurate; the property is **Harness-neutral**, and a **Harness** either supports a feature or runs a documented fallback.
