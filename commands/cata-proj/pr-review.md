---
description: Extract and categorize PR review feedback
argument-hint: [optional: PR number]
allowed-tools: Read, Write, Grep, Glob, Bash, WebFetch
---

# PR Review Feedback Processor

Extract and categorize feedback from GitHub PR reviews: **$ARGUMENTS**

This command automates the process of analyzing PR review comments, categorizing them by priority based on your reactions and direct input, and creating an actionable plan for addressing feedback.

## Process

### Step 1: Identify Target PR

Determine which PR to analyze:

1. **If PR number provided in $ARGUMENTS**: Use that PR number
2. **If no argument provided**: Auto-detect latest open PR
3. **Fetch PR information** using gh CLI

```bash
# List open PRs to find the target
gh pr list --state open --json number,title,headRefName,author

# If no argument, use the first (most recent) PR
# If argument provided, verify PR exists
```

---

## ⚠️ CRITICAL: Prevent JSON Truncation

**ALWAYS pipe GitHub API calls through jq immediately. NEVER fetch raw JSON without formatting.**

### Why This Matters

GitHub API responses can return massive JSON payloads (10,000+ characters). When you fetch raw JSON without piping through jq, the output gets truncated, hiding most comments.

### The Rule

✅ **CORRECT** - Parse immediately:
```bash
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" | jq -r '.[] | "formatted output"'
```

❌ **WRONG** - Fetch raw JSON (will truncate):
```bash
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments"  # Don't do this!
```

### When to Use Each Format

**For displaying to user** (use `| jq -r` for formatted text):
```bash
gh api "..." | jq -r '.[] | "@\(.user.login) \(.path):\n\(.body)\n"'
```

**For saving to files** (use `--jq` for structured JSON):
```bash
gh api "..." --jq '.[] | {id, path, body}' > file.json
```

**Key Principle**: Parse while fetching, not after. Format immediately to prevent truncation.

---

### Step 2: Fetch PR Comments and Reactions

Gather all review feedback using GitHub API. Use `--jq` to parse immediately and save structured data.

#### Setup: Get Repository Info

```bash
# Get repository owner and name
REPO_INFO=$(gh repo view --json owner,name --jq '.owner.login + "/" + .name')
PR_NUMBER=[from step 1]

echo "Fetching comments from $REPO_INFO PR #$PR_NUMBER..."
```

#### Fetch and Save Structured Data

These commands save structured JSON for later processing. Using `--jq` ensures immediate parsing:

```bash
# Fetch inline code review comments with reactions
# Note: Using --jq (not | jq) to save structured JSON to file
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" \
  --jq '.[] | {
    id: .id,
    path: .path,
    line: (.line // .original_line),  # Handle both line and original_line
    body: .body,
    author: .user.login,
    created_at: .created_at,
    reactions: .reactions
  }' > /tmp/pr_inline_comments.json

# Fetch PR-level comments (issue comments)
gh api "repos/$REPO_INFO/issues/$PR_NUMBER/comments" \
  --jq '.[] | {
    id: .id,
    body: .body,
    author: .user.login,
    created_at: .created_at,
    reactions: .reactions
  }' > /tmp/pr_comments.json

# Fetch PR details (title, description, author)
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER" \
  --jq '{
    title: .title,
    body: .body,
    author: .user.login,
    base: .base.ref,
    head: .head.ref,
    state: .state
  }' > /tmp/pr_details.json

echo "✓ Saved comments to /tmp files for processing"
```

### Step 2A: Quick Preview of Comments (Optional but Recommended)

Before processing, display a preview of all comments in human-readable format. This confirms all comments were fetched without truncation.

```bash
# Preview inline comments (formatted immediately to prevent truncation)
echo ""
echo "=== Inline Code Review Comments ==="
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" | \
  jq -r '.[] | "---\n@\(.user.login) \(.path)#\(.line // .original_line):\n\(.body[0:200])\(if (.body | length) > 200 then "..." else "" end)\n"'

# Preview PR-level comments
echo ""
echo "=== PR-Level Comments ==="
gh api "repos/$REPO_INFO/issues/$PR_NUMBER/comments" | \
  jq -r '.[] | "---\n@\(.user.login) (PR-level comment):\n\(.body[0:200])\(if (.body | length) > 200 then "..." else "" end)\n"'

echo ""
echo "✓ Preview complete. All comments fetched successfully."
```

