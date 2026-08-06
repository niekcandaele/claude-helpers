---
name: create-pr
description: >
  Create a pull request or merge request with rich, context-aware description
  and inline review comments. Analyzes changes to explain what changed, why,
  and where reviewers should focus attention. Handles branch creation, commits,
  push, platform detection (GitHub/GitLab), and label assignment. Use this skill
  whenever creating a PR/MR, even for simple changes — it always produces better
  descriptions than a manual `gh pr create`. Accepts optional context from callers
  like player-coach for even richer descriptions with implementation journey and
  friction logs.
argument-hint: "[PR title] [--context=path] [--no-comments] [--base=<branch>] [--plan-file=<path>]"
metadata:
  group: ship
---

# Create Pull Request

Create a PR/MR with a description that transfers your context to the reviewer. When you create a PR, you know everything about the change — the reviewer knows nothing. Your job is to bridge that gap.

Parse `$ARGUMENTS` for:
- Optional PR title (quoted string)
- `--context=path` — path to a context file with additional structured data (from player-coach or similar)
- `--no-comments` — skip inline review comments
- `--base=<branch>` — the branch this PR should target
- `--plan-file=<path>` — explicit plan path (see step 3 of Phase 2)

## Phase 1: Git Mechanics

### 1. Determine the target branch

```bash
ORIGINAL_BRANCH=<--base if given>
# else:
ORIGINAL_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null)
# else:
ORIGINAL_BRANCH=$(git branch --show-current)
```

Prefer `--base` when given, then the repo's default branch, and only fall back to the
current branch. That order matters because a caller may have already put you **on** the
feature branch — a loop that commits as it goes has been sitting on it for hours. Reading
the current branch in that situation would target the PR at itself.

### 2. Check for existing PR/MR

```bash
# GitHub
gh pr view --json url,number 2>/dev/null

# GitLab
glab mr view --output json 2>/dev/null
```

If a PR/MR already exists:
- Store its URL, number, and base/target branch
- The current branch IS the feature branch — set `ORIGINAL_BRANCH` to the PR's base branch (from `gh pr view --json baseRefName` / MR target branch), not from `git branch --show-current`
- Skip steps 3-7 (branch, commit, push, labels are already done)
- Proceed to Phase 2 to update the description and add comments

### 3. Detect platform

```bash
REMOTE_URL=$(git remote get-url origin)
```

- Contains `github.com` → GitHub (use `gh`)
- Contains `gitlab.com` or other GitLab instance → GitLab (use `glab`)

Verify the CLI tool is installed (`which gh` / `which glab`). If not installed, provide installation instructions and stop.

### 4. Create feature branch

**First check whether you are already on one.** If the current branch is not
`ORIGINAL_BRANCH` and has commits ahead of it:

```bash
git rev-parse --abbrev-ref HEAD
git log --oneline origin/$ORIGINAL_BRANCH..HEAD
```

then this branch already *is* the feature branch — a caller prepared it and committed to it.
**Skip the rest of this step and step 5 entirely** and go to step 6 to push it.

Cutting a new branch here would be quietly wrong in two ways: the new branch would be based
on the feature branch rather than trunk, and the "add a timestamp suffix if the branch
exists" rule below would hide the collision instead of surfacing it.

Otherwise, generate a branch name from the PR title (if provided) or from analysis of the changes:
- New feature → `feature/brief-description`
- Bug fix → `fix/issue-description`
- Docs → `docs/update-description`
- Refactor → `refactor/component-name`

Rules: kebab-case, max 50 chars, valid git branch name. Add timestamp suffix if branch exists.

```bash
git checkout -b [branch-name]
```

### 5. Handle uncommitted changes

```bash
git status --porcelain
```

If changes exist, stage and commit on the feature branch. Generate a descriptive commit message from the changes. All commits happen on the feature branch, never the original.

### 6. Push

```bash
git push -u origin [feature-branch]
```

### 7. Fetch and filter labels

Fetch available labels first — never assume labels exist:

**GitHub:**
```bash
AVAILABLE_LABELS=$(gh label list --json name --jq '.[].name' 2>/dev/null || echo "")
```

**GitLab:**
```bash
AVAILABLE_LABELS=$(glab label list 2>/dev/null | cut -f1 || echo "")
```

If fetching fails, proceed without labels.

**Simple matching** — propose labels from:
- Branch name prefix: `feature/*` → "enhancement", `fix/*` → "bug", `docs/*` → "documentation"
- Commit message prefix: `feat:` → "enhancement", `fix:` → "bug", `docs:` → "documentation"

Only apply labels that exist in `AVAILABLE_LABELS`. If no matches, create PR without labels.

