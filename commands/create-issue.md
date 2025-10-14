# Create GitHub Issue

## Goal

Transform notes, meeting minutes, or project documentation into well-structured GitHub issues with proper context from codebase analysis. This command uses the `gh` CLI to create issues that follow industry best practices for clarity, completeness, and actionability.

## Input

Required: Issue source via $ARGUMENTS (one of):
- File path to notes/documentation (e.g., `meetings/2024-10-sprint-planning.md`)
- Quoted text description (e.g., `"Users report login page is slow"`)
- Pasted text (if invoking interactively)

## Process

1. **Parse Input:** Determine if input is a file path or direct text
2. **Analyze Codebase:** Understand project context and structure
3. **Extract Issue Details:** Parse content to identify problem/feature
4. **Generate Issue:** Create well-structured title and body
5. **Detect Labels:** Intelligently categorize the issue
6. **Create via gh CLI:** Submit issue to GitHub
7. **Display Result:** Show issue URL and details

## Input Handling

### File Path Detection

Check if $ARGUMENTS points to an existing file:

```bash
# Test if argument is a file
if [[ -f "$ARGUMENTS" ]]; then
    echo "Reading issue details from: $ARGUMENTS"
    CONTENT=$(cat "$ARGUMENTS")
else
    echo "Using provided text as issue content"
    CONTENT="$ARGUMENTS"
fi
```

### Supported File Types

- Markdown files (`.md`) - meeting notes, project docs
- Text files (`.txt`) - plain notes
- Any readable text format

## Codebase Analysis

Before creating the issue, analyze the project to provide relevant context:

### 1. Project Overview

```bash
# Read project README for context
if [[ -f "README.md" ]]; then
    PROJECT_CONTEXT=$(head -50 README.md)
fi

# Get repository info
REPO_INFO=$(gh repo view --json name,description,primaryLanguage)
```

### 2. Project Structure Analysis

Identify key components to reference in the issue:

```bash
# Find primary language/framework
PRIMARY_LANG=$(gh repo view --json primaryLanguage --jq '.primaryLanguage.name')

# Identify project type indicators
if [[ -f "package.json" ]]; then
    PROJECT_TYPE="JavaScript/Node.js"
elif [[ -f "requirements.txt" ]] || [[ -f "setup.py" ]]; then
    PROJECT_TYPE="Python"
elif [[ -f "Cargo.toml" ]]; then
    PROJECT_TYPE="Rust"
elif [[ -f "go.mod" ]]; then
    PROJECT_TYPE="Go"
elif [[ -f "pom.xml" ]] || [[ -f "build.gradle" ]]; then
    PROJECT_TYPE="Java"
fi
```

### 3. Architectural Context

```bash
# Check for common directories
HAS_TESTS=$(find . -type d -name "test*" -o -name "__tests__" 2>/dev/null | head -1)
HAS_DOCS=$(find . -type d -name "docs" -o -name "documentation" 2>/dev/null | head -1)
HAS_CI=$(ls .github/workflows/*.yml 2>/dev/null || ls .gitlab-ci.yml 2>/dev/null)
```

## Issue Generation

### Title Generation

Create concise, imperative titles following best practices:

**Guidelines:**
- Use imperative mood (e.g., "Add", "Fix", "Update", not "Adding", "Fixed")
- No period at the end
- Keep under 60 characters
- Be specific and descriptive
- Start with action verb

**Examples:**
- ❌ Bad: "There's a problem with the login page loading slowly"
- ✅ Good: "Fix slow login page load time"

- ❌ Bad: "Adding dark mode feature"
- ✅ Good: "Add dark mode toggle to user settings"

- ❌ Bad: "Documentation is incomplete."
- ✅ Good: "Document API authentication flow"

### Body Structure

Use markdown formatting for maximum readability:

```markdown
## Problem/Feature Description
[Clear description of what needs to be done and why it matters]

## Context
[Background information from the input, with project-specific details]

## Expected Behavior (for bugs)
[What should happen]

## Current Behavior (for bugs)
[What actually happens]

## Proposed Solution (for features)
[How this could be implemented, referencing actual codebase components]

## Steps to Reproduce (for bugs)
1. [First step]
2. [Second step]
3. [Observe issue]

## Technical Context
[Relevant files, components, or patterns from codebase analysis]
- Project type: [detected type]
- Related components: [specific files/modules if identifiable]

## Acceptance Criteria
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]
- [ ] [Tests added/updated]

## Additional Notes
[Any other relevant information from the source material]
```

