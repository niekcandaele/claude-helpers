---
description: Setup or update repository engineer skill with knowledge from current session
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion, Task
---

# /setup-engineer - Repository Engineer Skill Management

## Goal

Manage the repository's engineer skill file - a persistent knowledge base about how to work with this specific repository. This command is **declarative**: run it anytime to either create the skill (if missing) or update it with knowledge from the current session.

Use cases:
- **Initial setup**: Run in a new repo to create the engineer skill by exploring the codebase
- **After learning something**: Run after debugging, implementing, or discovering something useful to capture that knowledge

## Process

### Step 1: Determine Repository Identity

```bash
# Try to get repo name from git remote
REPO_URL=$(git remote get-url origin 2>/dev/null)
if [ -n "$REPO_URL" ]; then
  REPO_NAME=$(basename -s .git "$REPO_URL")
else
  REPO_NAME=$(basename "$(pwd)")
fi
echo "Repository: $REPO_NAME"
```

### Step 2: Check for Existing Skill

```bash
# Check if engineer skill exists
SKILL_PATH=".claude/commands/${REPO_NAME}-engineer.md"
if [ -f "$SKILL_PATH" ]; then
  echo "Existing skill found: $SKILL_PATH"
else
  echo "No existing skill - will create new one"
fi
```

If skill exists, read its current content for later merging.

### Step 3: Analyze Session Context

**This is the key session-aware behavior.** Analyze what happened in this conversation:

1. **Review conversation history**: What work was done? What problems were solved? What commands were run?

2. **Check git state**:
   ```bash
   # Recent commits on current branch
   git log --oneline -10

   # Uncommitted changes
   git status --porcelain

   # What files changed recently
   git diff --name-only HEAD~5..HEAD 2>/dev/null || git diff --name-only
   ```

3. **Extract learnable knowledge**: Identify things worth documenting:
   - Commands that worked (test commands, build commands, debug commands)
   - Debugging techniques that solved problems
   - Gotchas or non-obvious behaviors discovered
   - Environment setup requirements
   - Error messages and their solutions

### Step 4: If No Skill Exists - Explore Repository

When creating a new skill, actively explore the repository to populate sections:

#### 4a. Detect Repository Stack

```bash
# Check for package managers and build systems
ls package.json 2>/dev/null && echo "Node.js project"
ls pyproject.toml setup.py requirements.txt 2>/dev/null && echo "Python project"
ls Cargo.toml 2>/dev/null && echo "Rust project"
ls go.mod 2>/dev/null && echo "Go project"
ls Makefile 2>/dev/null && echo "Has Makefile"

# Check for test configuration
ls jest.config.* vitest.config.* pytest.ini .pytest.ini 2>/dev/null

# Check for database
ls docker-compose*.yml 2>/dev/null | xargs grep -l "postgres\|mysql\|mongo\|redis" 2>/dev/null
find . -type d -name "migrations" 2>/dev/null | head -3

# Check for frontend
grep -l "react\|vue\|angular\|svelte" package.json 2>/dev/null

# Check for existing documentation
ls README.md CONTRIBUTING.md docs/*.md 2>/dev/null | head -5
```

#### 4b. For Each Detected Area: Research → Execute → Learn

**Tests:**
1. Find test command (package.json scripts, Makefile targets)
2. Actually run tests to verify they work
3. Note output, timing, any prerequisites

**Scripts:**
1. List available scripts (package.json, Makefile)
2. Document what each does

**Database (if detected):**
1. Check docker-compose for database services
2. Find migration commands
3. Document connection patterns

**Frontend/Backend (if detected):**
1. Find dev server commands
2. Document debugging approaches

#### 4c. Ask User When Stuck

If you can't figure out how something works after trying, use AskUserQuestion:

```
AskUserQuestion:
  question: "How do you run tests in this project?"
  options:
    - "npm test"
    - "make test"
    - "pytest"
    - "cargo test"
```

### Step 5: Merge Knowledge

