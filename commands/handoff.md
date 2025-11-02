---
description: Document current plan and progress into handoff file
argument-hint: [optional: custom filename]
allowed-tools: Read, Write, Bash, Grep, Glob, TodoWrite, AskUserQuestion
---

# /handoff - Work State Documentation

## Goal

Auto-generate a comprehensive handoff document that captures current work state, progress, and context. This supports the "Document & Clear" workflow for complex tasks - create a handoff document, `/clear` the session, then later resume by reading the handoff.

The document is saved to `/tmp` for easy copy/paste to wherever you need it (notes app, issue tracker, email, etc.).

## Input

- `$ARGUMENTS` (optional): Custom filename without extension
  - Default: `handoff-{timestamp}.md`
  - Example: `/handoff` → `/tmp/handoff-2024-01-15-1430.md`
  - Example: `/handoff auth-feature` → `/tmp/auth-feature.md`

## Process

### 1. Verify Git Repository

Check that we're in a git repository (handoff documents git state):

```bash
git rev-parse --git-dir
```

If this fails, create a minimal handoff without git context and warn the user.

### 2. Gather Git Context

Collect comprehensive git information:

```bash
# Current branch
CURRENT_BRANCH=$(git branch --show-current)

# Base branch (for comparison)
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$BASE_BRANCH" ]; then
  if git show-ref --verify --quiet refs/heads/main; then
    BASE_BRANCH="main"
  elif git show-ref --verify --quiet refs/heads/master; then
    BASE_BRANCH="master"
  else
    BASE_BRANCH="HEAD"
  fi
fi

# Commit history on current branch
git log --oneline $BASE_BRANCH..HEAD 2>/dev/null || git log --oneline -5

# Commits ahead count
COMMITS_AHEAD=$(git rev-list --count $BASE_BRANCH..HEAD 2>/dev/null || echo "unknown")

# Changed files with status
git diff --name-status $BASE_BRANCH...HEAD 2>/dev/null

# Uncommitted changes
git status --porcelain

# Recent commits with full messages
git log -5 --format="%h - %s%n%b" --no-merges

# Current git user
GIT_USER=$(git config user.name)
GIT_EMAIL=$(git config user.email)
```

### 3. Check for Existing TODO List

If TodoWrite has been used in the session, the current TODO state should be included:

- Check if there's an active TODO list
- Categorize tasks by status (completed, in_progress, pending)
- Include task descriptions in handoff

### 4. Gather File Context

For changed files, provide context:

```bash
# Count changes by status
git diff --name-status $BASE_BRANCH...HEAD | awk '{print $1}' | sort | uniq -c

# Group files by directory
git diff --name-only $BASE_BRANCH...HEAD | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn

# Diff stats for magnitude of changes
git diff --stat $BASE_BRANCH...HEAD
```

### 5. Optionally Gather User Context

Use AskUserQuestion **only if** there's significant work in progress (more than 3 commits OR uncommitted changes OR active TODOs).

Ask strategically useful questions:

```markdown
Question 1: "What's the current blocker or challenge (if any)?"
Options:
- "No blockers - work is progressing smoothly"
- "Waiting on code review or feedback"
- "Technical issue - something not working as expected"
- "Unclear requirements or design decision needed"

Question 2: "What's the most important context to remember?"
Options:
- "Implementation approach or architecture decisions"
- "Key files or functions to focus on"
- "Dependencies or integration points to be aware of"
- "No specific context - handoff document captures it"
```

Only ask if it adds value. For simple tasks (1-2 commits, clear scope), skip questions and generate automatically.

### 6. Generate Handoff Document

Create comprehensive markdown document with this structure:

```markdown
# Handoff: {Work Description from Commits or Branch Name}

**Generated**: {ISO timestamp}
**Branch**: {CURRENT_BRANCH}
**Created By**: {GIT_USER} <{GIT_EMAIL}>

---

## Quick Summary

{One-paragraph summary of what's being worked on, inferred from:
- Branch name
- Recent commit messages
- Changed files
}

## Current State

### Branch Information
- **Current Branch**: {CURRENT_BRANCH}
- **Base Branch**: {BASE_BRANCH}
- **Commits Ahead**: {COMMITS_AHEAD}
- **Uncommitted Changes**: {Yes/No} ({count} files)

### Repository Status
```
{Output from git status}
```

## Work Progress

{If TODO list exists:}

### ✅ Completed Tasks
- {List completed tasks from TODO}

### 🔄 In Progress
- {List in-progress tasks from TODO}

### ⏭️ Pending Tasks
- {List pending tasks from TODO}

{If no TODO list:}

Based on commit history, work appears to be focused on:
{Infer from commit messages what's been done}

## Changes Overview

### Commit History
```
{git log output showing commits on branch}
```

### Files Changed

**Summary**: {X} files ({A} added, {M} modified, {D} deleted)

{Group by directory:}

**{Directory}** ({count} files)
- {file1} (Status)
- {file2} (Status)

### Change Statistics
```
{git diff --stat output}
```

## Technical Context

{Analyze changes to provide context:}

### Components Modified
- {List major components/modules affected}

### Key Files to Review
{Highlight important files based on:
- Largest changes (diff stats)
- Core functionality (e.g., main.py, app.js)
- New files (might be important)
}

### Dependencies or Integration Points
{Check for changes to:
- package.json, requirements.txt, go.mod, Cargo.toml
- Config files
- API contracts
- Database migrations
}

## Known Issues or Blockers

{If user provided blocker info via AskUserQuestion, include it}
{Otherwise, check for TODO/FIXME/HACK comments in recent changes}

{If found, list them; if not:}
No known blockers documented.

## Key Decisions or Context

{If user provided context via AskUserQuestion, include it}
{Otherwise, extract from commit messages or skip}

## Resumption Guide

### To Resume This Work:

1. **Checkout the branch**:
   ```bash
   git checkout {CURRENT_BRANCH}
   ```

2. **Review current state**:
   ```bash
   git status
   git log {BASE_BRANCH}..HEAD
   ```

3. **Understand changes**:
   ```bash
   /catchup  # Use catchup command to get oriented
   ```

4. {If uncommitted changes exist:}
   **Review uncommitted work**:
   ```bash
   git diff  # See what's changed but not committed
   ```

5. **Continue implementation**:
   {If TODO list exists:}
   - Next task: {First pending task from TODO}
   {Otherwise:}
   - Review commit messages for next steps
   - Check for TODO comments in code

### Environment Setup

{Check for and include if present:}
- **Dependencies**: {Note if package.json/requirements.txt/etc changed}
- **Config Changes**: {Note if config files modified}
- **Build/Test**: {Suggest running tests if relevant}

## Related Resources

{Scan for and link to:}
- Design docs in docs/design/
- Related issues (check commit messages for #123 patterns)
- Pull requests (if branch pushed to remote)
- Related tasks files (in docs/tasks/)
}

## Next Actions

{Suggest concrete next steps based on state:}

**Immediate** (next 1-2 tasks):
1. {Infer from pending TODOs or commit history}

**Later** (follow-up work):
1. {Infer from branch scope or commit messages}

---

**How to Use This Handoff**:
- Copy this document to your notes/project management tool
- When resuming, read this document then run `/catchup` to verify current state
- Update this document if you discover new context while working
```

### 7. Save Handoff Document

Determine filename:

```bash
if [ -z "$ARGUMENTS" ]; then
  TIMESTAMP=$(date +%Y-%m-%d-%H%M)
  FILENAME="/tmp/handoff-$TIMESTAMP.md"
else
  # Sanitize filename (remove spaces, special chars)
  CLEAN_NAME=$(echo "$ARGUMENTS" | tr ' ' '-' | tr -cd 'a-zA-Z0-9-_')
  FILENAME="/tmp/$CLEAN_NAME.md"
fi
```

