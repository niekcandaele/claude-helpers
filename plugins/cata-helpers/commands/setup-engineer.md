---
description: Setup or update repository engineer skill with validated, multi-file knowledge
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion, Task
---

# /setup-engineer - Repository Engineer Skill Management

## Goal

Create a comprehensive, **multi-file skill** for this repository with **validated content**. Every piece of information should be verified by actually running commands and exercising the systems.

This command:
- Reads existing documentation first
- Detects areas to investigate (tests, database, API, etc.)
- Presents an investigation plan for approval
- Spawns agents to exercise each area
- Generates a multi-file skill with real, verified content

## Process

### Step 1: Determine Repository Identity

```bash
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
SKILL_DIR=".claude/skills/${REPO_NAME}-engineer"
if [ -d "$SKILL_DIR" ]; then
  echo "Existing skill found at: $SKILL_DIR"
  ls -la "$SKILL_DIR"
else
  echo "No existing skill - will create new one"
fi
```

If skill exists, read all files for later merging.

### Step 3: Read Existing Documentation

**Critical:** Before generating anything, find and read the repository's own documentation:

```bash
# Find documentation
find . -maxdepth 3 -type f \( -name "README.md" -o -name "CONTRIBUTING.md" -o -name "DEVELOPMENT.md" \) 2>/dev/null
find . -maxdepth 2 -type d \( -name "docs" -o -name "documentation" \) 2>/dev/null
ls docs/*.md 2>/dev/null | head -10
```

Read these files and extract:
- Project overview and architecture
- Developer setup instructions
- Build/test commands mentioned
- Repo-specific patterns and conventions
- Known gotchas or requirements

This becomes the foundation for skill content.

### Step 4: Detect Areas to Investigate

Scan the repository to identify what areas need investigation:

```bash
# Testing
ls package.json 2>/dev/null && jq -r '.scripts | keys[]' package.json | grep -i test
ls pytest.ini pyproject.toml jest.config.* vitest.config.* 2>/dev/null
find . -type d -name "__tests__" -o -name "test" -o -name "tests" 2>/dev/null | head -5

# Database
ls docker-compose*.yml 2>/dev/null
grep -l "postgres\|mysql\|mongo\|redis" docker-compose*.yml 2>/dev/null
find . -type d -name "migrations" 2>/dev/null | head -3

# API
find . -type d -name "api" -o -name "routes" -o -name "endpoints" 2>/dev/null | head -5
grep -r "app.get\|app.post\|router\." --include="*.ts" --include="*.js" -l 2>/dev/null | head -5

# Frontend
grep -l "react\|vue\|angular\|svelte" package.json 2>/dev/null
ls -d src/components packages/*/src/components 2>/dev/null

# Build system
ls Makefile 2>/dev/null && grep -E "^[a-zA-Z_-]+:" Makefile | head -10
ls package.json 2>/dev/null && jq -r '.scripts | keys[]' package.json
```

Build a list of areas to investigate based on what exists.

### Step 5: Present Investigation Plan

Before spawning agents, present the plan to the user using AskUserQuestion:

```
Based on my analysis, I found these areas to investigate:

1. **Testing** - Found jest/vitest config, test directories
2. **Database** - Found PostgreSQL in docker-compose
3. **API** - Found Express routes in packages/api
4. **Frontend** - Found React components

I will spawn investigation agents to:
- Run tests and document patterns
- Connect to database and document queries
- Exercise API endpoints
- Document frontend development workflow

Each agent will actually execute commands and report real findings.

Proceed with investigation?
```

Options:
- "Yes, investigate all areas"
- "Let me select which areas"
- "Skip investigation, create skeleton"

### Step 6: Spawn Investigation Agents

**Spawn agents in parallel** for each detected area. Each agent should:

1. **Actually exercise the system** - run commands, make requests, query databases
2. **Document what works** - exact commands with real output
3. **Note gotchas** - things that failed and why
4. **Report findings** - structured output for skill file generation

#### Testing Investigation Agent

```
Task: Investigate testing in this repository

You must ACTUALLY RUN things, not just describe them.

1. Find test configuration:
   - Look for jest.config.*, vitest.config.*, pytest.ini, etc.
   - Read the config to understand the setup

2. Run tests (start small):
   - Try running a single test file first
   - Then try the full test suite
   - Note any setup required (env vars, services)

3. Document findings:
   - Test framework used
   - Command to run all tests
   - Command to run specific tests
   - Command to run tests in watch mode
   - Any required setup (docker services, env vars)
   - Gotchas discovered

4. Report format:
   ## Test Framework
   {what framework, version if discoverable}

   ## Commands
   ### Run All Tests
   \`\`\`bash
   {actual command you ran}
   \`\`\`
   Output: {summary of what happened}

   ### Run Specific Tests
   \`\`\`bash
   {pattern that works}
   \`\`\`

   ## Setup Required
   {any setup needed before tests work}

   ## Gotchas
   {issues you encountered}
```

#### Database Investigation Agent

```
Task: Investigate database in this repository

You must ACTUALLY CONNECT and RUN QUERIES.

1. Find database configuration:
   - Check docker-compose.yml for database services
   - Find connection strings in config files
   - Check for migration tools

2. Connect to database:
   - Use docker compose exec to access database
   - Run sample queries to understand schema
   - Try common debugging queries

3. Document findings:
   - Database type and version
   - How to connect (exact command)
   - How to run migrations
   - Useful debugging queries
   - Schema overview (key tables)

4. Report format:
   ## Database Type
   {postgres/mysql/mongo/etc}

   ## Connection
   \`\`\`bash
   {exact docker compose exec command}
   \`\`\`

   ## Migrations
   \`\`\`bash
   {command to run migrations}
   \`\`\`

   ## Useful Queries
   \`\`\`sql
   -- List tables
   {query}

   -- Debug common issues
   {query}
   \`\`\`

   ## Gotchas
   {issues you encountered}
```

