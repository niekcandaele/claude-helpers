# Claude Code Helper Commands

A collection of productivity-enhancing commands and agents for Claude Code that streamline the software development workflow from requirements to implementation.

## Installation

### Using Claude Code Plugin System (Recommended)

1. Add the marketplace:
   ```
   /plugin marketplace add niekcandaele/claude-helpers
   ```

2. Install the plugin:
   ```
   /plugin install cata-helpers
   ```

Commands will be available as `/cata-helpers:command-name` (e.g., `/cata-helpers:commit-and-push`).

### Legacy Installation

If you're using an older version of Claude Code without plugin support:

```bash
curl -sSL https://raw.githubusercontent.com/niekcandaele/claude-helpers/main/install.sh | bash
```

## Required Permissions

Some agents and commands require specific permissions. Add these to your `.claude/settings.json` or `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git log:*)",
      "Bash(git rev-parse:*)",
      "Bash(git remote get-url:*)",
      "Bash(gh run list:*)",
      "Bash(gh api:*)",
      "Bash(find:*)",
      "Bash(ls:*)",
      "Bash(mkdir:*)",
      "Bash(curl:*)",
      "WebSearch",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:raw.githubusercontent.com)"
    ]
  }
}
```

### Optional MCP Servers

Some agents benefit from MCP server integration:

- **Playwright MCP** - For cata-debugger, cata-tester, and cata-ux-reviewer browser automation
- **PostgreSQL MCP** - For cata-debugger and cata-researcher database inspection
- **Redis MCP** - For cata-debugger and cata-researcher cache inspection

## Overview

### Agents

Specialized agents for specific review and analysis tasks (all follow "Report, Never Fix" philosophy):

| Agent | Purpose |
|-------|---------|
| `cata-reviewer` | Strict code review, detects over-engineering and AI patterns |
| `cata-debugger` | Evidence-based troubleshooting with systematic investigation |
| `cata-researcher` | Critical research with multi-source verification |
| `cata-tester` | No-nonsense test execution (100% pass rate only) |
| `cata-ux-reviewer` | User experience evaluation across all interfaces |
| `technical-writer` | Documentation editing following Google/Grafana style |

### Commands

| Command | Purpose |
|---------|---------|
| `/setup-engineer` | Create/update repository-specific engineer skill |
| `/create-issue` | Transform notes into GitHub issues |
| `/commit-and-push` | Quality checks, commit, and push |
| `/create-pr` | Create PR with branch management |
| `/check-ci` | Monitor CI/CD and fix failures |
| `/catchup` | Summarize branch changes |
| `/handoff` | Document progress for session continuity |
| `/rebase` | Rebase branch onto target with conflict guidance |
| `/ralph-execute` | Autonomous full-cycle: execute plan, verify, PR, CI |

## Commands

### Setup Engineer (`/setup-engineer`)

Create or update a repository-specific engineer skill that captures knowledge about how to work with the codebase.

**Usage:**
```
/setup-engineer
```

**What it does:**
- **First run**: Explores the repository to discover tests, scripts, database setup, debugging approaches
- **Subsequent runs**: Extracts knowledge from the current session and adds it to the skill

**Key feature - Session awareness:**
When you run this command after doing work (debugging, implementing features, etc.), Claude analyzes the conversation and captures useful knowledge:
- Commands that worked
- Debugging techniques
- Gotchas and solutions
- Environment setup requirements

**Files created:**
- `.claude/commands/{repo-name}-engineer.md` - The engineer skill (loaded automatically in future sessions)
- Updates `CLAUDE.md` with reference to the skill

### Create Issue (`/create-issue`)

Transform notes, meeting minutes, or project documentation into well-structured GitHub issues.

**Usage:**
```
/create-issue [file path or text description]
```

**What it does:**
- Analyzes codebase to understand project context
- Extracts issue details from notes or text
- Generates clear, concise issue title
- Creates comprehensive issue body with markdown formatting
- Intelligently detects and applies relevant labels
- Always adds 'ai' label for transparency
- Creates issue via GitHub CLI (`gh`)

**Example:**
```
/create-issue meetings/sprint-planning.md
/create-issue "Users report login page is slow on mobile devices"
```

### Commit and Push (`/commit-and-push`)

Automatically runs quality checks, creates a clean commit, and pushes to remote.

**Usage:**
```
/commit-and-push
```

**What it does:**
- Analyzes repository to discover available linting, formatting, and build tools
- Runs quality checks in optimal order (format -> lint -> typecheck -> build)
- Stages all changes for commit
- Generates descriptive commit message based on changes
- Creates commit with proper Claude Code attribution
- Pushes to remote origin

**Features:**
- Dynamic tool discovery (works with any project type)
- Supports npm scripts, Makefile targets, and direct tool invocation
- Stops if any quality check fails

### Create PR (`/create-pr`)

Creates a pull request with automatic branch management and platform detection.

**Usage:**
```
/create-pr [optional PR title]
```

**What it does:**
- Checks if you're on a feature branch (creates one if on main/master)
- Runs commit-and-push workflow for uncommitted changes
- Detects git platform (GitHub, GitLab, Bitbucket)
- Creates PR using appropriate CLI tool (gh, glab)
- Generates PR title and description from commits

### Check CI (`/check-ci`)

Monitors CI/CD pipeline status after commits and provides fixes for failures.

**Usage:**
```
/check-ci [commit-sha or branch]
```

**What it does:**
- Detects CI platform (GitHub Actions, GitLab CI, CircleCI, etc.)
- Monitors pipeline status with real-time updates
- Analyzes failure logs when CI fails
- Identifies error patterns (test failures, build errors, linting)
- Proposes specific code fixes for identified issues

### Handoff (`/handoff`)

Document current work state for session continuity.

**Usage:**
```
/handoff
```

**What it does:**
- Captures git history and uncommitted changes
- Documents TODO progress
- Generates comprehensive handoff document
- Saves to `/tmp` for easy copy/paste

## Complete Workflow Example

```bash
# 0. Set up repository knowledge (first time)
/setup-engineer

# 1. Create issues from meeting notes
/create-issue meetings/sprint-planning.md

# 2. Autonomously execute plan, verify, create PR, and pass CI
/ralph-execute

# 3. Monitor CI and fix failures
/check-ci
```

## Development

### Validating the Plugin

```bash
just validate
```

### Testing Locally

```bash
just test
```

## Contributing

Visit the [GitHub repository](https://github.com/niekcandaele/claude-helpers) to contribute.