### Content Analysis

Parse input to identify issue type and details:

**Bug Indicators:**
- Keywords: "bug", "error", "crash", "broken", "fails", "doesn't work", "issue"
- Stack traces or error messages
- "expected vs actual" comparisons

**Feature Indicators:**
- Keywords: "feature", "add", "new", "support", "implement", "allow users to"
- User stories or use cases
- Requirements or specifications

**Documentation Indicators:**
- Keywords: "document", "readme", "guide", "tutorial", "docs", "explain"
- References to missing documentation

**Enhancement Indicators:**
- Keywords: "improve", "enhance", "optimize", "refactor", "better"
- Performance concerns
- UX improvements

## Label Detection

Intelligently assign labels based on content analysis:

### 1. Fetch Available Labels

**CRITICAL: Always fetch repository labels first**

```bash
# Get available labels from repository
if gh label list --json name --jq '.[].name' > /tmp/issue_labels.txt 2>/dev/null; then
    echo "✓ Fetched $(wc -l < /tmp/issue_labels.txt) available labels"
else
    echo "⚠ Could not fetch labels. Will create issue without labels."
    LABELS=""
fi
```

### 2. Analyze Content for Label Keywords

Map keywords to appropriate labels:

```bash
# Always include 'ai' label to indicate issue was created by AI
PROPOSED_LABELS="ai"

# Bug detection
if echo "$CONTENT" | grep -qiE "bug|error|crash|broken|fail"; then
    PROPOSED_LABELS="$PROPOSED_LABELS bug"
fi

# Enhancement/Feature detection
if echo "$CONTENT" | grep -qiE "feature|enhancement|add|new|implement"; then
    PROPOSED_LABELS="$PROPOSED_LABELS enhancement"
fi

# Documentation detection
if echo "$CONTENT" | grep -qiE "document|readme|docs|guide|tutorial"; then
    PROPOSED_LABELS="$PROPOSED_LABELS documentation"
fi

# Performance detection
if echo "$CONTENT" | grep -qiE "slow|performance|optimize|speed|latency"; then
    PROPOSED_LABELS="$PROPOSED_LABELS performance"
fi

# Security detection
if echo "$CONTENT" | grep -qiE "security|vulnerability|exploit|auth|permission"; then
    PROPOSED_LABELS="$PROPOSED_LABELS security"
fi

# Testing detection
if echo "$CONTENT" | grep -qiE "test|testing|spec|coverage"; then
    PROPOSED_LABELS="$PROPOSED_LABELS testing"
fi

# UI/UX detection
if echo "$CONTENT" | grep -qiE "ui|ux|interface|design|layout|styling"; then
    PROPOSED_LABELS="$PROPOSED_LABELS ui/ux"
fi

# Priority detection
if echo "$CONTENT" | grep -qiE "urgent|critical|blocker|high priority"; then
    PROPOSED_LABELS="$PROPOSED_LABELS priority:high"
fi
```

### 3. Validate and Apply Labels

**IMPORTANT: Only use labels that exist in the repository**

```bash
FINAL_LABELS=""
AI_LABEL_MISSING=false

# Check each proposed label against repository labels
for label in $PROPOSED_LABELS; do
    # Check exact match
    if grep -qx "$label" /tmp/issue_labels.txt; then
        FINAL_LABELS="$FINAL_LABELS --label \"$label\""
        echo "✓ Label '$label' will be applied"
    else
        # Check case-insensitive match
        MATCHED_LABEL=$(grep -ix "$label" /tmp/issue_labels.txt | head -1)
        if [[ -n "$MATCHED_LABEL" ]]; then
            FINAL_LABELS="$FINAL_LABELS --label \"$MATCHED_LABEL\""
            echo "✓ Label '$MATCHED_LABEL' will be applied"
        else
            if [[ "$label" == "ai" ]]; then
                AI_LABEL_MISSING=true
                echo "⚠ Label 'ai' not found in repository - consider creating it"
            else
                echo "✗ Label '$label' not found in repository - skipping"
            fi
        fi
    fi
done

# Note if AI label is missing (informational only, don't fail)
if [[ "$AI_LABEL_MISSING" == "true" ]]; then
    echo ""
    echo "Note: To create the 'ai' label, run:"
    echo "  gh label create ai --description 'Issue created by AI' --color '8B5CF6'"
fi
```

