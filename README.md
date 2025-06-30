# Claude Code Helper Commands

A collection of productivity-enhancing commands for Claude Code that streamline the software development workflow from requirements to implementation.

## Overview

These commands provide a structured approach to feature development:
1. **Create PRD** - Generate a Product Requirements Document from user input
2. **Generate Tasks** - Convert a PRD into an actionable task list
3. **Process Tasks** - Execute tasks systematically with progress tracking
4. **Commit and Push** - Run quality checks, commit with good message, and push to remote

## Installation

### Automatic Install (Recommended)

Run this one-liner to download and install all commands:

```bash
curl -sSL https://raw.githubusercontent.com/niekcandaele/claude-helpers/main/install.sh | bash
```

### Manual Install

If you prefer to install manually:

```bash
# Download and extract commands folder
curl -L https://github.com/niekcandaele/claude-helpers/archive/main.tar.gz | tar -xz --strip-components=1 claude-helpers-main/commands
# Move to Claude Code commands directory
mkdir -p ~/.claude && mv commands ~/.claude/
```

## Commands

### 1. Create PRD (`/create-prd`)

Creates a detailed Product Requirements Document based on user input.

**Usage:**
```
/create-prd [feature description]
```

**What it does:**
- Asks clarifying questions about the feature
- Generates a comprehensive PRD including:
  - Goals and objectives
  - User stories
  - Functional requirements
  - Success metrics
  - Technical considerations
- Saves the PRD as `tasks/prd-[feature-name].md`

**Example:**
```
/create-prd Add user profile editing functionality
```

### 2. Generate Tasks (`/generate-tasks`)

Converts a PRD into a structured task list with dependencies.

**Usage:**
```
/generate-tasks tasks/prd-[feature-name].md
```

**What it does:**
- Analyzes the PRD's functional requirements
- Creates high-level parent tasks
- Breaks down into detailed sub-tasks
- Identifies task dependencies
- Lists relevant files to be created/modified
- Saves as `tasks/tasks-prd-[feature-name].md`

**Example:**
```
/generate-tasks tasks/prd-user-profile-editing.md
```

### 3. Process Tasks (`/process-tasks`)

Executes tasks from a task list with progress tracking.

**Usage:**
```
/process-tasks tasks/tasks-prd-[feature-name].md
```

**What it does:**
- Reads the task list and checks dependencies
- Implements tasks one at a time in sequential order
- Updates task completion status
- Asks for user approval between tasks
- Maintains a list of modified files

**Example:**
```
/process-tasks tasks/tasks-prd-user-profile-editing.md
```

### 4. Commit and Push (`/commit-and-push`)

Automatically runs quality checks, creates a clean commit, and pushes to remote.

**Usage:**
```
/commit-and-push
```

**What it does:**
- Analyzes repository to discover available linting, formatting, and build tools
- Runs quality checks in optimal order (format → lint → typecheck → build)
- Stages all changes for commit
- Generates descriptive commit message based on changes
- Creates commit with proper Claude Code attribution
- Pushes to remote origin

**Features:**
- Dynamic tool discovery (works with any project type)
- Supports npm scripts, Makefile targets, and direct tool invocation
- Stops if any quality check fails
- Handles common git errors gracefully

**Example:**
```
/commit-and-push
```

## Complete Workflow Example

Here's how to use all four commands together for a complete development cycle:

```bash
# 1. Create a PRD for a new feature
/create-prd Add shopping cart functionality to e-commerce site

# Claude will ask clarifying questions, then create:
# tasks/prd-shopping-cart.md

# 2. Generate tasks from the PRD
/generate-tasks tasks/prd-shopping-cart.md

# Claude will create:
# tasks/tasks-prd-shopping-cart.md

# 3. Process the tasks
/process-tasks tasks/tasks-prd-shopping-cart.md

# Claude will:
# - Work through each task systematically in sequential order
# - Update progress and ask for approval between tasks

# 4. Commit and push the completed work
/commit-and-push

# Claude will:
# - Run available quality checks (linting, formatting, build)
# - Create a descriptive commit message
# - Push to remote repository
```

## Benefits

- **Complete Development Cycle**: From requirements to deployed code in structured steps
- **Clear Requirements**: PRDs ensure all stakeholders understand the feature
- **Task Management**: Break complex features into manageable chunks
- **Dependency Tracking**: Ensure tasks are completed in the correct order
- **Progress Visibility**: See exactly what's been done and what's remaining
- **Quality Assurance**: Automated linting, formatting, and build checks before commit
- **Clean Git History**: Descriptive commit messages with proper attribution
- **Junior Developer Friendly**: Clear, explicit instructions in all outputs

## Notes

- All generated files are saved in a `tasks/` directory in your project
- Commands are designed to work together but can be used independently
- Task lists support dependency management with `[depends on: X.Y]` notation
- PRDs and task lists are written for junior developers to understand

## Contributing

To contribute to these commands, visit the [GitHub repository](https://github.com/niekcandaele/claude-helpers).