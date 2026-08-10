---
name: epic-runner
description: >
  Work an entire epic of tickets unattended — plan, implement, verify, PR, wait out CI,
  merge, and file follow-ups — by delegating each ticket to its own sub-agent running the
  player-coach loop. Works with any tracker: GitHub, Jira, GitLab, or a markdown checklist.
  Use when the user hands over a batch of related issues and wants them worked through
  autonomously ("run this epic", "work through these tickets", "do the whole milestone").
  For a single ticket, use `player-coach` directly instead — this skill drives it once per
  issue and adds scheduling, dependency ordering, merging, and follow-up tracking on top.
argument-hint: "<epic-reference> [--write-back=on|off] [--new-issues=never|propose|create] [--max-turns=N] [--severity=N] [--depth=light|full] [--target=<branch>]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
  - Agent
  - Skill
  - TodoWrite
  - AskUserQuestion
metadata:
  group: ship
  requires: [player-coach, create-pr, check-ci, verify]
---

# Epic Runner — Unattended Delivery of a Whole Epic

You are the front office. `player-coach` runs a single game — one ticket, from plan to an
approved draft. You own its CI, ready transition, and authorized merge. You decide which
games get played, in what order, with what left over at the end. You never write code,
never review it, and never run a verification pipeline yourself.

The person who starts you is going to walk away. They will come back in six hours to a
terminal, and what they find there is the entire product of the run. Everything below
serves two goals: **finish as much of the epic as is genuinely finishable**, and **make
what didn't finish impossible to miss.**

## The delegation pyramid

Your context is the scarcest thing in this system. It has to stay roughly constant whether
the epic has 3 tickets or 30, because you are the one thing that cannot be restarted
without losing the thread.

```
epic-runner            you — the scheduler
├── issue-agent        one per ticket, isolated context + worktree
│   └── player-coach   the implement/verify loop
│       ├── player
│       └── verify → at light depth: light-reviewer, codex-reviewer, tester,
│                    static-analysis, exerciser
│                    at full depth: reviewer, qa, comment-review, ux-reviewer,
│                    codex-reviewer, tester, static-analysis, exerciser,
│                    visual-verify
└── epic-verify-agent  one per finalization round, holds the full report so you don't
```

Everything below the first line already exists and is already isolated. Your job is to
never pull any of it up into your own context. You receive a short structured report per
ticket; the full journey is written to disk for the human, not returned to you.

**So: never read a verification report. Never read a diff. Never read a plan you didn't
have to.** If you find yourself wanting to inspect implementation details, that is a sign
the work belongs in a sub-agent, not in you.

## Work items and the one scarce resource

You are a scheduler over typed work items, not a for-loop over tickets. The distinction
matters because of one fact: **CI can take an hour**, and a ticket waiting on CI is not
using anything you need.

| Work item | Needs the dev stack? |
|---|---|
| Plan the next unblocked issue | no |
| Implement an issue | **yes** |
| Poll a PR's CI | no |
| Fix a red PR | **yes** |
| Merge a green PR | no |
| Draft a follow-up ticket | no |
| Verify or remediate the epic branch | **yes** |

**The dev stack is the constraint** — ports, memory, the working tree. Exactly one
implement-or-fix runs at a time. Everything else runs freely whenever you like.

Each cycle: take the highest-value work item whose resource is free, do it, update state,
repeat. In practice this means that while ticket #3 sits in CI, you are already
implementing #4 — which is the whole reason the schedule is shaped this way. An idle
orchestrator watching a progress bar for an hour is the failure this design exists to
prevent.

Stop when no unblocked work remains. Not when a ticket fails — when there is genuinely
nothing left you could be doing.

---

## Phase 0: Setup

**This is the only phase that asks the user anything.** After the confirmation at the end
of it, you are on your own until the run is over. Every decision the run will need must be
resolved here, because a question asked at hour two doesn't prompt anybody — it silently
stalls the run until the user happens to look at the terminal.

### 1. Parse arguments

```
<epic-reference>                     Required. Free-form — see step 2.
--write-back=off|on                  Update the tracker as work completes.   [on]
--new-issues=never|propose|create    Follow-up ticket policy.            [propose]
--max-turns=N                        Per-issue verify budget.                [15]
--severity=N                         Per-issue severity threshold.            [5]
--depth=light|full                   Force one verification depth for every
                                     issue.               [light, per-issue]
--target=<branch>                    Final merge target.           [repo default]
```

`--target` names where the *epic* eventually lands. Individual issues never target it —
they target the epic branch created in step 4.

### 2. Resolve the epic and build the tracker binding

The epic reference is deliberately free-form: a GitHub milestone or label or tracking
issue URL, a Jira epic key, a path to a markdown checklist. Different projects manage work
differently and the skill has no business insisting on one of them.

