---
description: Rebase current branch onto target branch with conflict resolution
argument-hint: [optional: target branch name, defaults to main/master]
allowed-tools: Read, Bash, Grep, Glob, AskUserQuestion
---

# Rebase Branch

## Goal

Rebase the current branch onto a target branch, guide through any conflicts that arise, and optionally force-push the rebased branch. This command helps keep feature branches up-to-date with the main branch while maintaining a clean commit history.

**Note:** Interactive rebase (`git rebase -i`) is not supported as it requires terminal interaction. This command performs a standard rebase.

## Input

- `$ARGUMENTS` (optional): Target branch name to rebase onto (defaults to auto-detected main branch: main, master, or develop)

## Process

1. **Pre-flight Checks:** Verify working directory is clean and identify branches
2. **Detect Target Branch:** Auto-detect main branch if not specified
3. **Fetch Latest:** Fetch latest changes from remote
4. **Execute Rebase:** Run git rebase onto target branch
5. **Handle Conflicts:** Guide user through resolution if conflicts occur
6. **Force Push:** Offer to push rebased branch with safety checks

## Pre-flight Checks

Before starting the rebase:

1. **Check for uncommitted changes:**
   - Run `git status --porcelain`
   - If output is non-empty, abort and ask user to commit or stash changes first

2. **Identify current branch:**
   - Run `git branch --show-current`
   - Store for later use in push step

3. **Verify not on target branch:**
   - If current branch equals target branch, abort with helpful message

4. **Check for rebase already in progress:**
   - Check if `.git/rebase-merge` or `.git/rebase-apply` directories exist
   - If found, use AskUserQuestion: "A rebase is already in progress. What would you like to do?"
   - Options: "Continue the rebase", "Abort and start fresh", "Skip this commit"

## Target Branch Detection

If no target branch is specified in `$ARGUMENTS`:

1. Check for common main branch names (local OR remote):
   - `git show-ref --verify --quiet refs/heads/main || git show-ref --verify --quiet refs/remotes/origin/main` → use `main`
   - `git show-ref --verify --quiet refs/heads/master || git show-ref --verify --quiet refs/remotes/origin/master` → use `master`
   - `git show-ref --verify --quiet refs/heads/develop || git show-ref --verify --quiet refs/remotes/origin/develop` → use `develop`

2. If none found, ask user to specify target branch

## Fetch and Rebase

1. **Fetch latest changes:**
   ```bash
   git fetch origin
   ```

2. **Execute rebase:**
   ```bash
   git rebase origin/<target-branch>
   ```

3. Check exit code to determine if conflicts occurred

## Conflict Resolution

When conflicts occur, guide the user through resolution:

### 1. Identify Conflicted Files
```bash
git diff --name-only --diff-filter=U
```

### 2. For Each Conflicted File:
- Display the file path
- Read and show the conflict markers using the Read tool
- Explain what the conflict is with CORRECT terminology:
  - **IMPORTANT:** During rebase, git terminology is REVERSED from merge!
  - The "HEAD" / "Current Change" section shows the TARGET branch (e.g., main) - this is counterintuitive!
  - The "Incoming Change" section shows YOUR branch's changes
  - Explain this clearly: "The top section (HEAD) is from main, the bottom section is your changes"

### 3. Wait for User to Resolve:
- Use AskUserQuestion to wait for explicit confirmation
- Prompt: "Please resolve the conflicts in your editor, save the files, then confirm here."
- Options: "I've resolved the conflicts", "I need help understanding the conflict", "Abort the rebase"

### 4. After User Confirms Resolution:
- Verify the file no longer has conflict markers
- Stage the resolved file: `git add <file>`
- Ask if there are more conflicts to resolve

### 5. Continue Rebase:
```bash
git rebase --continue
```

### 6. Repeat if More Conflicts:
- If rebase stops again with conflicts, repeat the resolution process
- Keep track of progress and inform user

### 7. Abort Option:
- At any point, offer the user the option to abort:
  ```bash
  git rebase --abort
  ```
- This returns the branch to its pre-rebase state

## Force Push with Safety Checks

After successful rebase, offer to push:

### 0. Check for Protected Branches:
Before offering force push, verify current branch is not a protected branch:
```bash
# If current branch is main, master, or develop - DO NOT offer force push
```
- If on protected branch, display: "Force push skipped - you're on a protected branch (main/master/develop). Rebase complete but not pushed."
- Skip the entire force push flow and end the command

### 1. Check if Branch Exists on Remote:
```bash
git ls-remote --heads origin <current-branch>
```

### 2. Warn About Shared Branches:
- If other commits exist on remote that aren't in local, warn user
- Check with: `git log origin/<branch>..<branch> --oneline` and vice versa

### 3. Confirm with User:
Use AskUserQuestion to confirm:
- "Rebase complete. Push changes to origin/<branch>?"
- Options: "Yes, force push", "No, I'll push manually"

### 4. Execute Force Push:
Use `--force-with-lease` for safety (prevents overwriting others' work):
```bash
git push --force-with-lease origin <current-branch>
```

## Error Handling

- **Dirty working directory:** Ask user to commit or stash changes first
- **Target branch doesn't exist:** List available branches and ask user to specify
- **Rebase already in progress:** Offer to continue, abort, or skip
- **Push rejected:** Explain why and suggest solutions
- **No upstream set:** Offer to set upstream with push

## Command Execution Steps

1. Run `git status --porcelain` to check for uncommitted changes
2. Run `git branch --show-current` to get current branch name
3. Detect or validate target branch
4. Run `git fetch origin` to get latest
5. Run `git rebase origin/<target>` and check result
6. If conflicts:
   - List conflicted files
   - Read each file to show conflicts
   - Guide resolution
   - Stage resolved files
   - Continue rebase
   - Repeat until complete
7. Ask user about force push
8. If confirmed, run `git push --force-with-lease origin <branch>`

## Success Output

```
✅ Rebase Complete

📍 Branch: feature/my-feature
🎯 Rebased onto: origin/main
📊 Commits replayed: 5

🚀 Pushed to origin/feature/my-feature (force-with-lease)
```

## Example Usage

```
/rebase           # Rebase onto auto-detected main branch
/rebase main      # Explicitly rebase onto main
/rebase develop   # Rebase onto develop branch
```

## Final Instructions

1. Always check for clean working directory before starting
2. Never force push to main/master/develop branches
3. Use `--force-with-lease` instead of `--force` for safety
4. Guide users clearly through conflict resolution
5. Keep users informed of progress throughout the process
6. Offer abort option at any point during conflict resolution