**Why this step matters:**
- Immediately shows if all comments were retrieved (no truncation)
- Provides quick visibility into comment count and authors
- Uses `| jq -r` for human-readable output (not file storage)
- Truncates long comment bodies to 200 chars for preview

### Step 3: Identify Current User

Determine your GitHub username to filter your comments:

```bash
# Get authenticated user's username
CURRENT_USER=$(gh api user --jq '.login')
echo "Current user: $CURRENT_USER"
```

### Step 4: Categorize Comments by Priority

Analyze and categorize all comments:

#### Priority 1: Your Direct Comments
- Author matches `$CURRENT_USER`
- These are your explicit requests
- **Action**: Must implement

#### Priority 2: Bot Comments with Your Approval
- Author is a bot (e.g., `coderabbitai[bot]`, `dependabot[bot]`)
- Has `"+1"` reaction count > 0 (you gave 👍)
- **Action**: Implement these suggestions

#### Priority 3: Your Comments with Context
- Your comments that provide context or modifications
- Examples: "great idea, but do it differently", "not now, later", etc.
- Extract the intent and note for discussion
- **Action**: Follow your specific guidance

#### IGNORED: Bot Comments Without Your Interaction
- Author is a bot
- `reactions.total_count` is 0 OR no reactions from you specifically
- **Action**: Ignore completely - no discussion, no implementation

#### IGNORED: Bot Comments You Rejected
- Author is a bot
- Has `"-1"` reaction count > 0 (you gave 👎)
- **Action**: Explicitly ignore these

**CRITICAL PRINCIPLE**: If you didn't interact with a bot comment (no 👍, no 👎, no reply), it gets IGNORED. No interaction = No implementation. Period.

### Step 5: Generate Categorized Report

Create a comprehensive report of all feedback:

```markdown
# PR Review Feedback Analysis

**PR #[NUMBER]**: [PR Title]
**Branch**: [head] → [base]
**Author**: [author]

---

## 📋 Summary

- **Total Comments**: [count]
- **Your Direct Comments**: [count] ⚡ MUST IMPLEMENT
- **Approved Bot Suggestions**: [count] ⚡ MUST IMPLEMENT
- **Your Contextual Notes**: [count] 📝 FOLLOW YOUR GUIDANCE
- **Ignored (No Interaction)**: [count] ❌ IGNORE
- **Ignored (Rejected)**: [count] ❌ IGNORE

---

## ⚡ PRIORITY 1: Your Direct Comments

These are your explicit requests that must be implemented:

### Comment 1: [file:line or "PR-level"]
**Location**: `[path]:[line]` (or "General PR comment")
**Your comment**:
> [comment body]

**Action Required**: [Extract specific action]

---

### Comment 2: ...
[repeat for each direct comment]

---

## ⚡ PRIORITY 2: Bot Suggestions You Approved (👍)

These bot suggestions received your thumbs-up and should be implemented:

### Suggestion 1: [file:line]
**Location**: `[path]:[line]`
**Bot**: [bot name]
**Suggestion**:
> [comment body]

**Your reaction**: 👍 Approved

**Action Required**: [Extract specific action]

---

### Suggestion 2: ...
[repeat for each approved bot comment]

---

## 📝 PRIORITY 3: Your Contextual Notes

Comments where you provided additional context or modifications:

### Note 1: [file:line or "PR-level"]
**Location**: `[path]:[line]` (or "General PR comment")
**Your note**:
> [comment body]

**Interpretation**: [Extract intent - what needs to be done differently]

---

## ❌ IGNORED: Bot Suggestions (No Interaction)

**You did not interact with these comments (no reaction, no reply). They are IGNORED.**

Count: [number] bot comments ignored

_These suggestions were not approved and will not be implemented. If you want any of these implemented, go back to GitHub and react with 👍._

---

## ❌ IGNORED: Bot Suggestions You Rejected (👎)

These suggestions were explicitly rejected and should be ignored:

### Rejected 1: [file:line]
**Bot**: [bot name]
**Suggestion**: [brief summary]
**Your reaction**: 👎 Rejected

---

## 🎯 Implementation Plan

Based on the categorized feedback, here's the recommended action plan:

### Immediate Actions (Must Do)
1. [Action from Priority 1 comment 1]
2. [Action from Priority 1 comment 2]
3. [Action from Priority 2 suggestion 1]
4. [etc...]

### Contextual Changes (Your Specific Guidance)
1. [Action from Priority 3 note 1 - with your specific context]
2. [etc...]

### Explicitly Ignored
- [Count] bot comments without your interaction - IGNORED
- [Count] bot comments you rejected with 👎 - IGNORED

---

## Next Steps

Would you like me to:

1. **Create a task list** for the immediate actions (integrates with `/cata-proj:tasks`)?
2. **Execute the changes** directly using `/cata-proj:execute`?
3. **Discuss specific points** before proceeding?

Choose your preferred next step, or I can start implementing the Priority 1 and 2 items immediately.
```