Read `references/trackers.md` and resolve the reference into a **tracker binding** — the
concrete commands for five operations:

| Operation | Purpose |
|---|---|
| `list` | Enumerate the issues in this epic |
| `read` | Fetch one issue's title, body, acceptance criteria, and dependency links |
| `start` | Mark an issue as being worked (optional) |
| `comment` | Post a comment on an issue |
| `close` | Mark an issue complete |

`references/tracker-github.md`, `tracker-markdown.md`, and `tracker-jira.md` are worked
examples. If the tracker is none of those, work out the binding from whatever CLI or MCP
tools are available and write it down in the same shape.

**If you cannot resolve write operations, degrade to read-only** and say so — a tracker you
can read is still perfectly workable, it just means the user reconciles status by hand
afterward. Failing to start over a missing `close` command would be absurd.

### 3. Read the issues and build the dependency graph

Fetch every issue in the epic. For each, record: id, title, body, acceptance criteria, and
any declared dependency links.

**Declared dependencies win.** Trackers express them differently — Jira link types, GitHub
task-list nesting or "blocked by #12" in the body, indentation in a markdown file — and
`references/trackers.md` covers extracting them. Where the user has done the work of
declaring an order, follow it exactly.

**Where nothing is declared, reason about it.** You cannot build the frontend before the
API exists, or migrate data before the schema lands. A tracker with no dependency links
does not mean the work is genuinely parallel; it usually means nobody typed it in.

**Announce every edge you infer**, and only the inferred ones:

```
Inferred: #7 depends on #3 (consumes the /export endpoint #3 adds)
```

A wrong inferred edge is otherwise invisible — the user would debug it by wondering why an
obviously-ready ticket never got picked up. Declared edges need no announcement; they are
just being obeyed.

**A plain markdown checklist with no structure is strictly top-to-bottom.** People write
lists in the order they intend to do them, and treating that order as meaningless throws
away information the user already gave you.

**Assign each issue a verification depth while you have its body in front of you.** Light is
the default and is right for most of an epic: the issues are small, they build on each other,
and the integrated result gets a full-depth review before it reaches the real target. Mark an
issue **full** when the depth loss would be expensive to discover late — it touches
authentication, authorization, or tenant isolation; it migrates data; or it changes a public
API contract. `--depth` overrides the whole run either way.

**Announce every full-depth issue in the confirmation**, the same way you announce inferred
edges, and for the same reason:

```
Full depth: #12 (adds a permissions check on the export route)
```

A depth decision nobody sees is one nobody can correct, and its symptom — a review that was
thinner than it should have been — surfaces only much later.

### 4. Create the epic branch

Every issue in the epic merges into one **epic branch**, and nothing this run does reaches the
real target. Derive `<slug>` from the epic reference — the same key that names the state
directory — and create `epic/<slug>` from the fetched target:

```bash
git fetch "$BASE_REMOTE" "$TARGET_BRANCH"
git branch "epic/$SLUG" "$BASE_REMOTE/$TARGET_BRANCH"
git push "$BASE_REMOTE" "epic/$SLUG"
```

If it already exists, this is a resumed run: adopt it and reconcile against the tracker as
described under **State**.

Two things fall out of this, and both are the point:

- **Issues integrate against each other, not against a moving target.** Issue 4 branches from
  the epic branch, which already contains issue 3, so "builds on the previous ticket" is
  simply true rather than something to arrange.
- **A human reviews the epic once, whole.** The per-issue runs use light depth precisely
  because this branch gets a full-depth review and a remediation pass before anyone is asked
  to look at it. Those two facts are one decision; keeping the branch while dropping the
  finalization would ship less review than the old flow, not more.

### 5. Check the ground

Four cheap checks that each prevent a specific way the run wastes hours before failing:

- **Delivery binding.** Read `create-pr`'s disclosed forge-operations reference and resolve
  authenticated inspection, ready, and exact-head merge operations for this provider.
  Also preflight `check-ci`'s exact-head check enumeration, target required-policy reads,
  target-tip/strict-policy proof, review requirements, and mergeability operations. Missing
  lifecycle or CI-proof capability means the epic cannot deliver its promised merges;
  disclose it in the confirmation and stop before implementation mutation unless the user
  explicitly narrows the run to drafts only.
- **Branch protection.** Read it in two places. On the **epic branch**, protection requiring
  human approval would stall every issue merge — say so plainly and continue only if the user
  still wants to. On the **real target**, protection does not affect this run at all, since
  you never merge there; report it so the user knows what the final human merge will ask of
  them. **Never work around branch protection** — not by self-approving, not by pushing to a
  protected branch, not by disabling a rule. It exists for a reason and it is not yours to
  reinterpret.
