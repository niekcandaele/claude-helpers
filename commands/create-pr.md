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
6. **Fetch Repository Labels:** Query available labels from the repository BEFORE attempting to assign any
7. **Create Pull Request:** Use appropriate CLI tool to create PR with valid labels from feature branch to original branch
8. **Display PR URL:** Show the created PR URL for easy access

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

**IMPORTANT: You MUST fetch the repository's actual labels FIRST before attempting to assign any labels to the PR. Never assume labels exist - always verify!**

### 1. Label Discovery (REQUIRED FIRST STEP)

**GitHub (EXECUTE THIS FIRST):**
```bash
# Method 1: Using gh label list (simpler and more reliable)
gh label list --json name --jq '.[].name' > /tmp/available_labels.txt

# Alternative Method 2: Using API directly
gh api repos/{owner}/{repo}/labels --jq '.[].name' > /tmp/available_labels.txt

# Store in a variable for immediate use
AVAILABLE_LABELS=$(gh label list --json name --jq '.[].name')
```

**GitLab (EXECUTE THIS FIRST):**
```bash
# Method 1: Using glab label list (simpler)
glab label list --repo {owner}/{repo} | cut -f1 > /tmp/available_labels.txt

# Alternative Method 2: Using API
PROJECT_ID=$(glab api projects --owned=true --jq '.[] | select(.ssh_url_to_repo == "'$(git remote get-url origin)'") | .id')
glab api projects/$PROJECT_ID/labels --jq '.[].name' > /tmp/available_labels.txt

# Store in a variable for immediate use  
AVAILABLE_LABELS=$(glab label list | cut -f1)
```

**CRITICAL: If label fetching fails, proceed WITHOUT labels rather than using invalid ones:**
```bash
if ! gh label list --json name --jq '.[].name' > /tmp/available_labels.txt 2>/dev/null; then
    echo "Warning: Could not fetch repository labels. Creating PR without labels."
    AVAILABLE_LABELS=""
fi
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

### 3. Label Filtering and Assignment (CRITICAL STEP)

**ONLY apply labels that actually exist in the repository:**
```bash
# IMPORTANT: Only use labels that were confirmed to exist
# Never apply a label without verifying it exists first!

PROPOSED_LABELS="enhancement bug documentation"  # Based on your analysis
FINAL_LABELS=""

# Check each proposed label against the ACTUAL repository labels
for label in $PROPOSED_LABELS; do
    if grep -qx "$label" /tmp/available_labels.txt; then
        # Label exists - safe to use
        FINAL_LABELS="$FINAL_LABELS --label \"$label\""
        echo "✓ Label '$label' exists in repository"
    else
        # Label doesn't exist - skip it
        echo "✗ Label '$label' not found in repository - skipping"
    fi
done

# If no valid labels found, proceed without any
if [[ -z "$FINAL_LABELS" ]]; then
    echo "Note: No matching labels found. Creating PR without labels."
fi
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

## PR Title Generation for Changelogs

**CRITICAL: PR titles appear in changelogs and release notes. They must be user-facing, not technical.**

### Core Principles

1. **Write for end users, not developers**
   - Describe the user impact, not the code change
   - Focus on benefits and improvements users will notice
   - Avoid technical implementation details

2. **Use clear, action-oriented language**
   - Start with verbs when possible
   - Be specific about what changed from the user's perspective
   - Keep it concise but meaningful

3. **Remember the changelog context**
   - Users read these in release notes to understand what's new
   - Titles should make sense without viewing the code
   - Each title should communicate value

### Good vs Bad Examples

#### Features
- ❌ **Bad:** "feat: implement Redis caching layer"
- ✅ **Good:** "Speed up page loading times"

- ❌ **Bad:** "feat: add WebSocket support to notification service"
- ✅ **Good:** "Receive instant notifications without refreshing"

- ❌ **Bad:** "feat: integrate Stripe payment API"
- ✅ **Good:** "Enable secure credit card payments"

#### Bug Fixes
- ❌ **Bad:** "fix: CacheManager has wrong keys set"
- ✅ **Good:** "Ensure displayed user data is always fresh"

- ❌ **Bad:** "fix: null pointer exception in UserService"
- ✅ **Good:** "Prevent app crashes when viewing profiles"

- ❌ **Bad:** "fix: race condition in async handler"
- ✅ **Good:** "Fix occasional duplicate form submissions"

#### Performance
- ❌ **Bad:** "perf: optimize database queries in product listing"
- ✅ **Good:** "Load product catalog 3x faster"

- ❌ **Bad:** "perf: reduce bundle size by 40%"
- ✅ **Good:** "Improve initial page load speed on mobile devices"

#### Security
- ❌ **Bad:** "security: add CSRF token validation"
- ✅ **Good:** "Protect against cross-site request forgery attacks"

- ❌ **Bad:** "security: implement rate limiting on auth endpoints"
- ✅ **Good:** "Prevent brute force login attempts"

#### Refactoring
- ❌ **Bad:** "refactor: move auth logic to middleware"
- ✅ **Good:** "Improve login reliability and performance"

