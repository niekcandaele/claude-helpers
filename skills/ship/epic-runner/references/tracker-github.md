# Binding: GitHub via `gh`

The reference implementation. Verify `gh auth status` succeeds in Phase 0 — an
unauthenticated `gh` fails every call in the same opaque way.

## Resolving the epic reference

GitHub has no first-class epic, so an epic is whichever grouping the user actually uses:

| Reference looks like | Grouping | `list` |
|---|---|---|
| `"Q3 export"`, a milestone URL | Milestone | `gh issue list --milestone "{name}" --state open --json number,title,body --limit 100` |
| `epic:export`, a label | Label | `gh issue list --label "{label}" --state open --json number,title,body --limit 100` |
| `#412`, an issue URL | Tracking issue | Read #412, extract the task list (below) |
| A project board URL | Project | `gh project item-list {n} --owner {owner} --format json` |

Ambiguous references are normal — `export` could be a label or a milestone. Check both and
ask in Phase 0 if more than one matches.

**Tracking-issue task lists** are the most common shape and need parsing out of the body:

```bash
gh issue view {n} --json body -q .body | grep -oE '^\s*- \[[ x]\] .*#([0-9]+)'
```

Checked boxes are already done — exclude them. Indentation is a dependency signal: a nested
item generally depends on its parent.

## The six operations

```bash
# read
gh issue view {id} --json number,title,body,labels,milestone

# start
gh issue edit {id} --add-label in-progress          # only if the label exists

# comment
gh issue comment {id} --body-file {file}

# close — explicit, then confirm
gh issue close {id} --reason completed
gh issue view {id} --json state,stateReason      # require CLOSED / COMPLETED

# create — a drafted follow-up ticket
gh issue create --title {title} --body-file {file}
```

**Create it into the epic the way `list` finds the epic.** The four resolutions need four
different things, and a follow-up that skips this vanishes from the next `list` and from any
resume: add `--milestone` for a milestone epic, `--label` for a label one, append it to the
parent's task list for a tracking issue, and add the project item for a project board.
Invent no grouping the epic doesn't already have.

**Child PR bodies carry `Refs #{id}`.** GitHub records a closing relationship only for a PR
targeting the default branch; a child PR targets `epic/{slug}`, so `Closes` there is a
promise the forge never keeps — the PR merges and the issue stays open. `Refs` states the
linkage truthfully and leaves closing to the explicit `close` above, which is what moves the
parent's sub-issue progress.

**The epic PR is the exception.** It targets the default branch, so its body carries
`Closes #{epic}` and the human's eventual merge closes the parent atomically.

Before using `start`, confirm the label exists — `gh label list --json name -q '.[].name'`.
Creating labels in someone's repo is not your call.

## Dependencies

```bash
gh issue view {id} --json body -q .body | grep -iE 'blocked by|depends on|after #'
```

GitHub's typed relationships are not exposed by `gh` in older versions, so body text and
task-list nesting carry most of the signal in practice.

## Ground checks

```bash
# Branch protection — needs repo admin; treat a failure as "unknown", not "unprotected"
gh api repos/{owner}/{repo}/rulesets 2>/dev/null
gh api repos/{owner}/{repo}/branches/{branch}/protection 2>/dev/null
```

If protection requires human review, merges will not happen. Report it; never self-approve
or push to the target to route around it.

## PR delivery

PR inspection, required-check proof, readiness, and exact-head merge are delivery
operations, not tracker operations. Use `check-ci` and `create-pr`; the latter's disclosed
forge-operations reference is the single source of truth for concrete GitHub commands.
