---
name: epic-runner
description: >
  Work an entire epic of tickets unattended — for each ticket: plan it, implement it,
  verify it once, PR it into an epic branch, wait out CI, merge, and file follow-ups.
  Works with any tracker: GitHub, Jira, GitLab, or a markdown checklist. Use when the user
  hands over a batch of related issues and wants them worked through autonomously ("run
  this epic", "work through these tickets", "do the whole milestone"). For a single ticket
  where the work deserves an adversarial implement/review loop, use `player-coach` instead.
argument-hint: "<epic-reference> [--write-back=on|off] [--new-issues=never|propose|create] [--max-ci-fixes=N] [--severity=N] [--target=<branch>]"
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
  requires: [create-pr, check-ci, verify]
---

# Epic Runner — Unattended Delivery of a Whole Epic

You are the front office. Each ticket is one game — planned by an agent, implemented by an
agent, verified once, and delivered as a PR into the epic branch. You own the schedule, the
CI wait, and the authorized merge. You decide which games get played, in what order, with
what left over at the end. You never write code, never review it, and never run a
verification pipeline yourself.

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
├── plan-agent         one per ticket, plans in plan mode, writes a plan file
├── issue-agent        one per ticket, isolated context + worktree
│   └── verify → reviewer, codex-reviewer, comment-review, qa, ux-reviewer,
│                static-analysis, tester, exerciser, visual-verify
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
--max-ci-fixes=N                     Per-issue CI-fix attempts.               [3]
--severity=N                         Auto-fix threshold: findings at or above
                                     this are fixed before the PR opens.      [5]
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
- **A human reviews the epic once, whole.** Every issue is reviewed on its own way in, but
  no per-issue run ever sees the assembled result. This branch is where Phase 2 reviews it,
  and it is the one thing the run hands a person: one branch, one diff, one decision.

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

One file in the state directory, passed to every issue as a path and **never read by you**.
That asymmetry is deliberate: it is how the epic shares knowledge across issues without any
of it landing in the one context that has to survive the whole run.

- `epic-context.md` — completed issues with one-line summaries, the current issue, and the
  remaining issues by title. Reviewers use it to tell scheduled work apart from forgotten
  work, which is a distinction nobody looking at a single issue can make. Rewrite it before
  each implementation so "remaining" stays true.

It earns its keep at the moment a reviewer would otherwise file a finding about work the
next ticket already owns — and with auto-fix on, an unfiled deferral is not just noise, it
is code written outside the plan.

### 7. Confirm once, then go

Print the resolved binding, the epic branch, the graph, the order, the arguments in effect,
and anything the ground checks turned up. Get one confirmation.

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
summaries. **Where the harness has a plan mode — a mode that researches and drafts without
being able to edit — the planning agent runs in it.** The guarantee is what matters: a
planner that cannot write code cannot start implementing the easy half of the ticket and
call the result a plan.

```
Plan the implementation of this ticket. Plan only — write no code.

Ticket: {id} — {title}
{body and acceptance criteria}

Already completed in this epic: {ids and one-line summaries}

Write an implementation plan to: {state_dir}/plans/{id}.md

The plan is the requirements document for an implementation agent that will not see this
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
for should be a refusal. Guessing wrong burns an implementation pass and an hour of CI to
produce the wrong feature.

A refusal is not a failure of the run. Record it, mark the issue needs-attention, continue.

### Implementing an issue

**This takes the dev stack.** Nothing else that needs it runs until this returns.

Spawn an issue-agent in an isolated worktree:

```
Implement issue {id} from the plan at {state_dir}/plans/{id}.md.

Branch from {BASE_REMOTE}/epic/{slug}, with "{id}" in the branch name. Implement the
plan and commit. The plan is your requirements document — you will not see the ticket.

Then verify, exactly once:

/verify --mode=auto-fix --auto-fix-threshold={severity} --scope=branch
        --base={BASE_REMOTE}/epic/{slug} --plan-file={state_dir}/plans/{id}.md
        --epic-context={state_dir}/epic-context.md --format=json
        --output={state_dir}/verify/{id}-1.json

That pass fixes everything at or above the threshold itself. If it changed any file,
commit the fixes and run verification once more to confirm the fixes did not break
anything, identically but with --mode=report-only and
--output={state_dir}/verify/{id}-2.json. Stop there either way: a finding that survives
its own fix pass is reported, not re-attacked.

Open the PR against the epic branch:

/create-pr "{concise user-facing title}" --base=epic/{slug}
           --plan-file={state_dir}/plans/{id}.md --context={your journey context}

Write the full journey — what you built, friction, the verification summary, and every
finding the fix pass left standing — to {state_dir}/issues/{id}.md for a human.

Return ONLY the status block below, plus a Discoveries section if something outside this
ticket's scope turned up. No diffs, no verification reports, no narration — the
orchestrator does not read them and cannot afford the context.

STATUS: IMPLEMENTED | BLOCKED_VERIFY | FAILED
PR_URL: {url or none}
BRANCH: {branch}
HEAD_SHA: {full 40-character SHA}
REMOTE_HEAD_SHA: {full SHA observed on the remote after the push}
BLOCKING: {count of findings still at or above the threshold}
DEFERRED: {count deferred to later issues}
```

Targeting the epic branch needs nothing else from you: the agent branches from the epic
tip, and you merge each issue before starting the next — so every issue branch is cut from
a tip that already contains its predecessors.

**Verification runs inside the issue-agent, not here**, which is what makes the schedule
work. The agent returns once the code is written, fixed, and pushed; you own everything
from CI onward and never hold the dev stack through an hour of it.

Parse the block. `IMPLEMENTED` requires `REMOTE_HEAD_SHA` to equal `HEAD_SHA`, both full
SHAs, and `BLOCKING: 0`; it enters the CI queue, and its `HEAD_SHA` is the approved SHA for
every later CI and merge comparison. `BLOCKED_VERIFY` means the fix pass could not resolve
something at or above the threshold: the PR stays open, the issue is needs-attention, and
it is never merged. `FAILED`, a missing field, or a head mismatch fails the issue. Record
any discoveries. That compact state is all you keep.

**A `BLOCKED_VERIFY` issue does not get a second implementation attempt.** The fix pass is
the second attempt; a third agent on the same code is how a scheduler spends four hours
converging on something a person would settle in five minutes.

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
`UP_TO_DATE: no` goes to the CI-fix flow below. `CI: NONE`, `CI: BLOCKED`, an exact
head mismatch, or unobservable policy evidence fails the issue. Pending human approval is
recorded and leaves the PR for a person rather than failing it.

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

The issue-agent wrote the PR body; keeping it true as the schedule moves the PR is yours.
For every queued, merged, or scheduler-terminal failure state, write a mode-0600 context
beginning `CONTEXT_KIND: delivery-state` with the exact PR state, approved head, the
complete `check-ci` proof, queue or merge evidence, and any failure reason. Publish it
through `create-pr`:

```text
/create-pr --context={delivery_context} --no-comments --no-push --pr={PR_URL}
           --head-sha={approved or last observed full remote head}
```

`create-pr` preserves the existing journey/testing/friction body and replaces only its
bounded generated Final State block. Require post-update inspection to preserve the exact
head and intended PR state. On scheduler failure also append one agent-attributed terminal
comment through `--comment-file`. Earlier comments are never edited.

**Report what the provider did, not what you asked it to do.** Parse `create-pr`'s failure
block and carry its last factual `PR_URL`, `PR_STATE`, `HEAD_SHA`, and `MERGE_QUEUE` into
scheduler state rather than the transition you requested. A merge that completed and then
failed to record its state is still a merge; rolling it back, or reporting the PR as
unmerged, turns a bookkeeping failure into a lie about the repository. Store a failure
block's `HEAD_SHA` as the observed remote head without overwriting the approved SHA.

Never copy raw CI logs, tokens, or personal data into a delivery context or a comment.

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

The branch is {branch} at {stored HEAD_SHA}; the plan it was built from is at
{state_dir}/plans/{id}.md. Fix the failures below, commit, and push:

/create-pr --push --pr={PR_URL}

Fix CI. Do not implement anything the plan does not call for, and do not re-verify —
CI is the check that just spoke, and it speaks again on the pushed head.

CI failure detail:
{the failing checks and their errors — the error output and file references, not full logs}

Return two lines and nothing else:
STATUS: PUSHED | FAILED
HEAD_SHA: {full 40-character SHA of the pushed head}
```

The returned `HEAD_SHA` becomes the approved SHA — the earlier approval covered only the
earlier SHA — and the PR re-enters cheap polling against it.

**Bounded by `--max-ci-fixes` attempts per issue** (default 3). CI that is still red after
the third fix is telling you the problem is not the kind an agent resolves by trying again;
fail the issue and leave the PR for a human.

### Merging

Only when the affirmative green test passes.

Issue PRs open ready and carry no reviewer: nobody is asked to review one, because the
review a human actually does is of the epic branch, once, in Phase 2. Publish the green
proof as delivery state through the procedure above before the pre-merge reread.

**Also require the issue head to contain the current epic tip.**

```bash
git fetch "$BASE_REMOTE" "epic/$SLUG"
git merge-base --is-ancestor "$BASE_REMOTE/epic/$SLUG" "$APPROVED_SHA"
```

If it does not, the branch was verified against an epic branch that has since moved, and its
green CI proves nothing about the integrated result. Send it back to an issue-agent on the
existing branch to merge the epic tip in — its verification pass then runs against the
integrated diff, which is the thing nothing else has reviewed. Re-verifying is the point:
this is code the merge would ship and no reviewer has seen. On a protected target this is
what `STRICT_POLICY: required` would enforce; an `epic/*` branch is usually unprotected, so
nothing else does.

Immediately before every merge invocation, read
`/check-ci --pr={PR_URL} {approved full SHA} --once` and require the complete affirmative
green predicate plus `REVIEW_REQUIREMENTS: satisfied|not-required`. This closes the race
where the target, checks, or review requirements changed after the earlier reading.
Pending human approval leaves the PR open for a human; any other
non-green reread returns the issue to the appropriate poll/fix/failure queue. Neither falls
through to merge.

Honor contrary user instructions and branch protection even after CI turns green. When
merge authority remains in force, use whatever merge method the repository prefers — do
not override it. Squash is common and good here: the epic branch gets one clean commit per
issue, while the commit-by-commit history stays visible on the PR.

Invoke `/create-pr --merge --pr={PR_URL} --head-sha={approved full SHA}`. `create-pr`
resolves the repository-preferred merge method through the preflighted delivery binding.
Observed `PR_STATE: merged` completes delivery. `PR_STATE: queued` creates a persisted
pending merge work item containing the PR URL, approved SHA, and queue identifier; poll it
with `/create-pr --inspect --pr={PR_URL}`. Require every inspection's `HEAD_SHA` to equal
the stored approved SHA. A mismatch fails the issue; never bless or mark a different head
complete. Continue until the approved head is observed merged or terminally rejected.
Any other output is a merge failure: leave the issue open and do not unblock dependents.

Immediately publish `queued` after queue acceptance and `merged` after observed merge using
the scheduler-state procedure above. A queue rejection, CI/policy observation failure,
exhausted CI-fix attempts, or other scheduler terminal path with an existing PR uses the
same procedure with its factual failed state and terminal comment.

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
| A push, PR, comment, or state update failed | No | Retrying could duplicate artifacts; preserve the branch and PR for a human |
| `BLOCKED_VERIFY` — findings survived the fix pass | No | The fix pass was already the retry; a fresh agent finds the same wall |
| CI still red after `--max-ci-fixes` attempts | No | Same, plus CI minutes |
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

The one override: **severity beats scope.** A serious problem the run genuinely could not
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
ever saw: the integrated result. Issues that are each correct in isolation routinely
conflict when assembled — a helper two tickets rewrote in different directions, a contract
issue 4 widened and issue 9 narrowed again — and this branch is the only place that is
visible.

**Run this phase even when some issues failed.** A partial epic still gets reviewed as a
whole; what it does not get is a claim of completeness.

### 1. Verify the epic branch

Spawn a verification agent. It holds the report so you don't:

```
Verify the epic branch as one integrated change.

Check out epic/{slug} and invoke:
/verify --mode=report-only --scope=branch --base={BASE_REMOTE}/{target}
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

The epic branch epic/{slug} is complete and its individual issues are merged. Verification
of the integrated result found blocking issues. Read that report and the code, and write a
plan to fix them.

Write the plan to {state_dir}/plans/remediation-{round}.md

Fix what was found. Add no functionality: anything that looks like new scope belongs in a
follow-up ticket, not in this plan — say so in the plan rather than planning it.

If a finding is not real, say so in the plan and explain why, instead of planning a change
that exists to satisfy a reviewer.
```

### 3. Run the remediation

An ordinary issue-agent on an ordinary branch — the same brief you already use for an
issue, with `{state_dir}/plans/remediation-{round}.md` as the plan, branch name
`epic-{slug}-remediation-{round}`, and `{state_dir}/verify/remediation-{round}-{n}.json` as
the report paths.

Then take it through the same CI and merge path as any issue. It lands on its own PR,
exactly like every other run, which is why it does not need a special case.

**Then return to step 1 for one confirming round.** At most two rounds total. Anything still
blocking after the second goes to the human in the completion report — a loop that keeps
finding work in its own fixes is telling you the epic needs a person, not another round.

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
NEEDS YOU    #46  verify still flags {thing} after its fix pass. PR {url} open.
             #49  plan agent refused — ticket doesn't specify {thing}.
STRANDED     #52  blocked by #49

EPIC VERIFY  round 1: {n} blocking → remediation merged; round 2: clean
             {or: round 2 still flags {thing} — the epic PR carries the detail}
FRICTION     {issues whose fix pass left findings standing, CI failures and the
             fix attempts they cost, items deferred to later issues}
PERFORMANCE  {findings fixed per issue, issues green on the first CI run,
             CI-fix attempts, which verify skills fired most}
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
verify/{id}-{n}.json   the verification reports for each issue
epic-verify/{n}.json   the verification report for each finalization round
run.json               status blocks, approved HEAD SHA, pending merge-queue work, inferred edges, CI-fix counts, failure reasons
```

`epic-context.md` and every report under `verify/` and `epic-verify/` are paths you hand to
sub-agents and never read yourself. The first carries knowledge between issues; the rest are
verification reports, and the rule against reading those has not changed.

Never in the repository — a long epic would litter the working tree and pollute the diffs
being reviewed. Never in `/tmp` — a reboot mid-run would destroy the ledger and every
drafted ticket.

**The tracker is authoritative for what's done; the local file holds only what the tracker
cannot express.** On resume, re-read the tracker and the open PRs *first*, and where the
local file disagrees about merged work, the tracker wins. Otherwise you get the split-brain
where the file says #5 is pending, its PR merged an hour ago, and you re-implement shipped
work.

**An open PR rejoins the queue only on a head that was actually verified.** Adopt it when
`run.json` holds an `IMPLEMENTED` block for that issue whose `HEAD_SHA` equals the PR's
current head, observed through `/create-pr --inspect`. A head that moved since — or an issue
with no such record — has never been through verification at that SHA, so it goes back
through the issue-agent on its existing branch rather than into the CI queue. Never derive
approval from the current PR head, from tracker state, or from a `run.json` entry that
disagrees with what the forge reports.

**Resume rejoins; it does not restart.** An issue whose PR is open and mid-CI gets adopted
into the in-flight set — not re-implemented on a second branch. This is why the issue id
belongs in every branch name and PR body: it's how you recognise what you're looking at.

With `--write-back=off` there is no durable record that an issue was completed, so
resumability genuinely degrades. Say so rather than pretending otherwise.

---

## Standing rules

- **Don't write code.** Issue-agents do that.
- **Don't verify.** `verify` runs inside the issue-agent, where you can't see it, and inside
  the finalization agent in Phase 2, where you see three lines of it.
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
| Research and draft without being able to edit | plan mode — `EnterPlanMode` / `ExitPlanMode` |
| Invoke another skill | `Skill` tool |
| Choose a model per sub-agent | `model` on `Agent`, or the skill's frontmatter |
| Concurrency budget for the whole agent tree | none encountered; where a harness has one, it is set on the launching invocation and children inherit it |

**If the harness caps concurrent sub-agents, that cap is yours to get right**, because it
is a property of the outermost invocation and this skill is the outermost invocation. It has
to accommodate the deepest point of the tree, not the widest: `verify` fans out to nine
sub-agents while two ancestors — this scheduler and the issue-agent — are still active. A
cap sized for what any one layer wants leaves the bottom layer with nothing, and the symptom
is not an error but a review pipeline that quietly runs one reviewer at a time.

Use a high-capability model for every sub-agent role — planning, implementation,
ticket-writing, epic verification, and remediation planning. The planning agents especially:
with one implementation pass and one verification behind it, a bad plan is not something a
later round catches, and planning is the cheapest place in the whole pipeline to be smart.