- ❌ **Bad:** "refactor: migrate from callbacks to promises"
- ✅ **Good:** "Enhanced stability in data processing"

### Title Templates by Change Type

**New Features:**
- "Enable [user capability]"
- "Add support for [user action]"
- "Allow users to [specific action]"
- "Introduce [user-facing feature]"

**Bug Fixes:**
- "Fix [user-visible problem]"
- "Resolve issue where [problem description]"
- "Prevent [undesired behavior]"
- "Correct [specific user-facing issue]"

**Improvements:**
- "Improve [aspect] of [feature]"
- "Enhance [user experience area]"
- "Speed up [user action]"
- "Simplify [user task]"

**Breaking Changes:**
- "Update [feature] to [new behavior]"
- "Change how [feature] works"
- "Require [new user action] for [feature]"

### Analyzing Code to Generate User-Facing Titles

When analyzing changes to create a title:

1. **Ask: "What will users notice?"**
   - Will pages load faster?
   - Will something work that was broken?
   - Can they do something new?

2. **Translate technical changes to user benefits:**
   - Database optimization → Faster search results
   - API integration → New functionality available
   - Bug fix → Specific problem solved
   - Refactoring → Better reliability/performance

3. **Avoid these technical terms in titles:**
   - Class names, function names, file names
   - Technical patterns (middleware, service, controller)
   - Implementation details (cache, queue, worker)
   - Internal architecture terms

4. **Use these user-focused terms instead:**
   - Speed, performance, reliability
   - Features, capabilities, options
   - Experience, interface, workflow
   - Security, privacy, safety

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

2. **FIRST: Fetch Available Labels (MANDATORY):**
   ```bash
   # This MUST be done before attempting to create the PR
   echo "Fetching repository labels..."
   if gh label list --json name --jq '.[].name' > /tmp/available_labels.txt; then
       echo "Successfully fetched $(wc -l < /tmp/available_labels.txt) labels"
   else
       echo "Warning: Could not fetch labels. Proceeding without labels."
       FINAL_LABELS=""
   fi
   ```

3. **Create PR (with user-facing title and validated labels):**
   ```bash
   # Generate a user-facing title following the changelog guidelines
   # Example: "Speed up dashboard loading" not "fix: optimize SQL queries"
   PR_TITLE="[User-facing title per guidelines above]"
   
   # Only include labels that were verified to exist
   gh pr create \
     --title "$PR_TITLE" \
     --body "[Generated description]" \
     --base [original-branch] \
     $FINAL_LABELS
   ```
   - **IMPORTANT:** Title must be user-facing for changelogs (see PR Title Generation section)
   - Note: `--base` is set to the branch you started from, not the default branch
   - `$FINAL_LABELS` contains ONLY validated labels that exist in the repository
   - If no valid labels found, `$FINAL_LABELS` will be empty (PR created without labels)

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

2. **FIRST: Fetch Available Labels (MANDATORY):**
   ```bash
   # This MUST be done before attempting to create the MR
   echo "Fetching repository labels..."
   if glab label list | cut -f1 > /tmp/available_labels.txt; then
       echo "Successfully fetched $(wc -l < /tmp/available_labels.txt) labels"
   else
       echo "Warning: Could not fetch labels. Proceeding without labels."
       FINAL_LABELS=""
   fi
   ```

3. **Create MR (with user-facing title and validated labels):**
   ```bash
   # Generate a user-facing title following the changelog guidelines
   # Example: "Improve search accuracy" not "refactor: update search algorithm"
   MR_TITLE="[User-facing title per guidelines above]"
   
   # Only include labels that were verified to exist
   glab mr create \
     --title "$MR_TITLE" \
     --description "[Description]" \
     --target-branch [original-branch] \
     $FINAL_LABELS
   ```
   - **IMPORTANT:** Title must be user-facing for changelogs (see PR Title Generation section)
   - Note: `--target-branch` is set to the branch you started from
   - `$FINAL_LABELS` contains ONLY validated labels that exist in the repository
   - If no valid labels found, `$FINAL_LABELS` will be empty (MR created without labels)

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
  - Title: Allow users to sign in with email and password
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
5. **CRITICAL: Fetch available repository labels BEFORE creating the PR**
   - Use `gh label list` or `glab label list` to get actual labels
   - ONLY apply labels that exist in the fetched list
   - If label fetching fails, create PR without any labels
   - Never assume common labels like "bug" or "enhancement" exist
6. **Generate user-facing PR titles for changelogs**
   - Write titles that describe user impact, not technical changes
   - Avoid implementation details and technical jargon
   - Focus on benefits and improvements users will notice
   - Remember: these titles appear in release notes
7. Generate meaningful PR descriptions with technical details
8. Handle platform differences gracefully
9. Provide clear error messages and next steps
10. Never create duplicate PRs - check if one already exists
11. Set up tracking between local and remote branches
12. Make it clear which branch the PR targets (show "feature → original" flow)

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