## Phase 2: Context Gathering

Understand the change deeply enough to write a useful description. Two paths depending on invocation:

### Path A: Context file provided (`--context=path`)

Read the context file. It contains structured data from the caller (e.g., player-coach):
- Plan summary
- Turn history / implementation journey
- Friction log (sticky issues, player concerns)
- Below-threshold issues
- CI failure log

Also read the diff for code-level understanding:
```bash
git diff origin/$ORIGINAL_BRANCH...HEAD
git diff --stat origin/$ORIGINAL_BRANCH...HEAD
```

Three dots, not two, and against `origin/`. Two-dot `git diff` compares the two branch tips,
so anything that merged into trunk since you branched shows up in your PR description as
**deletions you didn't make**. Three dots diffs from the merge base, which is what the PR
itself will show. This produces a plausible-looking but wrong description otherwise, which
is the worst kind of wrong.

If the context file includes a `## Testing Plan Hints` section, use those hints (user-facing flows, known edge cases, exerciser results) as a starting point for the Testing Plan.

### Path B: Standalone invocation (no context file)

Gather context yourself:

1. **Read the diff:**
   ```bash
   git diff origin/$ORIGINAL_BRANCH...HEAD --stat
   git diff origin/$ORIGINAL_BRANCH...HEAD
   ```
   Three dots and `origin/` — see the note in Path A for why two-dot diffs misreport.
   For large diffs (20+ files), use `--stat` first and selectively read key files.

2. **Read the commit log:**
   ```bash
   git log origin/$ORIGINAL_BRANCH..HEAD --format='%s%n%n%b---'
   ```
   Two dots is correct here — for `git log` it already means "commits on this branch only".

3. **Check for a plan file:**
   If `--plan-file=<path>` was passed, read that. Otherwise look for one:
   ```bash
   ls .claude/plans/*.md 2>/dev/null
   ```
   If found, read it — it explains the "why" behind the change. A caller that runs many
   loops keeps its plans outside the repository, which is why the explicit path exists.

4. **Check for issue references:**
   Scan commit messages for `#NNN` patterns. Fetch context:
   - GitHub: `gh issue view NNN --json title,body`
   - GitLab: `glab issue view NNN`

5. **Check for engineer skill:**
   ```bash
   ls .claude/skills/*-engineer/SKILL.md 2>/dev/null
   ```
   If found, read for architecture context.

6. **Identify testable user flows:** From the plan file (if found) and the diff, identify what the feature does from the user's perspective — what inputs it accepts, what outputs it produces, and what can go wrong. This feeds the Testing Plan section.

## Phase 3: Compose Rich PR Description

The description is the reviewer's primary entry point. Write it for someone who has zero context on this work.

### PR Title

PR titles appear in changelogs and release notes. They must be user-facing, not technical.

Write for end users: describe the user impact, not the code change. "Speed up page loading times" not "feat: implement Redis caching layer."

Templates:
- Features: "Enable [capability]", "Add support for [action]"
- Bug fixes: "Fix [user-visible problem]", "Prevent [behavior]"
- Improvements: "Improve [aspect] of [feature]", "Speed up [action]"

Avoid: class names, function names, file names, technical patterns (middleware, service, controller), implementation details (cache, queue, worker).

### PR Body Template

**Core sections (always present):**

```markdown
## Summary

{2-4 sentences: what was built/changed and WHY. Include the problem being
solved or the need being addressed. Write for someone with zero context.}

## Architecture

{ASCII diagram of component relationships, data flow, or request paths
relevant to the change. Show how the pieces fit together.

Skip this section for trivial changes (< 3 files, no new components,
pure bug fixes, config changes).}

## What Changed

{Changes grouped by component/area, not by file. Each item explains
WHAT and WHY at the component level.}

- **Area/Component**: What was done and why
- **Another area**: What was done and why
- **Tests**: Summary of test coverage added

## Reviewer Guide

{Help the reviewer navigate the change efficiently.}

- **Start here**: {entry point file/function — where to begin reading}
- **Pay attention to**: {areas that are tricky, non-obvious, or critical}
- **Design decision**: {choices made and why, alternatives considered}
```

**Testing plan (always present):**

```markdown
## Testing Plan

{A manual QA checklist for the human reviewer. Write concrete steps for
someone who has never seen this feature. Generate from the plan, the diff,
friction points (which are natural edge cases), and implementation details.}

### Happy Path
- [ ] {concrete action — "Open /settings, click 'Add API Key'"}
- [ ] {verify expected result — "Key appears in the list, status shows 'Active'"}

### Edge Cases
- [ ] {edge case — "Submit with empty required fields, verify validation errors"}
- [ ] {edge case — "Enter special characters / very long input"}
- [ ] {edge case — "Perform action while offline or with slow connection"}

### Regression Checks
- [ ] {anything that might have broken — "Existing feature X still works as before"}
```

