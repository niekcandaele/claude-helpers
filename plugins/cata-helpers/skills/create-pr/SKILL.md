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
argument-hint: "[PR title] [--context=path] [--no-comments]"
---

# Create Pull Request

Create a PR/MR with a description that transfers your context to the reviewer. When you create a PR, you know everything about the change — the reviewer knows nothing. Your job is to bridge that gap.

Parse `$ARGUMENTS` for:
- Optional PR title (quoted string)
- `--context=path` — path to a context file with additional structured data (from player-coach or similar)
- `--no-comments` — skip inline review comments

## Phase 1: Git Mechanics

### 1. Store original branch

```bash
ORIGINAL_BRANCH=$(git branch --show-current)
```

This becomes the PR target branch. All PRs go back to whatever branch you started from.

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

Generate a branch name from the PR title (if provided) or from analysis of the changes:
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
git diff $ORIGINAL_BRANCH..HEAD
git diff --stat $ORIGINAL_BRANCH..HEAD
```

### Path B: Standalone invocation (no context file)

Gather context yourself:

1. **Read the diff:**
   ```bash
   git diff $ORIGINAL_BRANCH..HEAD --stat
   git diff $ORIGINAL_BRANCH..HEAD
   ```
   For large diffs (20+ files), use `--stat` first and selectively read key files.

2. **Read the commit log:**
   ```bash
   git log $ORIGINAL_BRANCH..HEAD --format='%s%n%n%b---'
   ```

3. **Check for a plan file:**
   ```bash
   ls .claude/plans/*.md 2>/dev/null
   ```
   If found, read it — it explains the "why" behind the change.

4. **Check for issue references:**
   Scan commit messages for `#NNN` patterns. Fetch context:
   - GitHub: `gh issue view NNN --json title,body`
   - GitLab: `glab issue view NNN`

5. **Check for engineer skill:**
   ```bash
   ls .claude/skills/*-engineer/SKILL.md 2>/dev/null
   ```
   If found, read for architecture context.

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
cat > /tmp/pr-review-comments.json << 'EOF'
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
  --input /tmp/pr-review-comments.json
```

The `line` parameter is the line number in the new version of the file. `side: "RIGHT"` means the new file (not the old). Use `gh api repos/{owner}/{repo}/pulls/{pr_number} --jq '.head.sha'` if you need the head SHA.

**GitLab — via MR discussions API:**

GitLab requires diff position SHAs for inline notes. Fetch them first:

```bash
# Get the MR's diff refs
DIFF_REFS=$(glab api projects/{project_id}/merge_requests/{mr_iid} --jq '.diff_refs')
BASE_SHA=$(echo "$DIFF_REFS" | jq -r '.base_sha')
START_SHA=$(echo "$DIFF_REFS" | jq -r '.start_sha')
HEAD_SHA=$(echo "$DIFF_REFS" | jq -r '.head_sha')
```

Then post each comment as a discussion:

```bash
glab api projects/{project_id}/merge_requests/{mr_iid}/discussions \
  --method POST \
  -f "body=This retry logic works but is a workaround..." \
  -f "position[base_sha]=$BASE_SHA" \
  -f "position[start_sha]=$START_SHA" \
  -f "position[head_sha]=$HEAD_SHA" \
  -f "position[position_type]=text" \
  -f "position[new_path]=src/auth/middleware.ts" \
  -f "position[new_line]=45"
```

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