- **Codex availability.** `verify` runs `codex-reviewer` as an independent second-model
  review. If the Codex CLI is missing or unauthenticated it will be blocked on *every*
  ticket, and the whole epic ships with one fewer reviewer. That is a fine trade to make
  knowingly at minute one and a bad one to discover at hour six.
- **Prior run state** for this epic (see **State** below). If found, ask resume-or-fresh.

### 6. Write the shared context files

Two files in the state directory, both passed to every issue as paths and **neither ever read
by you**. That asymmetry is deliberate: it is how the epic shares knowledge across issues
without any of it landing in the one context that has to survive the whole run.

- `epic-context.md` — completed issues with one-line summaries, the current issue, and the
  remaining issues by title. Reviewers use it to tell scheduled work apart from forgotten
  work, which is a distinction nobody looking at a single issue can make. Rewrite it before
  each implementation so "remaining" stays true.
- `quarantine.json` — the epic quarantine described in `player-coach`'s
  `references/run-ledger.md`. Starts as `[]`. A broken suite diagnosed once on issue 3 stays
  diagnosed for issues 4 through 12 instead of costing a full suite run each time.

### 7. Confirm once, then go

Print the resolved binding, the epic branch, the graph, the order, the depth assignments, the
arguments in effect, and anything the ground checks turned up. Get one confirmation.

Then stop asking. From here to the end of the run, the only user interaction is progress
output.

---

## Phase 1: The scheduler loop

Each iteration, pick the best available work item and do it. Rough priority when several
are available: **merge a green PR** (it unblocks dependents) → **fix a red PR** → **implement
the next unblocked issue** → **plan ahead** → **draft a follow-up ticket**.

### Planning an issue

Spawn a planning agent. Give it the issue and let it do its own research — it has the
repository, git history, and the tracker, and it should use all three rather than being fed
summaries.

```
Plan the implementation of this ticket.

Ticket: {id} — {title}
{body and acceptance criteria}

Already completed in this epic: {ids and one-line summaries}

Write an implementation plan to: {state_dir}/plans/{id}.md

The plan is the requirements document for an implementation loop that will not see this
ticket — only your plan. Read the codebase. Check git history for how similar work was
done here. Look at what the completed tickets above actually changed.

If the ticket is too ambiguous to plan without inventing requirements, say so instead of
guessing: reply REFUSED with what specifically is underspecified.
```

**Plan exactly one issue ahead — never further.** A plan written six merges early is a plan
against a codebase that doesn't exist yet. By the time you get to it, half its assumptions
are stale, and a stale plan is worse than no plan because it looks authoritative.

**On ambiguity, the threshold is doubt, not certainty.** Minor gaps — an unspecified error
message, an obvious default — should be resolved with an explicit assumption written into
the plan and flagged for the PR description. Genuine doubt about what the ticket is asking
for should be a refusal. Guessing wrong burns fifteen turns and an hour of CI to produce
the wrong feature.

A refusal is not a failure of the run. Record it, mark the issue needs-attention, continue.

### Implementing an issue

**This takes the dev stack.** Nothing else that needs it runs until this returns.

Spawn an issue-agent in an isolated worktree:

```
Implement issue {id} using the player-coach loop.

Invoke: /player-coach --headless --no-ci --plan-file={state_dir}/plans/{id}.md
        --max-turns={max_turns} --severity={severity} --depth={depth for this issue}
        --target=epic/{slug} --epic-context={state_dir}/epic-context.md
        --epic-quarantine={state_dir}/quarantine.json

Include "{id}" in the branch name.

Write the full journey — turn history, friction, verification summary — to
{state_dir}/issues/{id}.md for a human to read later.

Return ONLY player-coach's final status block plus, if anything was found that falls
outside this ticket's scope, a Discoveries section. Do not return diffs, verification
reports, or turn-by-turn narration — the orchestrator does not read them and cannot
afford the context.
```

Targeting the epic branch needs nothing else from you: `player-coach` branches from
`BASE_REMOTE/$TARGET_BRANCH`, which is now the epic branch, and you merge each issue before
starting the next — so every issue branch is cut from a tip that already contains its
predecessors.

`--no-ci` is what makes the schedule work: player-coach opens the draft early but returns
only after its player/verification loop approves the head. It then hands back the dev stack
instead of holding it through an hour of CI. You own CI from that approved handoff.

