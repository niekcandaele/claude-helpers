---
description: Summarize all changes in current branch compared to base branch
argument-hint: [optional: base branch name]
allowed-tools: Read, Bash, Grep, Glob
---

# /catchup - Branch Changes Summary

## Goal

Quickly understand all changes in the current branch by providing a smart summary of commits, changed files, and key modifications. This is optimized for the "restart workflow" - after running `/clear`, use `/catchup` to get back up to speed without reading every file.

## Input

- `$ARGUMENTS` (optional): Base branch name to compare against
  - If not provided: auto-detects `main`, `master`, or `develop`
  - Examples: `/catchup`, `/catchup main`, `/catchup develop`

## Process

### 1. Verify Git Repository

Check that we're in a git repository:

```bash
git rev-parse --git-dir
```

If this fails, inform the user this command requires a git repository and exit.

### 2. Detect Current and Base Branch

```bash
# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# If no argument provided, auto-detect base branch
if [ -z "$ARGUMENTS" ]; then
  # Try to find default branch from remote
  DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')

  # Fallback: check if main or master exists
  if [ -z "$DEFAULT_BRANCH" ]; then
    if git show-ref --verify --quiet refs/heads/main; then
      DEFAULT_BRANCH="main"
    elif git show-ref --verify --quiet refs/heads/master; then
      DEFAULT_BRANCH="master"
    elif git show-ref --verify --quiet refs/heads/develop; then
      DEFAULT_BRANCH="develop"
    else
      echo "Could not auto-detect base branch. Please specify: /catchup <base-branch>"
      exit 1
    fi
  fi
  BASE_BRANCH="$DEFAULT_BRANCH"
else
  BASE_BRANCH="$ARGUMENTS"
fi
```

Verify base branch exists:
```bash
if ! git show-ref --verify --quiet refs/heads/$BASE_BRANCH; then
  echo "Error: Base branch '$BASE_BRANCH' does not exist"
  exit 1
fi
```

### 3. Check for Changes

Determine if there are any changes:

```bash
# Get commit count ahead
COMMITS_AHEAD=$(git rev-list --count $BASE_BRANCH..HEAD)

# Get changed files count
CHANGED_FILES=$(git diff --name-only $BASE_BRANCH...HEAD | wc -l)
```

If both are zero:
```
No changes detected between $CURRENT_BRANCH and $BASE_BRANCH.
Branches are in sync.
```
Exit successfully.

### 4. Gather Branch Information

Collect comprehensive branch context:

```bash
# Commit history (one-line format)
git log --oneline $BASE_BRANCH..HEAD

# Changed files with status
git diff --name-status $BASE_BRANCH...HEAD

# Diff stats (lines added/removed per file)
git diff --stat $BASE_BRANCH...HEAD

# Get uncommitted changes if any
git status --porcelain
```

### 5. Organize and Present Summary

Present information in this structured format:

```markdown
# Branch Catchup: {CURRENT_BRANCH}

## Overview
- **Current Branch**: {CURRENT_BRANCH}
- **Base Branch**: {BASE_BRANCH}
- **Commits Ahead**: {COMMITS_AHEAD}
- **Files Changed**: {total} ({added} added, {modified} modified, {deleted} deleted)
- **Uncommitted Changes**: {Yes/No} ({count} files)

## Commit History

{List commits with hash and message}

## Changed Files by Status

### Added Files
{List of added files}

### Modified Files
{List of modified files with diff stats}

### Deleted Files
{List of deleted files}

## Diff Statistics

{Output from git diff --stat showing lines changed per file}

## Uncommitted Changes
{If any exist, show git status output}

## File Organization

{Group files by directory/component for easier understanding}
Example:
- **Backend (src/)**: 5 files
- **Frontend (ui/)**: 3 files
- **Tests (tests/)**: 2 files
- **Docs (docs/)**: 1 file

## Key Insights

{Analyze commit messages and file changes to provide context}
- Main focus: {infer from commit messages}
- Components affected: {list major areas}
- Potential breaking changes: {flag if file names suggest}

## Next Steps

To see detailed changes in a specific file:
- Use Read tool: `Read path/to/file.py`
- Or git diff: `git diff {BASE_BRANCH}...HEAD -- path/to/file.py`

To resume work:
- Review uncommitted changes if any
- Check TODO list with TodoWrite
- Continue implementation
```

### 6. Smart File Reading (Optional)

Only read file contents if:
- There are very few changed files (≤3)
- User explicitly requests more detail
- File changes are unclear from diff stats

Otherwise, trust that the summary provides enough context. The goal is efficiency - reading 20+ files defeats the "quick catchup" purpose.

## Error Handling

### Not in Git Repository
```
Error: This command requires a git repository.
Current directory is not a git repository.
```

### Invalid Base Branch
```
Error: Base branch '{BASE_BRANCH}' does not exist.
Available branches: {list branches}

Usage: /catchup [base-branch-name]
```

### Detached HEAD State
```
Warning: You are in a detached HEAD state.
Current commit: {hash}
Cannot determine current branch name.

You may want to create a branch first:
git checkout -b my-branch-name
```

### No Commits Yet
```
This appears to be a new repository with no commits.
Cannot compare branches without commit history.
```

## Output Guidelines

- **Be concise**: Show summary first, details available on request
- **Be organized**: Group related files together
- **Be actionable**: Suggest next steps based on state
- **Be accurate**: Parse git output carefully, handle edge cases

## Usage Examples

```bash
# Basic usage - auto-detect base branch
/catchup

# Compare to specific branch
/catchup develop

# Compare to main explicitly
/catchup main

# After /clear to understand current state
/clear
/catchup  # "What have I been working on?"
```

## Integration with Other Commands

This command works well with:
- `/clear` - Clear state, then `/catchup` to understand what's there
- `/handoff` - After `/catchup`, use `/handoff` to document work
- `/create-pr` - After `/catchup`, review changes before creating PR
- `/check-ci` - After `/catchup`, ensure tests pass

## Final Instructions

1. Keep output under 1000 lines for readability
2. If diff is huge (>50 files), show summary stats only
3. Focus on commits and high-level changes, not line-by-line diffs
4. Make it easy to quickly understand branch state in under 30 seconds
5. Provide file paths in a format that can be easily copied for Read tool
