# The tracker binding

Several skills write to a repository's issue tracker — publishing a spec, splitting work into
tickets, charting a map of decisions, marking an issue in-progress. None of them should have to
rediscover *which* tracker this repo uses, or what its labels mean, on every run. That
rediscovery is slow, and worse, it is inconsistent: two sessions guess differently and the
tracker ends up with two vocabularies in it.

So the binding is resolved once, by `setup-engineer`, and written down as **`TRACKER.md`
alongside the engineer skill** — the same place `VERIFICATION.md`, `VISUAL.md`, `API.md`, and
`DATABASE.md` already live. Every skill that touches the tracker reads it and gets the same
answer.

`TRACKER.md` is **optional**, and deliberately so: plenty of repos have no tracker worth
binding. A skill that can't find one resolves the tracker itself for that run and carries on.
Absence is a fallback, never a failure.

## Resolving the binding

Work outward from the cheapest evidence — what the user gave you, then the repo, then the
installed tooling, then ask. `epic-runner`'s `references/trackers.md` holds that ladder in full,
along with the *declared beats inferred* rule for dependency edges; follow it there rather than
inventing a second procedure. Two things are specific to doing it here:

- **Ask freely.** Asking is free during `setup-engineer` and expensive at runtime — a wrong
  guess written into `TRACKER.md` costs every later run, not just this one.
- **Verify before you write.** An unauthenticated `gh` resolves and then fails every call in the
  same confusing way, so run one read command and confirm it returns real data.

**Default to local markdown** when nothing resolves. A directory of ticket files is a real
tracker — it is version-controlled, greppable, and needs no credentials.

## The file

Write commands out concretely, with `{id}`-style placeholders. A skill should be able to
substitute and run, not interpret.

```markdown
# Tracker

**Tracker:** github
**Issues live at:** https://github.com/acme/widgets/issues

## Operations

| Operation | Command |
|---|---|
| `list` | `gh issue list --json number,title,labels --limit 100` |
| `read` | `gh issue view {id} --json title,body,labels,comments` |
| `create` | `gh issue create --title {title} --body-file {file}` |
| `start` | `gh issue edit {id} --add-label in-progress` |
| `comment` | `gh issue comment {id} --body-file {file}` |
| `close` | `gh issue close {id}` |

Only `list` and `read` are required. A tracker you can read but not write is fully workable —
record the gap here and the skills will report status for a human to reconcile by hand.

## Labels

| Meaning | Label in this repo |
|---|---|
| Ready for an agent to pick up | `ready-for-agent` |
| Being worked right now | `in-progress` |
| Blocked on a human | `needs-human` |

Meanings on the left, this repo's actual strings on the right. Skills ask for a meaning; the
right-hand column is what gets typed. Record only the meanings this repo has a label for —
a skill that wants "ready for an agent" and finds no row simply skips the labelling step
rather than inventing a label.

## Wayfinding operations

Only needed if the repo uses `wayfinder`. How this tracker expresses the three relationships a
map needs:

- **Child issue** — `gh issue edit {id} --add-sub-issue {child}`
- **Blocking edge** — native issue relationships; otherwise a `## Blocked by` list in the body
- **Frontier query** — `gh issue list --search 'parent-issue:{map} is:open no:assignee'`

`wayfinder` owns its own `wayfinder:*` label namespace and creates those labels itself; they
don't belong in the label table above.
```

## Per-tracker notes

**GitHub / GitLab.** Native sub-issues and issue relationships exist and should be preferred —
they render the dependency graph in the tracker's own UI, so a human sees what's takeable
without opening anything. Labels are cheap; create the ones the label table names.

**Jira.** Blocking is a first-class link type (`blocks` / `is blocked by`); use it. Jira's
"label" concept and its workflow *status* are different things, and the label table above may
map onto either — record which, because moving a status is a transition, not an edit.

**Local markdown.** One file per ticket under a stable directory, numbered in dependency order,
plus an `issues.md` checklist beside them — one `- [ ]` line per ticket, in dependency order,
naming its file. The checklist is the handle you hand an orchestrator; the per-ticket files hold
the detail. Blocking edges are text: a `**Blocked by:**` line naming the tickets that gate this
one. The frontier is "every open ticket whose blockers are all closed" — computed by reading,
not queried.

Record the directory in the file, so every skill writes to the same place. There is no command
table for this tracker; a `**Ticket directory:** .scratch/<feature-slug>/issues/` line under the
tracker name is the whole binding.

## Keeping it true

`TRACKER.md` caches something the environment cannot tell you by looking — which tracker this
team actually uses and what their labels mean. That makes it worth writing down, and it also
makes it capable of going stale: a repo that migrates from Jira to GitHub leaves this file
lying about where the work is.

Treat a failed tracker command as drift, not as an error to route around. Re-resolve, fix the
file, then carry on.
