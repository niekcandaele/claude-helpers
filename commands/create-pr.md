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

## Label Assignment

Automatically query available repository labels and intelligently assign them to the pull request:

### 1. Label Discovery

**GitHub:**
```bash
# Get repository owner and name from remote URL
REPO_INFO=$(gh repo view --json owner,name)
OWNER=$(echo $REPO_INFO | jq -r .owner.login)
REPO=$(echo $REPO_INFO | jq -r .name)

# Fetch all available labels
gh api repos/$OWNER/$REPO/labels --jq '.[].name' > /tmp/available_labels.txt
```

**GitLab:**
```bash
# Get project ID from remote URL
PROJECT_ID=$(glab api projects --owned=true --jq '.[] | select(.ssh_url_to_repo == "'$(git remote get-url origin)'") | .id')

# Fetch all available labels  
glab api projects/$PROJECT_ID/labels --jq '.[].name' > /tmp/available_labels.txt
```

### 2. Intelligent Label Selection

Analyze changes and assign relevant labels based on patterns:

**Branch Pattern Analysis:**
- `feature/*` or `feat/*` → "enhancement", "feature"
- `fix/*` or `bugfix/*` → "bug", "bugfix"
- `docs/*` or `documentation/*` → "documentation"
- `refactor/*` → "refactoring"
- `test/*` or `testing/*` → "testing"
- `chore/*` → "maintenance", "chore"
- `hotfix/*` → "hotfix", "critical"

**Commit Message Analysis:**
- `feat:` or `feature:` → "enhancement", "feature"
- `fix:` → "bug", "bugfix"
- `docs:` → "documentation"
- `refactor:` → "refactoring"
- `test:` → "testing"
- `chore:` → "maintenance", "chore"
- `perf:` → "performance"
- `style:` → "style"

**File Change Analysis:**
```bash
# Get list of changed files
CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --cached --name-only)

# Pattern matching for file types
if echo "$CHANGED_FILES" | grep -q "\.md$\|README\|docs/"; then
    LABELS="$LABELS documentation"
fi

if echo "$CHANGED_FILES" | grep -q "test/\|\.test\.\|\.spec\.\|__tests__/"; then
    LABELS="$LABELS testing"
fi

if echo "$CHANGED_FILES" | grep -q "package\.json\|requirements\.txt\|Gemfile\|pom\.xml"; then
    LABELS="$LABELS dependencies"
fi

if echo "$CHANGED_FILES" | grep -q "\.css$\|\.scss$\|\.sass$\|\.less$"; then
    LABELS="$LABELS frontend styling"
fi

if echo "$CHANGED_FILES" | grep -q "\.js$\|\.jsx$\|\.ts$\|\.tsx$\|\.vue$\|\.svelte$"; then
    LABELS="$LABELS frontend"
fi

if echo "$CHANGED_FILES" | grep -q "\.py$\|\.java$\|\.rb$\|\.php$\|\.go$\|\.rs$"; then
    LABELS="$LABELS backend"
fi

if echo "$CHANGED_FILES" | grep -q "\.sql$\|migrations/\|schema/"; then
    LABELS="$LABELS database"
fi

if echo "$CHANGED_FILES" | grep -q "Dockerfile\|docker-compose\|\.yml$\|\.yaml$"; then
    LABELS="$LABELS infrastructure"
fi
```

### 3. Label Filtering and Assignment

Filter proposed labels against available repository labels:
```bash
# Filter labels to only include ones that exist in the repository
FINAL_LABELS=""
for label in $LABELS; do
    if grep -q "^$label$" /tmp/available_labels.txt; then
        FINAL_LABELS="$FINAL_LABELS --label \"$label\""
    fi
done
```

### 4. Error Handling for Label Assignment

Gracefully handle label-related failures without blocking PR creation:

```bash
# Attempt to fetch labels with error handling
fetch_labels() {
    local platform=$1
    
    case $platform in
        "github")
            if ! gh api repos/$(gh repo view --json owner,name --jq '.owner.login + "/" + .name')/labels --jq '.[].name' > /tmp/available_labels.txt 2>/dev/null; then
                echo "Warning: Could not fetch repository labels. Proceeding without automatic labeling." >&2
                return 1
            fi
            ;;
        "gitlab")
            PROJECT_ID=$(glab api projects --owned=true --jq '.[] | select(.ssh_url_to_repo == "'$(git remote get-url origin)'") | .id' 2>/dev/null)
            if [[ -z "$PROJECT_ID" ]] || ! glab api projects/$PROJECT_ID/labels --jq '.[].name' > /tmp/available_labels.txt 2>/dev/null; then
                echo "Warning: Could not fetch repository labels. Proceeding without automatic labeling." >&2
                return 1
            fi
            ;;
    esac
    return 0
}

# Use labels only if successfully fetched
if fetch_labels "$PLATFORM"; then
    # Run label assignment logic
    assign_labels
else
    # Skip labeling and continue with PR creation
    FINAL_LABELS=""
fi
```

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
     --base [original-branch] \
     $FINAL_LABELS
   ```
   - Note: `--base` is set to the branch you started from, not the default branch
   - `$FINAL_LABELS` contains the filtered `--label` flags for applicable repository labels

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
     --target-branch [original-branch] \
     $FINAL_LABELS
   ```
   - Note: `--target-branch` is set to the branch you started from
   - `$FINAL_LABELS` contains the filtered `--label` flags for applicable repository labels

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
  - Labels: enhancement, backend, security
  
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