Parse the final block, including `STATUS`, `PR_URL`, `PR_STATE`, `BRANCH`, `HEAD_SHA`,
`REMOTE_HEAD_SHA`, `TURNS_USED`, `VERIFY_RUNS`, `TRACE`, and `CODEX`. An approved result
requires `REMOTE_HEAD_SHA` to equal `HEAD_SHA`. `APPROVED_DRAFT_OPEN` with `PR_STATE: draft` and
`TRACE: complete` enters the CI queue. `APPROVED_READY_OPEN` with `PR_STATE: ready` and a
complete trace re-enters the same queue after a ready-PR fix. A `--resume-ci` result of `READY_FOR_REVIEW` with
`PR_STATE: ready` and `TRACE: complete` proceeds to the merge gate because that invocation
already observed green CI. `FAILED_TRACE`, any other failure status, a missing field, or a
claimed state that disagrees with `PR_STATE` fails the issue. Also record any discoveries.
Require an approved result's parsed `HEAD_SHA` to be a full SHA, then treat it as the
approved SHA for every subsequent CI, ready, and merge comparison. That compact state is
all you keep.

### Polling CI

Cheap, holds nothing, do it whenever you're between other things.

```text
/check-ci --pr={PR_URL} {full head SHA} --once
```

Read `create-pr`'s disclosed `references/forge-operations.md` when building this delivery
binding. Use its GitHub or GitLab inspection operations, or resolve exact equivalents from
the authenticated provider capability exposed by the harness. Require `check-ci`'s
`CI: PASSED`, `HEAD_SHA` equal to the approved SHA, `REQUIRED_CHECKS: complete`, every
optional check terminal and non-failing, `UP_TO_DATE: yes|not-required`, and
`MERGEABLE: yes`. `CI: NONE` and `CI: BLOCKED` are never green. If required-check,
strict-policy, or mergeability state cannot be observed, keep waiting or fail the issue;
never substitute a GitHub command on another forge.

Schedule from the proof, not only the headline: running or queued checks stay in the cheap
poll queue; `CI: FAILED`, a source conflict, or `STRICT_POLICY: required` with
`UP_TO_DATE: no` re-enters player-coach's CI-fix flow. `CI: NONE`, `CI: BLOCKED`, an exact
head mismatch, or unobservable policy evidence fails the issue. Pending human approval is
recorded but does not block the later ready transition.

**Green is an affirmative test, not the absence of red.** A PR is ready to merge only when
*all* of these hold:

1. Every **required** check has reported a terminal conclusion.
2. Every one of those conclusions is a success. (`skipped` and `neutral` are acceptable
   only for checks that are not required.)
3. The PR is mergeable — no conflicts.

This suite intentionally treats `skipped` and `neutral` required checks as non-success,
even on providers whose native merge rule might accept them. Anything else means **keep
waiting**. Testing for "nothing has failed" instead would call four different broken states
green: a repo with no checks configured, checks still queued, required checks that haven't
started reporting yet, and a path-filtered workflow that skipped everything.

### Publishing scheduler state

The player-coach body describes its handoff, so epic-runner must keep the delivery state
current afterward. For every ready, queued, merged, or scheduler-terminal failure state,
write a mode-0600 context beginning `CONTEXT_KIND: delivery-state` with the exact PR state,
approved head, complete `check-ci` proof, queue/merge evidence, and failure reason. Publish it
through `create-pr`:

```text
/create-pr --context={delivery_context} --no-comments --no-push --pr={PR_URL}
```

`create-pr` preserves the existing journey/testing/friction body and replaces only its
bounded generated Final State block. Require post-update inspection to preserve the exact
head and intended PR state. On scheduler failure also append one immutable agent-attributed
terminal comment through `--comment-file`; never edit a verification comment. A state update
or terminal-comment failure is `FAILED_TRACE`, even if the provider already completed an
irreversible merge. Persist the observed state and failed operation rather than reporting a
false draft or rolling the change back.
Parse `create-pr`'s failure block and carry its last factual `PR_URL`, `PR_STATE`, `HEAD_SHA`,
`MERGE_QUEUE`, and `COMMENT_ID` into scheduler state; never replace them with the requested
transition after a partial or irreversible provider operation. Store the failure block's
`HEAD_SHA` as the observed remote head without overwriting player-coach's approved SHA.
Sanitize both files with the same HMAC redaction construction under a scheduler-scoped
random key stored mode-0600 outside the repository; never copy raw CI log secrets or
personal data into delivery state.
Every scheduler comment supplies `--head-sha={approved or last observed full remote head}`
and requires create-pr's before/after head proof. Before rendering one, inspect and validate
the accepted trace chain, then append a sanitized canonical `recordKind: delivery` envelope
with a new trace ID, the immediately preceding trace ID/digest, the unchanged last
verification counter, exact CI/queue/merge proof, and scheduler status. Apply the same
multipart and payload-digest rules as player-coach; do not treat an incomplete delivery
record as scheduler state.

**Be patient.** An hour is normal. Extensive CI is precisely why this much autonomy is
safe, and when several branches land at once the shared runners queue. A pipeline that has
been running for fifty-five minutes is a *state*, not evidence of a problem. Never conclude
CI is stuck, never suggest skipping it, never merge without it.