#### API Investigation Agent

```
Task: Investigate API in this repository

You must ACTUALLY MAKE REQUESTS.

1. Find API structure:
   - Locate route definitions
   - Find authentication patterns
   - Check for API documentation (OpenAPI, etc.)

2. Exercise the API:
   - Find how to start the API server
   - Make sample requests
   - Test authentication flow

3. Document findings:
   - How to start the API
   - Base URL pattern
   - Authentication method
   - Key endpoints
   - Example requests that work

4. Report format:
   ## Starting the API
   \`\`\`bash
   {command to start}
   \`\`\`

   ## Authentication
   {how auth works, how to get tokens}

   ## Key Endpoints
   | Method | Endpoint | Description |
   |--------|----------|-------------|
   | GET | /api/... | ... |

   ## Example Requests
   \`\`\`bash
   curl {actual request that works}
   \`\`\`

   ## Gotchas
   {issues you encountered}
```

#### Frontend Investigation Agent (if applicable)

```
Task: Investigate frontend development in this repository

1. Find frontend setup:
   - Framework (React, Vue, etc.)
   - Build tools (Vite, webpack, etc.)
   - Component structure

2. Run development server:
   - Find the dev command
   - Note the URL and port
   - Check for hot reload

3. Document findings:
   - Framework and build tool
   - Dev server command
   - How to add new components
   - Testing approach for frontend

4. Report format:
   ## Framework
   {React/Vue/etc with version}

   ## Development Server
   \`\`\`bash
   {command to start dev server}
   \`\`\`
   URL: {localhost:port}

   ## Component Structure
   {where components live, naming conventions}

   ## Gotchas
   {issues you encountered}
```

### Step 7: Generate Multi-File Skill

Create the skill directory structure:

```bash
mkdir -p .claude/skills/${REPO_NAME}-engineer
```

Generate files based on investigation results:

#### SKILL.md (entry point)

```markdown
---
name: {REPO_NAME}-engineer
description: {REPO_NAME} repository knowledge - architecture, testing, database, API, development workflows. Use when working on this codebase, running tests, debugging, or understanding the project.
---

# {REPO_NAME} Engineer

{Brief overview from README/docs - actual content, not placeholder}

## Quick Reference

| Area | File | Key Command |
|------|------|-------------|
| Testing | [TESTING.md](TESTING.md) | `{actual test command}` |
| Database | [DATABASE.md](DATABASE.md) | `{actual db command}` |
| API | [API.md](API.md) | `{actual api command}` |
{add rows for each area that was investigated}

## Architecture

{From documentation - actual architecture info}

## Getting Started

{From documentation - actual setup steps}

## Maintenance

This skill should stay accurate. During work:

- **Discover something useful?** → Ask the human if it should be added
- **Find outdated info?** → Ask the human if it should be updated
- **Run `/setup-engineer`** → Bulk update from current session
```

#### TESTING.md

```markdown
# Testing

{Content from Testing Investigation Agent - real, verified commands}
```

#### DATABASE.md

```markdown
# Database

{Content from Database Investigation Agent - real, verified commands}
```

#### API.md

```markdown
# API

{Content from API Investigation Agent - real, verified commands}
```

(Create additional files for each investigated area)

### Step 8: Ensure CLAUDE.md Reference

Check and update CLAUDE.md:

```markdown
# Repository Engineer Skill

This repository has an engineer skill at `.claude/skills/{REPO_NAME}-engineer/`.

Claude will automatically discover and use this skill. The skill contains multiple files:
- `SKILL.md` - Overview and quick reference
- `TESTING.md` - Test commands and patterns
- `DATABASE.md` - Database access and debugging
- `API.md` - API usage and authentication
{list other files}

## Proactive Maintenance

During your work, if you discover something that should be in the engineer skill:
- A debugging technique that worked
- A command or workflow that's useful
- A gotcha or non-obvious behavior

**ASK THE HUMAN:** "Should I add this to the engineer skill?"

Also watch for **outdated information**:
- Commands that no longer work
- Patterns that have changed

**ASK THE HUMAN:** "The skill says X but I found Y - should I update it?"

---

{rest of existing CLAUDE.md content}
```

### Step 9: Report Results

```
✅ Engineer skill created: .claude/skills/{REPO_NAME}-engineer/

Files created:
- SKILL.md (overview and quick reference)
- TESTING.md (verified test commands)
- DATABASE.md (verified database access)
- API.md (verified API usage)
{list all files}

All content has been verified by actually running commands.

💡 Claude will automatically discover and use this skill.
💡 Run /setup-engineer anytime to add new knowledge.
```

## Updating Existing Skills

When a skill already exists and you're adding session knowledge:

1. Read all existing skill files
2. Identify what new knowledge to add from the session
3. Determine which file(s) should be updated
4. Merge new content, preserving existing verified content
5. Update any outdated information discovered

## Error Handling

### Investigation Agent Fails

If an agent can't complete its investigation:
- Note what worked and what failed
- Include partial findings in the skill
- Mark sections as "needs verification"

### No Areas Detected

If nothing is detected:
- Ask user what areas exist
- Create skeleton files for user to fill in

### Cannot Write Files

```
❌ Cannot write to .claude/skills/
Check directory permissions.
```

## Session-Aware Updates

When run after a work session:

1. Analyze conversation for new knowledge
2. Identify which skill file(s) should be updated
3. Present changes to user for approval
4. Update specific files, not the whole skill
