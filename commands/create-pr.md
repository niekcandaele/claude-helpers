# Create Pull Request

## Goal

To streamline the pull request creation workflow by automatically creating a feature branch, handling uncommitted changes, pushing to remote, and creating a pull request with appropriate CLI tools. This command always creates a new feature branch from your current branch, commits any changes on that feature branch, and creates a PR back to your original branch.

## Input

Optional PR title: $ARGUMENTS (e.g., `"Add user authentication feature"`)

## Process

1. **Store Original Branch:** Save the current branch name as the PR target branch
2. **Create Feature Branch:** Always generate and switch to a new feature branch
3. **Handle Uncommitted Changes:** If changes exist, commit them on the new feature branch
4. **Push Feature Branch:** Push the feature branch to remote with upstream tracking
5. **Detect Git Platform:** Identify whether using GitHub, GitLab, or Bitbucket
6. **Create Pull Request:** Use appropriate CLI tool to create PR from feature branch to original branch
7. **Display PR URL:** Show the created PR URL for easy access

## Platform Detection

The command automatically detects the git platform by examining the remote URL:

1. **Remote URL Analysis:**
   - Run `git remote get-url origin` to get the remote URL
   - Parse URL to identify platform:
     - Contains `github.com` → GitHub (use `gh` CLI)
     - Contains `gitlab.com` or self-hosted GitLab → GitLab (use `glab` CLI)
     - Contains `bitbucket.org` → Bitbucket (use platform API)

2. **CLI Tool Verification:**
   - Check if required CLI tool is installed (`which gh`, `which glab`)
   - If not installed, provide installation instructions
   - For platforms without CLI tools, use web URL to create PR

## Branch Management

### Branch Flow

1. **Store Original Branch:**
   - Get current branch with `git branch --show-current`
   - Save as `ORIGINAL_BRANCH` for PR target
   - This ensures PR goes back to whatever branch you started from

2. **Feature Branch Creation (always):**
   - Generate branch name based on:
     - PR title if provided in $ARGUMENTS
     - Analysis of uncommitted changes
     - Recent commits on current branch
   - Branch naming patterns:
     - New feature → `feature/brief-description`
     - Bug fix → `fix/issue-description`
     - Documentation → `docs/update-description`
     - Refactoring → `refactor/component-name`
   - Create and switch: `git checkout -b [branch-name]`

3. **Branch Name Generation:**
   - Extract from PR title or changes
   - Convert to kebab-case
   - Limit to 50 characters
   - Ensure valid git branch name
   - Add timestamp suffix if branch already exists

## Commit and Push Integration

After creating the feature branch, handle any uncommitted changes:

1. **Check for Uncommitted Changes:**
   ```bash
   git status --porcelain
   ```

2. **If Changes Exist (commit on feature branch):**
   - Follow the same workflow as `/commit-and-push` command:
     - Run quality checks (linting, formatting, build)
     - Stage all changes
     - Generate descriptive commit message
     - Create commit with attribution
   - Important: All commits happen on the new feature branch, not the original branch

3. **Push Feature Branch:**
   ```bash
   git push -u origin [feature-branch]
   ```
   - Always set upstream tracking for the new branch
   - This enables easy PR creation and updates

## Pull Request Creation

### GitHub (using `gh` CLI)

1. **Check CLI Installation:**
   ```bash
   which gh || echo "GitHub CLI not installed"
   ```

2. **Create PR:**
   ```bash
   gh pr create \
     --title "[Title from commits or user input]" \
     --body "[Generated description]" \
     --base [original-branch]
   ```
   - Note: `--base` is set to the branch you started from, not the default branch

3. **PR Description Template:**
   ```markdown
   ## Summary
   [Brief description of changes based on commits]
   
   ## Changes
   - [List of key changes from git diff]
   
   ## Testing
   - [ ] Code has been tested locally
   - [ ] All tests pass
   - [ ] No console errors
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   ```

### GitLab (using `glab` CLI)

1. **Check CLI Installation:**
   ```bash
   which glab || echo "GitLab CLI not installed"
   ```

2. **Create MR (Merge Request):**
   ```bash
   glab mr create \
     --title "[Title]" \
     --description "[Description]" \
     --target-branch [original-branch]
   ```
   - Note: `--target-branch` is set to the branch you started from

### Bitbucket and Others

For platforms without CLI tools:
1. Generate the web URL for creating a PR
2. Open in default browser (if available)
3. Provide manual instructions

## Error Handling

- **No Git Repository:** Check for `.git` directory before proceeding
- **No Remote:** Ensure remote origin is configured
- **CLI Not Installed:** Provide platform-specific installation instructions
- **Authentication Issues:** Guide user to authenticate with platform CLI
- **Uncommitted Changes:** Run commit-and-push workflow first
- **PR Already Exists:** Display existing PR URL instead of creating duplicate
- **Push Failures:** Handle upstream issues and conflicts

## Success Output

Display comprehensive information about the created PR:

```
🚀 Pull Request Created Successfully!

📋 PR Details:
  - Title: Add user authentication feature
  - Source: feature/user-auth → develop
  - Original Branch: develop
  - Platform: GitHub
  
🔗 PR URL: https://github.com/user/repo/pull/123

📝 Next Steps:
  1. Review the PR in your browser
  2. Add reviewers if needed
  3. Wait for CI/CD checks to pass
  4. Merge when approved
```

## Command Options

While the basic usage is `/create-pr`, the command supports:

- **Custom Title:** `/create-pr "Custom PR Title"`
- **Auto-detection:** `/create-pr` (generates title from commits)

## Final Instructions

1. Always create a new feature branch - never commit directly to the original branch
2. Store the original branch name to use as the PR target
3. Commit any uncommitted changes on the feature branch, not the original
4. Run all quality checks before pushing (via commit-and-push integration)
5. Generate meaningful PR titles and descriptions
6. Include proper attribution in commits
7. Handle platform differences gracefully
8. Provide clear error messages and next steps
9. Never create duplicate PRs - check if one already exists
10. Set up tracking between local and remote branches
11. Make it clear which branch the PR targets (show "feature → original" flow)

## Platform-Specific Installation

If CLI tools are not installed, provide these instructions:

### GitHub CLI (gh)
```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# After installation
gh auth login
```

### GitLab CLI (glab)
```bash
# macOS
brew install glab

# Linux
# Download from https://gitlab.com/gitlab-org/cli/-/releases

# After installation
glab auth login
```