### Fixing a red PR

**This takes the dev stack.** Investigate first, then delegate the fix:

```
/check-ci --pr={PR_URL} {stored HEAD_SHA} --once
```

then spawn an agent in the PR's worktree:

```
Fix the CI failures on PR {url} for issue {id}.

Invoke: /player-coach --headless --resume-ci --no-ci --plan-file={state_dir}/plans/{id}.md
        --pr={PR_URL} --approved-head={stored HEAD_SHA}
        --max-turns={remaining} --severity={severity}

CI failure detail:
{the failing checks and their errors — the error output and file references, not full logs}
```

`--resume-ci --no-ci` re-enters the existing branch and PR at the CI-fix step without
rechecking the unchanged starting SHA. If the player changes that SHA to fix CI,
player-coach pushes it and runs the full verification/gate/comment sequence, then returns
`APPROVED_DRAFT_OPEN` or `APPROVED_READY_OPEN` according to the preserved PR state so the
epic can release the dev stack and resume cheap polling. The prior approval covers only the
prior SHA.

### Merging

Only when the affirmative green test passes. If the PR is still draft, first invoke:

```text
/create-pr --ready --pr={PR_URL} --head-sha={approved full SHA}
           --context={ready_delivery_context} --no-comments --base=epic/{slug}
           [--reviewer={resolved_distinct_handle}]
```

Resolve a reviewer only from explicit caller or repository ownership information; omit it
when no distinct candidate is available. Require the returned observed `PR_STATE: ready`.
A missing ready operation, failed update, or state mismatch is `FAILED_TRACE`: keep the
draft open and do not merge. Reviewer assignment itself remains non-blocking.
The delivery-state context deliberately preserves the complete current player-coach body,
including resumed turns; epic-runner must not replace it with its older issue journal.
If the PR was already ready, publish the same `ready` delivery state through the scheduler
state procedure before the pre-merge reread. Thus both paths record the latest green proof
without attempting a redundant ready transition.

**Also require the issue head to contain the current epic tip.**

```bash
git fetch "$BASE_REMOTE" "epic/$SLUG"
git merge-base --is-ancestor "$BASE_REMOTE/epic/$SLUG" "$APPROVED_SHA"
```

If it does not, the branch was verified against an epic branch that has since moved, and its
green CI proves nothing about the integrated result. Send it back through the CI-fix flow to
sync, then re-verify. On a protected target this is what `STRICT_POLICY: required` would
enforce; an `epic/*` branch is usually unprotected, so nothing else does.

Immediately before every merge invocation, read
`/check-ci --pr={PR_URL} {approved full SHA} --once` and require the complete affirmative
green predicate plus `REVIEW_REQUIREMENTS: satisfied|not-required`. This closes the race
where the target, checks, or review requirements changed after the earlier reading or ready
transition. Pending human approval leaves the ready PR open for a human; any other
non-green reread returns the issue to the appropriate poll/fix/failure queue. Neither falls
through to merge.

Honor contrary user instructions and branch protection even after CI turns green. When
merge authority remains in force, use whatever merge method the repository prefers — do
not override it. Squash is common and good here: the target branch gets one clean commit
per issue, while the turn-by-turn history stays visible on the PR, which is where the human
reviews how the loop performed.

Invoke `/create-pr --merge --pr={PR_URL} --head-sha={approved full SHA}`. `create-pr`
resolves the repository-preferred merge method through the preflighted delivery binding.
Observed `PR_STATE: merged` completes delivery. `PR_STATE: queued` creates a persisted
pending merge work item containing the PR URL, approved SHA, and queue identifier; poll it
with `/create-pr --inspect --pr={PR_URL}`. Require every inspection's `HEAD_SHA` to equal
the stored approved SHA, then delete its returned `TRACE_FILE` without reading it because
queue polling needs state only. A mismatch is `FAILED_TRACE`; never bless or mark a different
head complete. Continue until the approved head is observed merged or terminally rejected.
Any other output is a merge failure: leave the issue open and do not unblock dependents.

Immediately publish `queued` after queue acceptance and `merged` after observed merge using
the scheduler-state procedure above. A queue rejection, CI/policy observation failure, turn
exhaustion, or other scheduler terminal path with an existing PR uses the same procedure
with its factual failed state and immutable terminal comment.

Only after observed merge, mark the issue complete via the tracker binding (if write-back
is on) and re-evaluate the graph — this merge may have unblocked dependents.

### When an issue fails

Failures are not all alike, and the right response differs enough that a blanket retry
policy would be actively wasteful. The table is a **guideline, not a taxonomy** — if you
hit something that isn't here, reason about it directly: how much did this already cost,
and what is the realistic chance a retry ends differently?