### Step 6: Integration Options

After presenting the report, offer integration with existing workflows:

#### Option A: Create Task List
- Generate a `tasks.md` file in `.design/pr-[NUMBER]-feedback/tasks.md`
- Structure tasks by priority
- Can be executed with `/cata-proj:execute`

#### Option B: Direct Implementation
- Start implementing Priority 1 and 2 items immediately
- Create commits for each logical group of changes
- Update PR with new commits

#### Option C: Discussion First
- Review optional suggestions with user
- Clarify any contextual notes
- Then proceed with A or B

## Comment Parsing Guidelines

### Identifying Bots
Common bot patterns:
- Username ends with `[bot]` (e.g., `coderabbitai[bot]`, `dependabot[bot]`)
- Username contains: `bot`, `ai`, `automated`
- Known bots: `coderabbitai`, `dependabot`, `renovate`, `snyk-bot`

### Reaction Structure
GitHub API returns reactions as:
```json
{
  "reactions": {
    "total_count": 1,
    "+1": 1,      // thumbs up
    "-1": 0,      // thumbs down
    "laugh": 0,
    "confused": 0,
    "heart": 0,
    "hooray": 0,
    "rocket": 0,
    "eyes": 0
  }
}
```

### Extracting Actions
From comment bodies, identify:
- Imperative verbs: "Add", "Remove", "Fix", "Update", "Refactor"
- Specific code references: function names, file paths, line numbers
- Technical suggestions: architecture changes, pattern improvements
- Your modifications: "but do X instead", "later, not now", "different approach"

## Error Handling

### PR Not Found
```bash
if ! gh pr view $PR_NUMBER &>/dev/null; then
  echo "❌ PR #$PR_NUMBER not found"
  echo "Available PRs:"
  gh pr list --state open --json number,title
  exit 1
fi
```

### No Comments Found
```
ℹ️ No review comments found on this PR.

This PR has no inline code review comments or PR-level comments yet.
Would you like to:
1. Check the PR on GitHub to add comments first
2. Analyze the PR diff for potential improvements
```

### Authentication Issues
```bash
if ! gh auth status &>/dev/null; then
  echo "❌ GitHub CLI not authenticated"
  echo "Run: gh auth login"
  exit 1
fi
```

### JSON Truncation Detection

If you suspect output was truncated (missing comments, incomplete data):

**Symptoms:**
- Output ends abruptly with `...`
- Comment count seems too low
- Known comments are missing from preview

**Recovery Steps:**

```bash
# 1. Check if jq is being used (required!)
# If you see raw JSON output, you forgot to pipe through jq

# 2. Re-run with formatted output (prevents truncation)
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" | \
  jq -r '.[] | "---\n@\(.user.login) \(.path)#\(.line // .original_line):\n\(.body)\n"'

# 3. Count comments to verify completeness
COMMENT_COUNT=$(gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" | jq '. | length')
echo "Total comments: $COMMENT_COUNT"

# If count matches what you see in the preview, no truncation occurred
```

**Prevention:**
- Always use `| jq -r` for display output
- Always use `--jq` for saving to files
- Never fetch raw JSON without parsing
- Follow Step 2A to verify all comments were retrieved

## Usage Examples

### Analyze latest PR
```
/cata-proj:pr-review
```

### Analyze specific PR
```
/cata-proj:pr-review 123
```

### After analyzing, create tasks
```
User: "Create a task list for these changes"
Assistant: [Creates .design/pr-123-feedback/tasks.md and suggests /cata-proj:execute]
```

## Implementation Notes

- **Comment Ordering**: Present comments in order of priority, then by file path
- **Summarization**: For long bot comments, summarize but link to full text
- **Code Snippets**: Include relevant code snippets from comments when helpful
- **Batch Actions**: Group similar actions together (e.g., all imports, all type fixes)
- **File Context**: Show which files are affected most to prioritize work
- **Dependency Detection**: Identify if some changes depend on others

