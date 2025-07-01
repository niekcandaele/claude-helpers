# Create Pull Request

## Goal

To streamline the pull request creation workflow by automatically handling branch management, committing changes, pushing to remote, and creating a pull request with appropriate CLI tools. This command ensures you're on a feature branch, your changes are committed and pushed, and creates a PR against the default branch.

## Input

Optional PR title: $ARGUMENTS (e.g., `"Add user authentication feature"`)

## Process

1. **Check Current Branch:** Determine if on main/master branch or feature branch
2. **Create Feature Branch (if needed):** Generate and switch to appropriately named branch
3. **Run Commit and Push:** Execute the commit-and-push workflow for any uncommitted changes
4. **Detect Git Platform:** Identify whether using GitHub, GitLab, or Bitbucket
5. **Create Pull Request:** Use appropriate CLI tool to create PR against default branch
6. **Display PR URL:** Show the created PR URL for easy access

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

### Branch Detection and Creation

1. **Current Branch Check:**
   - Get current branch with `git branch --show-current`
   - Identify if on default branch (main, master, develop)

2. **Feature Branch Creation (if on default branch):**
   - Analyze changes to generate branch name:
     - New feature → `feature/brief-description`
     - Bug fix → `fix/issue-description`
     - Documentation → `docs/update-description`
     - Refactoring → `refactor/component-name`
   - Create and switch: `git checkout -b [branch-name]`

3. **Branch Name Generation:**
   - Extract from staged/unstaged changes and recent commits
   - Convert to kebab-case
   - Limit to 50 characters
   - Ensure valid git branch name

## Commit and Push Integration

Before creating a PR, ensure all changes are committed and pushed:

1. **Check for Uncommitted Changes:**
   ```bash
   git status --porcelain
   ```

2. **If Changes Exist:**
   - Follow the same workflow as `/commit-and-push` command:
     - Run quality checks (linting, formatting, build)
     - Stage all changes
     - Generate descriptive commit message
     - Create commit with attribution
     - Push to remote

3. **Set Upstream (if needed):**
   ```bash
   git push -u origin [current-branch]
   ```

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
     --base [default-branch]
   ```

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
     --target-branch [default-branch]
   ```

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
  - Source: feature/user-auth → main
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

1. Always ensure you're on a feature branch before creating a PR
2. Run all quality checks before pushing (via commit-and-push integration)
3. Generate meaningful PR titles and descriptions
4. Include proper attribution in commits
5. Handle platform differences gracefully
6. Provide clear error messages and next steps
7. Never create duplicate PRs - check if one already exists
8. Set up tracking between local and remote branches

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