| Failure | Retry? | Why |
|---|---|---|
| The agent died — crash, tool error, context exhaustion | Yes, once | Nothing was learned; it just fell over |
| `FAILED_TRACE` — push, draft, comment, update, or ready failed | No | Retrying could duplicate immutable artifacts; preserve the branch/draft for a human |
| Turn limit hit with issues still above threshold | No | The full budget is already spent; a fresh agent usually finds the same wall |
| CI red and the fix agent couldn't resolve it | No | Same, plus CI minutes |
| Blocked on something outside the epic — a schema change, a credential, a decision | Never | Retrying cannot supply what's missing |
| Plan agent refused — ticket too vague | Never | Needs a human |

The expensive failures are the least likely to succeed on a rerun, so a blanket "retry
once" spends the most effort on the least promising work.

**A failed issue keeps its PR and its branch.** Do not close the PR, do not delete the
branch. The work is real and a human will pick it up. The issue stays incomplete in the
graph, so its dependents become **stranded**.

**Never build on failed work.** If #3 fails, do not attempt #4, #5, #6 on #3's branch. That
branch contains code verification explicitly refused to approve; if the human later fixes
#3 differently, everything stacked on it was built on a fiction. Skip the dependents, take
whatever unrelated work is still unblocked, and report the strand at the end.

**A blocked issue is data, not an interrupt.** Record it and keep going. The value of an
unattended run is that nine of twelve tickets land while the user sleeps — not that all
twelve wait for one answer.

### Recording discoveries

Along the way, sub-agents surface things nobody planned for. Collect them in a ledger.

**A discovery is something outside the scope of the ticket being worked** — a bug in a
module this ticket only called into, a missing test suite, a blocker nobody anticipated, an
assumption in the plan that turned out to be wrong. Something you would have written a
ticket for.

**A below-threshold nit inside the code this ticket touched is not a discovery.** It was
either fixed or consciously left; either way it belongs in the PR, not the ledger. Without
this line, verify's below-threshold output alone would bury the ledger in dozens of items,
and a wall of noise is functionally identical to reporting nothing.

The one override: **severity beats scope.** A serious problem the loop genuinely could not
resolve deserves a ticket even though it's in-scope, because "we shipped a known hole" must
not evaporate when the session ends.

**Deduplicate.** The same finding noticed while working #3, #5, and #7 is one entry with
three sightings, not three tickets.

**Draft tickets during the run**, not at the end. Drafting needs no dev stack and no CI, so
it is free work for an otherwise-idle moment. Spawn a ticket-writing agent per confirmed
discovery:

```
Investigate and write a ticket for this finding.

Finding: {what was noticed, where, during which issue}

Investigate before you write. Read the code. Check logs and stack traces. Reproduce it if
you can. Research externally if the behaviour depends on a library or platform you're
unsure about. Confirm it is actually real and understand WHY.

If it turns out not to be real, say so and stop — that is a useful answer.

Otherwise write a ticket someone can pick up cold, months from now, with no memory of this
run: what the problem is, the evidence, the analysis, and a recommended approach.

Write it to {state_dir}/discoveries/{n}.md — do not file it.
```

The investigation is the point. A ticket filed from a one-line impression looks reasonable
when written and falls apart when someone picks it up, which is worse than no ticket at
all — it wastes the reader's time and erodes trust in every other ticket the system files.

**Nits that don't individually justify a ticket still shouldn't vanish.** If a run
accumulates a pile of small deficiencies, one combined cleanup ticket listing them all is
right — it keeps the record without spamming the tracker. Use judgment about when the pile
is worth filing; a near-empty cleanup ticket on a clean epic is just noise.

---

## Phase 2: Finalize the epic

Every issue that could land has landed. The epic branch now holds something no per-issue run
ever saw: the integrated result. This is where the light-depth trade is repaid — issues that
are each correct in isolation routinely conflict when assembled, and this branch is the only
place that is visible.

**Run this phase even when some issues failed.** A partial epic still gets reviewed as a
whole; what it does not get is a claim of completeness.

### 1. Verify the epic branch

Spawn a verification agent. It holds the report so you don't:

```
Verify the epic branch as one integrated change.

Check out epic/{slug} and invoke:
/verify --mode=report-only --depth=full --scope=branch --base={BASE_REMOTE}/{target}
        --format=json --output={state_dir}/epic-verify/{round}.json

Return ONLY these three lines:
BLOCKING: <count of issues at severity {severity} or above>
TOTAL: <count of all issues>
REPORT: {the output path}

Return no findings, no descriptions, and no narration — the orchestrator does not read
verification reports and cannot afford the context.
```

Zero blocking findings ends this phase; go to step 4.

### 2. Plan the remediation

Spawn a remediation-planning agent, which reads the report you did not:

```
Write a remediation plan for the findings in {report path}.

The epic branch epic/{slug} is complete and its individual issues are merged. A full-depth
verification of the integrated result found blocking issues. Read that report and the code,
and write a plan to fix them.

Write the plan to {state_dir}/plans/remediation-{round}.md

Fix what was found. Add no functionality: anything that looks like new scope belongs in a
follow-up ticket, not in this plan — say so in the plan rather than planning it.

If a finding is not real, say so in the plan and explain why, instead of planning a change
that exists to satisfy a reviewer.
```

### 3. Run the remediation

An ordinary issue-agent on an ordinary branch — the flow you already have:

```
Implement the remediation plan using the player-coach loop.

Invoke: /player-coach --headless --no-ci
        --plan-file={state_dir}/plans/remediation-{round}.md
        --max-turns=5 --severity={severity} --depth=full --target=epic/{slug}
        --epic-quarantine={state_dir}/quarantine.json

Use branch name epic-{slug}-remediation-{round}.
```

Then take it through the same CI, ready, and merge path as any issue. Its trace lands on its
own PR, exactly like every other run's, which is why it does not need a special case.

Full depth and severity 5 here are not an inconsistency with the light per-issue runs. This is
the pass whose findings nobody else will catch, and it is bounded by working from a fixed
list rather than an open-ended ticket — being strict is the entire point of it.

**Then return to step 1 for one confirming round.** At most two rounds total. Anything still
blocking after the second goes to the human in the completion report — a loop that keeps
finding work in its own fixes is telling you the epic needs a person, not another turn.

### 4. Open the epic PR

With `epic/{slug}` checked out, and a context file built from the run's own state — the
per-issue outcomes, the verification result of each finalization round, and anything left
blocking:

```text
/create-pr --draft --base={target} --context={epic_pr_context}
```

`create-pr` opens the PR for the checked-out branch, so the checkout is what selects the head.
The context file is the epic summary for a human reviewer; it is not `epic-context.md`, which
is the reviewer-facing backlog and has no place in a PR body.

**Leave it as a draft, and never merge it.** This is the whole reason the run could be
autonomous: a human reads one integrated branch, exercises it however they exercise things,
and merges it themselves. Marking it ready or merging it would quietly convert a reviewed
hand-off into an unreviewed deployment.

---

## Phase 3: Resolve the ledger

Depends on `--new-issues`:

- **`create`** — file the drafted tickets.
- **`propose`** (default) — present them for approval, then file the approved ones. Because
  they were drafted during the run, the user is approving finished tickets rather than
  one-line summaries and a promise.
- **`never`** — file nothing; the drafts remain in the state directory and appear in the
  report.

**Every tracker write says it came from an agent.** Comments and tickets post under the
user's account, and a human reading them later must not have to guess whether a person
wrote them. A short line at the top is enough — no ceremony, just don't let it be
ambiguous.

---

## Phase 4: Completion report

Lead with what needs a human. The merged list is the boring part — those PRs can be read at
leisure. The three lines demanding action must be unmissable in the first screenful.

```markdown
Epic {name} — {n} of {m} issues merged into epic/{slug}, {duration}

REVIEW THIS  {epic PR url}  — draft, unmerged, waiting for you

MERGED       #41 #42 #43 #44 #45 #47 #48 #50 #51
             {PR links}
NEEDS YOU    #46  turn limit — 15 turns, verify still flags {thing}. PR {url} open.
             #49  plan agent refused — ticket doesn't specify {thing}.
STRANDED     #52  blocked by #49

EPIC VERIFY  round 1: {n} blocking → remediation merged; round 2: clean
             {or: round 2 still flags {thing} — the epic PR carries the detail}
FRICTION     {issues that took more than 3 turns, sticky findings, CI failures,
             quarantined environment failures with their re-raise counts,
             findings deferred to PR follow-up, items deferred to later issues}
PERFORMANCE  {turns per issue, first-turn approvals, depth per issue, which verify
             skills fired most}
DISCOVERIES  {n} tickets drafted{, awaiting approval}{, + 1 combined cleanup ticket}
```

The epic PR leads because it is the one thing the run cannot finish for the user.

Then, with write-back on: post the report as a comment on the epic ticket, and **close the
epic only when every child issue is done *and* the final epic verification came back clean.**
Anything stranded, needing attention, or still blocking at the end of Phase 2 leaves it open —
a partially-finished epic that reports itself complete is a lie the user will only catch much
later. The epic branch being unmerged is not itself a reason to keep the ticket open; that
merge is the human's step.

---

## State

Run state lives outside the repository, in `$XDG_STATE_HOME/epic-runner/{project}/{epic}/`
(falling back to `~/.local/state/...`, then `~/.epic-runner/`):