## Output Principles

1. **Clear Prioritization**: User should immediately see what must be implemented vs what's ignored
2. **Actionable Items**: Every item should have a clear "what to do"
3. **Context Preservation**: Keep your notes and reasoning visible
4. **No Assumptions**: If a comment is ambiguous, mark it for discussion
5. **Rejection Respect**: Never implement something you explicitly downvoted OR didn't interact with
6. **Default to Ignore**: No interaction = No implementation. Only explicit approvals get implemented.
7. **Efficiency**: Group related changes to minimize commits

## Advanced Features

### Detect Patterns
- Multiple comments on same file → High-priority file
- Multiple type errors → Type system issue
- Multiple style issues → Consider linting/formatting
- Security comments → Tag as critical priority

### Smart Grouping
Group comments by theme:
- "Type Safety Improvements"
- "Error Handling Enhancements"
- "Code Style Fixes"
- "Documentation Updates"
- "Performance Optimizations"

### Change Estimation
Provide rough estimates:
- **Quick wins** (< 15 min): Simple changes, imports, renames
- **Medium effort** (15-60 min): Logic changes, new functions
- **Significant** (> 1 hour): Architecture changes, refactoring

## Final Validation

Before completing, verify:
- ✓ All comments fetched (inline + PR-level)
- ✓ Your username correctly identified
- ✓ Reactions properly parsed
- ✓ No comments miscategorized
- ✓ All bots identified correctly
- ✓ Action items are specific and clear
- ✓ Report is well-formatted and readable

## Best Practices for GitHub API Calls

### The Golden Rule: Parse While Fetching

**Never fetch raw JSON. Always parse immediately using jq.**

When you fetch GitHub API data without piping through jq, you risk truncation that hides most of the data. This is the #1 cause of missing PR comments.

### Two Formats for Two Purposes

#### 1. For Display (Human-Readable)
Use `| jq -r` to format immediately:

```bash
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" | \
  jq -r '.[] | "@\(.user.login) \(.path):\n\(.body)\n"'
```

**Why `-r` flag:** Removes JSON quotes, produces clean text output

**When to use:** Previewing, logging, showing to user

#### 2. For Storage (Structured Data)
Use `--jq` to parse and save:

```bash
gh api "repos/$REPO_INFO/pulls/$PR_NUMBER/comments" \
  --jq '.[] | {id, path, body}' > /tmp/comments.json
```

**Why `--jq` flag:** Parses and filters before saving to file

**When to use:** Saving for later processing, building data structures

### Common Mistakes to Avoid

❌ **Wrong:** Fetch then parse
```bash
# This will truncate!
COMMENTS=$(gh api "repos/$REPO/pulls/$PR/comments")
echo "$COMMENTS" | jq '.[] | .body'  # Too late, already truncated
```

✅ **Correct:** Parse while fetching
```bash
# This works perfectly
gh api "repos/$REPO/pulls/$PR/comments" | jq -r '.[] | .body'
```

### Verification Checklist

Before processing any PR comments, verify:
- [ ] All API calls use `| jq` or `--jq`
- [ ] No raw JSON output visible to user
- [ ] Comment count in preview matches expected count
- [ ] Step 2A preview shows all expected comments
- [ ] No output ends with `...` (truncation indicator)

### Character Limits

GitHub API responses can exceed 10,000 characters. Without jq:
- **Raw JSON:** Truncates at ~10,000 chars → Missing comments
- **With jq:** Parses immediately → No truncation

### Quick Test

To verify you're doing it right:
```bash
# Count comments using jq (always reliable)
gh api "repos/$REPO/pulls/$PR/comments" | jq '. | length'

# If this number matches your preview, you're good!
```

## Important Notes

- This command is **read-only** by default (no code changes)
- It **analyzes and categorizes** feedback
- It **creates an execution plan** based on your priorities
- Integration with `/cata-proj:execute` is optional
- You can run this multiple times as reviews evolve
- Works with any GitHub repository that has `gh` CLI access
- Respects your judgment via reactions (👍 = do it, 👎 = skip it)

This command bridges the gap between PR review feedback and systematic implementation, ensuring you only work on what truly matters based on your explicit approvals and guidance.
