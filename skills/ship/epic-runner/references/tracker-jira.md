# Binding: Jira

**Sketch, not a worked example.** This has not been exercised against a real instance. Treat
it as a starting shape, verify each operation in Phase 0 before relying on it, and correct
this file once you've run it for real.

Jira is the case the abstraction exists for: a first-class epic type, typed dependency
links, and a configurable workflow that differs per project.

## Access

Either an MCP server for Atlassian or the `jira` CLI. **Check which is actually available
and authenticated in Phase 0** — MCP servers that authenticate interactively may be absent
in a headless run, which is exactly when this skill is used.

## The six operations

| Operation | Approach |
|---|---|
| `list` | JQL: `parent = {EPIC-KEY} ORDER BY rank ASC`, or `"Epic Link" = {EPIC-KEY}` on older instances |
| `read` | Fetch the issue: summary, description, acceptance criteria field, issue links |
| `start` | Transition to the in-progress status **for this project's workflow** |
| `comment` | Add a comment |
| `close` | Transition to done |
| `create` | Create an issue in the same project, linked to the epic as `list` expects to find it |

**Transitions are the trap.** Status names are per-project (`In Progress`, `In Development`,
`Started`) and transitions are gated by the workflow — you cannot set a status, only apply an
available transition. Fetch the available transitions for one issue in Phase 0 and map them
to `start` and `close` then, rather than discovering at hour three that `close` isn't
reachable from the current state.

If a transition isn't available, degrade to read-only for that operation and report it.
Forcing a workflow is not something to attempt unattended.

## Dependencies

Jira has real typed links, so this is the one tracker where inference should be rare:

- `is blocked by` → a genuine dependency edge
- `blocks` → the inverse
- `relates to` → **not** a dependency; ignore it for ordering
- Sub-tasks → depend on their parent

Also check for rank ordering, which often encodes intended sequence where links don't.

Grep descriptions for prose dependencies anyway (`blocked by PROJ-4`) — people write them
even in a tracker that supports real links.

## Cautions

**Jira is where "enterprise" applies.** These projects are the ones most likely to have a
defined scope, a release the team is protecting, and colleagues who will read whatever gets
filed. Two things follow:

- Default `--new-issues` to `propose` and honour it strictly. A ticket appearing unbidden in
  a managed backlog is a real problem for the user, whatever you think of the process.
- Transitions and comments fire notifications, sometimes to a lot of people. Write at
  meaningful moments only — start, PR link, done, one epic summary. Never per turn.

The AI-attribution line matters more here than anywhere else: colleagues who never agreed to
work alongside an agent will read these comments.