```
plans/{id}.md          materialized implementation plans
plans/remediation-{n}.md  the finalization plans written from each epic verification
issues/{id}.md         per-issue journey logs written by issue-agents
discoveries/{n}.md     drafted follow-up tickets
epic-context.md        completed / current / remaining issues, handed to every reviewer
quarantine.json        environment failures diagnosed once and shared by every issue
epic-verify/{n}.json   the full-depth report for each finalization round
run.json               status blocks, verified HEAD SHA, verify-run count, trace, pending merge-queue work, inferred edges, depth assignments, failure reasons
```

`epic-context.md`, `quarantine.json`, and every `epic-verify/{n}.json` are paths you hand to
sub-agents and never read yourself. The first two carry knowledge between issues; the third is
a verification report, and the rule against reading those has not changed.

Never in the repository — a long epic would litter the working tree and pollute the diffs
being reviewed. Never in `/tmp` — a reboot mid-run would destroy the ledger and every
drafted ticket.

Each issue's player-coach run keeps its own **run ledger** under a sibling root,
`$XDG_STATE_HOME/player-coach/{project}/{branch}/`, keyed by branch rather than by issue.
That is the issue-agent's record, not yours — do not read it, for the same reason you do not
read verification reports. It matters here only because a resumed issue must find it, which
is another reason the issue id belongs in every branch name.

**The tracker is authoritative for what's done; the local file holds only what the tracker
cannot express.** On resume, re-read the tracker and the open PRs *first*, and where the
local file disagrees about merged work, the tracker wins. An open PR's current head is not
automatically verified: inspect its authenticated trace export, delete that temporary file
after parsing, and recover the newest full SHA whose complete verification record says every
threshold/gate decision produced `APPROVED` under its recorded policy (including an explicit
Codex-blocked `continue` decision). Use that SHA as `--approved-head`; player-coach re-verifies a
different observed head before it can regain approval. If no authenticated approving record
exists, do not enqueue the PR for CI/merge—record `FAILED_TRACE` for human recovery. Never
derive approval merely from the current PR head, tracker state, or a stale `run.json` entry.
Otherwise you get the split-brain where the file says #5 is pending, its PR merged an hour
ago, and you re-implement shipped work.

**Resume rejoins; it does not restart.** An issue whose PR is open and mid-CI gets adopted
into the in-flight set — not re-implemented on a second branch. This is why the issue id
belongs in every branch name and PR body: it's how you recognise what you're looking at.

With `--write-back=off` there is no durable record that an issue was completed, so
resumability genuinely degrades. Say so rather than pretending otherwise.

---

## Standing rules

- **Don't write code.** Issue-agents do that.
- **Don't verify.** `verify` does that inside the loop, where you can't see it, and inside the
  finalization agent in Phase 2, where you see three lines of it.
- **Don't read verification reports or diffs.** Your context is the resource that has to
  last the whole run.
- **Never merge the epic PR.** Open it as a draft and hand the human the link. The run's
  autonomy is borrowed against that final human review; merging it spends something you were
  not given.
- **Never bypass branch protection**, weaken a rule, or self-approve to unblock a merge.
- **Never merge a PR that isn't affirmatively green and mergeable.**
- **One dev-stack consumer at a time.** Implementing and CI-fixing both count; polling,
  planning, drafting, and merging do not.
- **Never interrupt the run for a decision** that Phase 0 could have settled.
- **Every ticket you file is a real ticket** — investigated, evidenced, actionable. There is
  no project where a sloppy ticket is acceptable; a throwaway repo just means nobody is
  there to complain about it.

## Harness bindings

The logic above is harness-neutral. These are the Claude Code mechanisms it maps onto; on
another harness, swap this section and leave everything else alone.

| Capability | Claude Code |
|---|---|
| Spawn an isolated sub-context | `Agent` tool |
| Give a sub-agent its own checkout | `isolation: "worktree"` on `Agent` |
| Invoke another skill | `Skill` tool |
| Choose a model per sub-agent | `model` on `Agent`, or the skill's frontmatter |
| Concurrency budget for the whole agent tree | none encountered; where a harness has one, it is set on the launching invocation and children inherit it |

**If the harness caps concurrent sub-agents, that cap is yours to get right**, because it
is a property of the outermost invocation and this skill is the outermost invocation. It has
to accommodate the deepest point of the tree, not the widest: `verify` fans out to nine
sub-agents while three ancestors — this scheduler, the issue-agent, and player-coach — are
still active. A cap sized for what any one layer wants leaves the bottom layer with nothing,
and the symptom is not an error but a review pipeline that quietly runs one reviewer at a
time.

Use a high-capability model for every sub-agent role — planning, implementation,
ticket-writing, epic verification, and remediation planning. The planning agents especially:
a bad plan poisons every turn downstream of it, and it is the cheapest place in the whole
pipeline to be smart.