## GitHub CLI Integration

### 1. Verify gh CLI Installation

```bash
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is not installed"
    echo ""
    echo "Install instructions:"
    echo "  macOS:   brew install gh"
    echo "  Linux:   sudo apt install gh"
    echo "  Windows: winget install GitHub.cli"
    echo ""
    echo "After installation, run: gh auth login"
    exit 1
fi
```

### 2. Check Authentication

```bash
if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated with GitHub"
    echo ""
    echo "Please run: gh auth login"
    exit 1
fi
```

### 3. Verify Repository Context

```bash
# Check if in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    echo ""
    echo "Either:"
    echo "  1. Run this command from within a git repository"
    echo "  2. Use --repo flag: gh issue create --repo owner/repo ..."
    exit 1
fi

# Check if repository has a remote
if ! git remote get-url origin &> /dev/null; then
    echo "❌ Error: No remote repository configured"
    echo ""
    echo "Add a remote: git remote add origin https://github.com/owner/repo.git"
    exit 1
fi
```

### 4. Create Issue

```bash
# Create the issue with gh CLI
gh issue create \
    --title "$ISSUE_TITLE" \
    --body "$ISSUE_BODY" \
    $FINAL_LABELS

# Capture the issue URL
ISSUE_URL=$(gh issue list --limit 1 --json url --jq '.[0].url')
```

## Advanced Features

### Template Support

If the repository has issue templates, offer to use them:

```bash
# Check for issue templates
TEMPLATES=$(gh api repos/:owner/:repo/contents/.github/ISSUE_TEMPLATE --jq '.[].name' 2>/dev/null)

if [[ -n "$TEMPLATES" ]]; then
    echo "📝 Available issue templates:"
    echo "$TEMPLATES"
    echo ""
    echo "Note: You can specify a template with --template flag in future runs"
fi
```

### Related Issues Detection

Check for similar existing issues:

```bash
# Extract key terms from content
KEY_TERMS=$(echo "$CONTENT" | grep -oiE "\w{5,}" | sort -u | head -10)

# Search for potentially related issues
echo "🔍 Checking for related issues..."
RELATED=$(gh issue list --search "$KEY_TERMS" --limit 5 --json number,title,url)

if [[ -n "$RELATED" ]] && [[ "$RELATED" != "[]" ]]; then
    echo ""
    echo "⚠️  Found potentially related issues:"
    echo "$RELATED" | jq -r '.[] | "  #\(.number): \(.title)"'
    echo ""
    read -p "Continue creating new issue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Issue creation cancelled"
        exit 0
    fi
fi
```

### Project Board Integration

Optionally add to project board:

```bash
# List available projects
PROJECTS=$(gh project list --owner @me --format json 2>/dev/null)

if [[ -n "$PROJECTS" ]] && [[ "$PROJECTS" != "[]" ]]; then
    echo "📊 Available projects:"
    echo "$PROJECTS" | jq -r '.projects[] | "  - \(.title)"'
    echo ""
    echo "Add --project flag to assign to a project"
fi
```

## Error Handling

### Rate Limiting

```bash
# Check API rate limit
RATE_LIMIT=$(gh api rate_limit --jq '.rate.remaining')
if [[ $RATE_LIMIT -lt 10 ]]; then
    RESET_TIME=$(gh api rate_limit --jq '.rate.reset')
    echo "⚠️  Warning: GitHub API rate limit low ($RATE_LIMIT requests remaining)"
    echo "Resets at: $(date -d @$RESET_TIME)"
fi
```

### Network Issues

```bash
# Test connectivity
if ! gh api user &> /dev/null; then
    echo "❌ Error: Cannot connect to GitHub API"
    echo "Check your internet connection and try again"
    exit 1
fi
```

### Invalid Input

```bash
# Validate content isn't empty
if [[ -z "$CONTENT" ]]; then
    echo "❌ Error: No issue content provided"
    echo ""
    echo "Usage:"
    echo "  /create-issue \"Issue description here\""
    echo "  /create-issue path/to/notes.md"
    exit 1
fi
```

## Output Format

### Success Case