**Additional sections when context file is provided (e.g., from player-coach):**

```markdown
## Implementation Journey

{Turn history and narrative from the context file. Include the turn table
and a brief narrative if the run was rough.}

## Friction Log

{Only if friction occurred. Each item references specific files/lines
and explains what was hard, why, and what the human should check.
Omit entirely for clean runs.}

## Below-Threshold Issues

{Issues that passed the severity bar but the reviewer may want to address.
Omit if none.}
```

### Guidance for writing the description

- **Summary**: Synthesize, don't paste. If a plan exists, distill its goals into plain language.
- **Architecture**: Even a 3-line box-and-arrow diagram is worth including for non-trivial changes. It helps the reviewer build a mental model before reading code.
- **What Changed**: Group by logical area. "Added JWT auth middleware" is better than "modified src/middleware/auth.ts". Include WHY each area was changed.
- **Reviewer Guide**: This is what makes your PR stand out. Point the reviewer to the entry point so they don't have to guess where to start. Flag anything that's correct but surprising.
- **Testing Plan**: Write steps a human can follow without reading the code. Include concrete UI actions ("click X", "fill in Y", "submit"), expected results ("Z appears", "error message shows"), and edge cases. Friction points from the context file are natural edge cases to include. Keep it focused — 5-10 items total, not an exhaustive test matrix.

## Phase 4: Create the PR/MR

Create the PR/MR with the rich description from Phase 3.

**GitHub:**
```bash
gh pr create \
  --title "$TITLE" \
  --body "$(cat <<'PRBODY'
{composed body}
PRBODY
)" \
  --base "$ORIGINAL_BRANCH" \
  $LABEL_FLAGS
```

**GitLab:**
```bash
glab mr create \
  --title "$TITLE" \
  --description "$(cat <<'MRBODY'
{composed body}
MRBODY
)" \
  --target-branch "$ORIGINAL_BRANCH" \
  $LABEL_FLAGS
```

If a PR/MR already existed (detected in Phase 1 step 2), update the description instead:

**GitHub:**
```bash
gh pr edit "$PR_NUMBER" --body "$(cat <<'PRBODY'
{composed body}
PRBODY
)"
```

**GitLab:**
```bash
glab mr update "$MR_IID" --description "$(cat <<'MRBODY'
{composed body}
MRBODY
)"
```

Extract and store the PR/MR URL and number for Phase 5.

## Phase 5: Inline Review Comments

Skip this phase if `--no-comments` was passed or if there are no attention-worthy areas.

Inline comments are like a self-review: they guide the reviewer to specific lines that need attention. A human author would leave these to explain non-obvious decisions, flag workarounds, or highlight critical sections. Do the same.

### Identify comment-worthy lines

**When context file is provided:**
- Friction log items that reference specific files/lines → inline comments on those locations
- Sticky issues → comment explaining what was hard and the current approach
- Player concerns → comment flagging uncertainty
- If a friction item references only a file (no line number), find the most relevant changed line in that file from the diff and comment there. If it's too vague to map to a specific location, include it in the PR body's Friction Log section instead of as an inline comment.

**When standalone (no context file):**
Scan the diff for:
- Complex conditional logic or non-obvious control flow
- TODO, FIXME, HACK comments in new code
- Security-sensitive operations (auth, crypto, input validation, data access)
- Non-obvious algorithms or business logic that needs explanation
- Large new functions (50+ lines)
- Workarounds or compatibility shims with comments explaining why

### Post comments

**Guardrails:**
- Maximum 8 inline comments per PR/MR
- Each comment should be 1-3 sentences — concise and actionable
- Only comment on NEW code (added lines), never on deleted or unchanged lines
- If no attention-worthy areas found, skip entirely
- If API calls fail, warn but don't fail — the PR body already has the context

**GitHub — via PR reviews API:**

Write comments to a temp JSON file, then post as a review:

```bash
PR_COMMENTS_JSON=$(mktemp -t pr-review-comments.XXXXXX.json)
cat > "$PR_COMMENTS_JSON" << 'EOF'
{
  "body": "Self-review: areas flagged for reviewer attention",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/auth/middleware.ts",
      "line": 45,
      "side": "RIGHT",
      "body": "This retry logic works but is a workaround for the race condition in token refresh. Consider a proper mutex if this path gets higher traffic."
    }
  ]
}
EOF

gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --method POST \
  --input "$PR_COMMENTS_JSON"
```

