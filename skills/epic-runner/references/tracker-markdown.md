# Binding: a markdown checklist

The low end of the spectrum, and a real one — plenty of work starts as a list of to-dos in a
file. The whole tracker is a path.

## Shape

```markdown
# Export pipeline

- [ ] Add the export schema and migration
- [ ] Build the /export endpoint
  - [ ] Pagination
- [x] Spike: which serialization format
- [ ] Wire up the download button
```

## The five operations

| Operation | Implementation |
|---|---|
| `list` | Parse `- [ ]` lines in file order. Skip `- [x]` — already done. |
| `read` | The line itself, plus any indented prose beneath it. |
| `start` | No-op. |
| `comment` | No-op — surface it in the final report instead. |
| `close` | Rewrite `- [ ]` to `- [x]` on that line. |

**Issue ids** are positional — `item-1`, `item-2` — since there's nothing else to key on.
Keep them stable across a resume by re-deriving from file order, and note that this is why
editing the file mid-run will confuse a resume.

**Closing** means editing the user's file. Change only the checkbox characters on the one
line; leave text, indentation, and everything around it untouched. Anyone reading the diff
should see one `[ ]` become `[x]` and nothing else.

## Dependencies

There are no links, so:

- **Order is the signal.** Top-to-bottom. People write lists in the order they mean to do
  them, and discarding that throws away information the user already gave.
- **Nesting means dependency.** An indented item depends on its parent.
- **Then reason**, and announce what you infer.

Given no other structure, treat a flat list as strictly sequential. If several items are
obviously independent, say so in Phase 0 and let the user confirm before you reorder.

## What's missing

No comments and no epic ticket, so **the final report is the only record of the run.** Two
consequences worth honouring:

- Under `--new-issues=create` there's nowhere to file. Write drafted tickets into the state
  directory and, if the checklist file has a natural place for them, offer to append —
  after asking, since it's the user's file.
- Confirm the epic name and state directory in Phase 0 more carefully than usual. A resume
  keys off them, and a markdown "tracker" carries no id of its own to fall back on.