Combine:
- Existing skill content (preserve what's there)
- New session learnings (add to appropriate sections)
- Exploration findings (if new skill)

When updating an existing skill:
- Add new information to relevant sections
- Don't duplicate existing content
- Update outdated information if you have better data
- Add new sections if needed

### Step 6: Generate/Update Skill File

Create the directory if needed:
```bash
mkdir -p .claude/commands
```

Write the skill file with this structure:

```markdown
---
description: {REPO_NAME} repository knowledge and development guide
---

# {REPO_NAME} Engineer

This skill contains essential knowledge for working with the {REPO_NAME} repository.

## Repository Overview

{Brief description from README.md or exploration}

**Stack:** {detected languages/frameworks}
**Build System:** {detected build tools}

## Running Tests

{Verified test commands with examples}

### Run All Tests
\`\`\`bash
{test command}
\`\`\`

### Run Specific Tests
\`\`\`bash
{pattern for running specific tests}
\`\`\`

## Scripts and Commands

| Command | Description |
|---------|-------------|
| {cmd} | {description} |

## Database

{Only include if database detected}

### Setup
\`\`\`bash
{database setup commands}
\`\`\`

### Migrations
\`\`\`bash
{migration commands}
\`\`\`

## Debugging

{Debugging approaches for this codebase}

### Frontend
{If applicable}

### Backend
{If applicable}

### Common Issues
{Known gotchas and solutions}

## Build and Deploy

### Local Build
\`\`\`bash
{build command}
\`\`\`

### Production
{Production build/deploy info if available}

## Common Issues and Solutions

{Issues discovered during exploration or session}

| Issue | Solution |
|-------|----------|
| {error/problem} | {how to fix it} |

## Maintenance

This skill should stay accurate and useful. During work:

- **Discover something useful?** → Ask the human if it should be added
- **Find outdated info here?** → Ask the human if it should be updated/removed
- **Run `/setup-engineer`** → Bulk update from current session

The human decides what goes in. Claude suggests, human approves.
```

### Step 7: Ensure CLAUDE.md Reference

Check if CLAUDE.md exists and references the engineer skill:

```bash
if [ -f CLAUDE.md ]; then
  grep -q "engineer" CLAUDE.md && echo "Reference exists" || echo "Need to add reference"
else
  echo "No CLAUDE.md - will create"
fi
```

If reference is missing, prepend to CLAUDE.md (or create it):

```markdown
# Repository Engineer Skill

**CRITICAL:** At session start, read `.claude/commands/{REPO_NAME}-engineer.md` for repository knowledge.

## Proactive Maintenance

During your work, if you discover something that should be in the engineer skill:
- A debugging technique that worked
- A command or workflow that's useful
- A gotcha or non-obvious behavior
- An error and its solution

**ASK THE HUMAN:** "Should I add this to the engineer skill?"

Also watch for **outdated information** in the skill:
- Commands that no longer work
- Patterns that have changed
- Information that contradicts what you just learned

**ASK THE HUMAN:** "The skill says X but I found Y - should I update it?"

The goal is keeping the skill accurate and useful, not just accumulating information.

---

{rest of existing CLAUDE.md content}
```

### Step 8: Report Results

Output summary:

```
✅ Engineer skill updated: .claude/commands/{REPO_NAME}-engineer.md

Changes:
- {what was added/updated}

Skill now includes:
- Repository overview
- Test commands
- {other sections present}

💡 The skill will be loaded automatically in future sessions.
💡 Run /setup-engineer anytime to add new knowledge.
```

## Error Handling

### Not a Git Repository
```
⚠️  Not in a git repository.
Using directory name: {dirname}
```
Continue without git context.

### Cannot Write to .claude/commands
```
❌ Cannot write to .claude/commands/
Check directory permissions.
```

### No Learnable Content
If running in update mode but no new knowledge was found:
```
ℹ️  No new knowledge to add from this session.
Current skill is up to date.

Run /setup-engineer after:
- Debugging an issue
- Discovering how something works
- Learning a new command or trick
```

## Examples

```bash
# Initial setup in a new repo
/setup-engineer

# After figuring out how to debug something
# ... debugging session ...
/setup-engineer
# → Adds debugging techniques to skill

# After discovering test patterns
# ... working with tests ...
/setup-engineer
# → Updates test section with new findings

# After setting up database locally
# ... database work ...
/setup-engineer
# → Adds database setup instructions
```

## Session-Aware Behavior

The power of this command is its session awareness. When you run it, consider:

1. **What problems did we solve?** Document the solutions.
2. **What commands worked?** Add them to the appropriate section.
3. **What gotchas did we discover?** Add to common issues.
4. **What debugging steps helped?** Add to debugging section.

The goal is building a knowledge base that makes future sessions more effective. Each run should capture something useful (when there's something to capture).
