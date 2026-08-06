# Tracker bindings

Everything below the orchestrator is tracker-blind. `player-coach` wants a plan file path;
it has never heard of Jira. So the entire job of a tracker binding is:

> Given an epic reference, produce (a) an ordered list of issue handles, and (b) enough
> detail about each to write a plan file.

That's it. Resolve the binding once in Phase 0, write it into `run.json`, and use it
without re-deriving it for the rest of the run.

## The five operations

| Operation | Required? | Produces |
|---|---|---|
| `list` | Yes | Issue ids in the epic |
| `read` | Yes | Title, body, acceptance criteria, dependency links |
| `start` | No | Marks an issue in-progress |
| `comment` | No | Posts a comment |
| `close` | No | Marks an issue complete |

**Only `list` and `read` are required.** A tracker you can read but not write is fully
workable — the user reconciles status by hand afterward. Refusing to run because you
couldn't find a `close` command would be absurd.

Record the resolved binding concretely, as commands with placeholders:

```
tracker:  github
list:     gh issue list --milestone "Q3 export" --json number,title,body --limit 100
read:     gh issue view {id} --json title,body,labels
start:    gh issue edit {id} --add-label in-progress
comment:  gh issue comment {id} --body-file {file}
close:    (automatic — PR body says "Closes #{id}")
```

## Resolving an unknown tracker

Work outward from cheapest evidence:

1. **What did the user actually give you?** A URL names its own host. `PROJ-482` is a Jira
   key. A path ending in `.md` is a file. This resolves most cases immediately.
2. **What's in the repo?** A git remote pointing at GitHub or GitLab, an `.md` file full of
   `- [ ]` lines.
3. **What tooling exists?** `gh`, `glab`, `jira`, or an MCP server for the tracker. Check
   before assuming — an unauthenticated `gh` will fail every call in the same confusing way.
4. **Ask.** This is Phase 0, where asking is free. One question beats an hour of failures.

Then write the binding in the shape above and confirm it with the user alongside everything
else in Phase 0.

**Degrade rather than fail.** No write commands → read-only, say so. Can't determine
dependencies → infer them and announce every edge.

## Extracting dependencies

The rule is the same everywhere: **declared beats inferred, and inferred gets announced.**

Where to look, in order:

1. **Typed links** — Jira's `blocks` / `is blocked by`, GitHub's issue relationships.
2. **Body text** — `blocked by #12`, `depends on PROJ-4`, `after #7`. Common and worth
   grepping for; people write this even where the tracker supports real links.
3. **Structure** — nesting in a task list, indentation in a markdown file, ordering.
4. **Reasoning** — no frontend before its API, no migration before its schema, no
   integration before the thing it integrates.

Only (4) gets announced, because only (4) can be wrong in a way the user didn't author:

```
Inferred: #7 depends on #3 (consumes the /export endpoint #3 adds)
```

## Writing back

Two rules regardless of tracker.

**Say it came from an agent.** Comments and issues post under the user's account. Anyone
reading later must not have to wonder whether a human wrote it. One short line at the top,
no ceremony.

**Write at meaningful moments only.** Marking in-progress when work starts, linking the PR,
closing on merge, one summary comment on the epic at the end. A tracker notification per
turn would make the user's inbox useless and teach their team to ignore the project.