Write the handoff document to the file using the Write tool.

### 8. Inform User

Output:
```
✅ Handoff document created: {FILENAME}

The document includes:
- Branch state and commit history ({X} commits)
- Changed files ({Y} files)
- {If TODOs exist: Task progress (X completed, Y pending)}
- Resumption instructions

📋 Copy the file content to wherever you need it.
📁 File location: {FILENAME}

💡 To resume this work later:
   1. Read the handoff document
   2. Run /catchup to verify current state
   3. Continue from where you left off
```

## Error Handling

### Not in Git Repository
```
⚠️  Warning: Not in a git repository.

Creating minimal handoff without git context...
```

Proceed with a simpler handoff that documents:
- Current working directory
- Any TODO list if active
- User-provided context via AskUserQuestion

### No Changes Detected
```
ℹ️  No commits or changes detected on this branch.

Creating minimal handoff with current directory state...
```

Include:
- Current directory
- List of files in working directory (ls)
- User-provided context

### Detached HEAD or Complex State
```
⚠️  Warning: Detached HEAD state detected.
Current commit: {hash}

Including state snapshot in handoff...
```

### Write Failure
```
❌ Error: Could not write to {FILENAME}

Possible issues:
- /tmp directory not writable
- Disk full
- Permission issues

Try specifying a different location:
/handoff ~/my-handoff
```

## Output Guidelines

- **Be comprehensive**: Capture all relevant context
- **Be structured**: Easy to scan and find information
- **Be actionable**: Include clear resumption steps
- **Be automated**: Minimize manual input unless valuable
- **Be portable**: Markdown format, copy/paste friendly

## Usage Examples

```bash
# Basic usage - auto-generated filename
/handoff

# Custom filename
/handoff auth-refactor

# After significant work, before taking a break
/handoff user-api-work

# Before handing off to teammate
/handoff feature-x-for-alice

# After /handoff, typical workflow:
# 1. Copy content from /tmp/handoff-*.md to your notes
# 2. Run /clear to reset session
# 3. Later: Read your notes, run /catchup, resume work
```

## Integration with Other Commands

This command works well with:
- `/clear` - After `/handoff`, clear the session knowing state is documented
- `/catchup` - When resuming, use `/catchup` to verify handoff is accurate
- `/create-pr` - Before creating PR, `/handoff` documents what's being submitted
- `/check-ci` - After `/handoff`, ensure tests pass before stepping away

## Advanced Features

### Smart TODO Integration

If TodoWrite has been active:
- Include all tasks with their status
- Highlight next pending task as "start here"
- Note if any tasks are blocked

### Commit Message Analysis

Parse commit messages for:
- Issue numbers (#123) → link to issues
- Breaking changes (BREAKING:, breaking change)
- Work in progress (WIP, TODO, FIXME in messages)

### File Importance Heuristic

Prioritize in "Key Files" section:
- Files with most lines changed (diff stats)
- Files matching patterns: main.*, index.*, app.*, *_test.*
- New files (might be core functionality)
- Config files (changes might affect setup)

### Context Preservation

Preserve ephemeral context:
- Environment variables set in session
- Build/test commands run recently
- Debugging steps taken
- Decisions made in chat

## Final Instructions

1. **Automation First**: Only ask user questions if truly valuable
2. **Infer Intent**: Use commit messages and file changes to understand work
3. **Be Complete**: Better to include extra context than miss critical info
4. **Standard Format**: Consistent structure makes handoffs easy to read
5. **Actionable**: Always include clear "next steps" and "resumption guide"
6. **Portable**: Save to /tmp, user decides where to preserve it
7. **Fast**: Generate in under 10 seconds for typical branches

The goal is making it effortless to pause complex work and resume later with full context intact.