```
✅ Issue Created Successfully!

📋 Issue Details:
  - Title: Fix slow login page load time
  - Number: #142
  - Labels: ai, bug, performance
  - URL: https://github.com/user/repo/issues/142

🎯 Next Steps:
  1. Review the issue in your browser
  2. Add additional details if needed
  3. Assign to team members
  4. Link to relevant PRs or projects
```

### With Warnings

```
⚠️  Issue created with warnings

📋 Issue Details:
  - Title: Add dark mode support
  - Number: #143
  - Labels: ai, enhancement
  - URL: https://github.com/user/repo/issues/143

⚠️  Warnings:
  - No issue templates found in repository

The issue was created successfully.
```

### Missing 'ai' Label

```
⚠️  Label 'ai' not found in repository - consider creating it

Note: To create the 'ai' label, run:
  gh label create ai --description 'Issue created by AI' --color '8B5CF6'

✅ Issue Created Successfully!

📋 Issue Details:
  - Title: Document API authentication flow
  - Number: #144
  - Labels: documentation
  - URL: https://github.com/user/repo/issues/144

Note: The 'ai' label could not be applied as it doesn't exist in the repository.
```

## Best Practices Integration

Follow industry best practices for issue quality:

### 0. AI Attribution Label
- **ALWAYS include 'ai' label** to indicate the issue was created by AI
- Helps teams track and manage AI-generated issues
- Provides transparency in issue creation workflow
- If label doesn't exist, provide helpful creation command but continue
- Recommended label color: `8B5CF6` (purple)

### 1. Clear and Concise Titles
- Use imperative mood
- Be specific, not generic
- Avoid technical jargon when possible
- Keep under 60 characters

### 2. Well-Structured Body
- Use markdown formatting for readability
- Include context and motivation
- Provide clear acceptance criteria
- Add code references when relevant

### 3. Appropriate Categorization
- Assign relevant labels only
- Use priority labels when applicable
- Tag with component/area labels

### 4. Actionable Content
- Make requirements specific and testable
- Include enough detail for implementation
- Link to related issues or PRs

### 5. Searchable Information
- Use clear terminology
- Include relevant keywords
- Reference specific features or components

## Final Instructions

### Core Workflow
1. Parse input to determine if file path or direct text
2. Read content from file or use provided text
3. Analyze codebase to gather project context
4. Extract key information from content (problem, expected behavior, etc.)
5. Generate clear, imperative issue title
6. Create comprehensive issue body with markdown formatting
7. Detect and validate appropriate labels
8. Check for similar existing issues
9. Create issue via `gh issue create` with validated labels
10. Display success message with issue URL

### Content Analysis
11. Identify issue type (bug, feature, documentation, etc.)
12. Extract technical details and context
13. Generate acceptance criteria based on requirements
14. Reference specific codebase components when identifiable
15. **ALWAYS include 'ai' label** to indicate issue was AI-generated

### Quality Checks
16. Ensure title follows best practices (imperative, concise, descriptive)
17. Validate labels exist before applying (including 'ai' label)
18. Check for duplicate/similar issues
19. Verify gh CLI is installed and authenticated
20. Confirm repository context is valid

### Error Handling
21. Gracefully handle missing gh CLI with installation instructions
22. Handle authentication failures with clear guidance
23. Proceed without labels if label fetch fails (don't fail the entire operation)
24. If 'ai' label doesn't exist, note this in output but continue
25. Validate input content is not empty
26. Check network connectivity before API calls

### User Experience
27. Provide clear progress updates during execution
28. Show related issues before creating (avoid duplicates)
29. Display comprehensive success message with all details
30. Suggest next steps after issue creation

## Usage Examples

```bash
# From a file containing meeting notes
/create-issue meetings/sprint-planning-2024-10.md

# From direct text description
/create-issue "Users report login page takes 10+ seconds to load. Happens on Chrome and Firefox."

# With quoted multi-line text
/create-issue "Feature request: Add dark mode
Users want ability to switch between light and dark themes
Should remember preference across sessions"

# After copying notes from clipboard
/create-issue
[Paste your meeting notes or issue description]
```

## Integration with Other Commands

This command works well with the existing workflow:

```bash
# After a meeting discussing a new feature:
/create-issue meetings/feature-planning.md

# Then create a design for the feature:
/cata-proj:design [feature-name]

# Generate implementation tasks:
/cata-proj:tasks .design/*/design.md

# Execute the implementation:
/cata-proj:execute [feature-name]

# Create a PR when done:
/create-pr
```