The `line` parameter is the line number in the new version of the file. `side: "RIGHT"` means the new file (not the old). Use `gh api repos/{owner}/{repo}/pulls/{pr_number} --jq '.head.sha'` if you need the head SHA.

**GitLab — via MR discussions API:**

GitLab requires diff position SHAs for inline notes. Fetch them first:

```bash
# Get the MR's diff refs. Note: glab api has no --jq flag (unlike gh api) — pipe to jq instead.
DIFF_REFS=$(glab api projects/{project_id}/merge_requests/{mr_iid} | jq '.diff_refs')
BASE_SHA=$(echo "$DIFF_REFS" | jq -r '.base_sha')
START_SHA=$(echo "$DIFF_REFS" | jq -r '.start_sha')
HEAD_SHA=$(echo "$DIFF_REFS" | jq -r '.head_sha')
```

Then post each comment as a discussion. **You must send a JSON body with an explicit `Content-Type: application/json` header.** The form-encoded `-f "position[base_sha]=..."` style gets accepted by GitLab (HTTP 201) but silently drops the nested `position` object — your note lands as a top-level MR comment instead of an inline `DiffNote`. Write the payload to a temp JSON file and post via `--input`:

```bash
MR_NOTE_JSON=$(mktemp -t mr-note.XXXXXX.json)
cat > "$MR_NOTE_JSON" <<EOF
{
  "body": "This retry logic works but is a workaround...",
  "position": {
    "base_sha": "$BASE_SHA",
    "start_sha": "$START_SHA",
    "head_sha": "$HEAD_SHA",
    "position_type": "text",
    "new_path": "src/auth/middleware.ts",
    "new_line": 45
  }
}
EOF

glab api projects/{project_id}/merge_requests/{mr_iid}/discussions \
  --method POST \
  --header "Content-Type: application/json" \
  --input "$MR_NOTE_JSON"
```

If the comment body is composed from a multi-line string or contains quotes/newlines, build the JSON with `jq` rather than string interpolation to get the escaping right:

```bash
jq -n --arg body "$COMMENT_BODY" --arg path "$FILE_PATH" --argjson line "$LINE_NUM" \
  --arg base "$BASE_SHA" --arg start "$START_SHA" --arg head "$HEAD_SHA" \
  '{body: $body, position: {base_sha: $base, start_sha: $start, head_sha: $head, position_type: "text", new_path: $path, new_line: $line}}' \
  > "$MR_NOTE_JSON"
```

**Verify the note posted as a true inline DiffNote:**

```bash
glab api projects/{project_id}/merge_requests/{mr_iid}/discussions \
  | jq '.[-1].notes[0] | {type, position}'
```

Expected: `type` is `"DiffNote"` and `position` is a non-null object. If you see `"DiscussionNote"` with `position: null`, the position object was stripped — almost always because `Content-Type: application/json` was missing and the request was form-encoded. (HTTP 415 `"The provided content-type '' is not supported."` is the same problem surfacing as an error rather than a silent strip.)

**To delete a wrongly-posted note** (e.g., it landed as a top-level comment instead of inline) — note that GitLab does not let you delete at the discussion level, only at the underlying note:

```bash
glab api projects/{project_id}/merge_requests/{mr_iid}/notes/{note_id} --method DELETE
```

The `note_id` comes from the discussion's `.notes[0].id` field, not the discussion's own `id`.

For the project ID and MR IID, extract from the MR created in Phase 4:
```bash
MR_JSON=$(glab mr view --output json)
PROJECT_ID=$(echo "$MR_JSON" | jq -r '.project_id')
MR_IID=$(echo "$MR_JSON" | jq -r '.iid')
```

Post each comment individually (GitLab doesn't support batched review comments like GitHub).

## Phase 6: Output

```markdown
## PR/MR Created

**URL**: {url}
**Branch**: {feature-branch} → {original-branch}
**Platform**: {GitHub/GitLab}
**Labels**: {applied labels, or "none"}
**Description**: Rich context with {list of sections included}
**Inline comments**: {N} reviewer attention flags posted {or "skipped"}
```

## Error Handling

- **No git repo**: Check for `.git` before proceeding
- **No remote**: Ensure `origin` is configured
- **CLI not installed**: Provide installation instructions (GitHub: `brew install gh` / `sudo apt install gh` + `gh auth login`; GitLab: `brew install glab` / download from releases + `glab auth login`)
- **Auth issues**: Guide user to authenticate
- **PR already exists**: Update description instead of creating duplicate
- **Push failures**: Report and stop — don't retry
- **Label fetch fails**: Proceed without labels
- **Inline comment API fails**: Warn but don't fail — PR body has the context
