# Claude Code Helper Commands

A collection of productivity-enhancing commands for Claude Code that streamline the software development workflow from requirements to implementation.

## Overview

These commands provide a structured approach to feature development:
1. **Create PRD** - Generate a Product Requirements Document from user input
2. **Generate Tasks** - Convert a PRD into an actionable task list
3. **Process Tasks** - Execute tasks systematically with progress tracking

## Installation

Run this one-liner to download and install all commands:

```bash
mkdir -p ~/.claude/commands && curl -s https://raw.githubusercontent.com/niekcandaele/claude-helpers/master/commands/{create-prd.md,generate-tasks.md,process-tasks.md} -o ~/.claude/commands/#1
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
- Offers parallel or sequential execution modes
- Implements one task at a time (or multiple in parallel)
- Updates task completion status
- Asks for user approval between tasks
- Maintains a list of modified files

**Example:**
```
/process-tasks tasks/tasks-prd-user-profile-editing.md
```

## Complete Workflow Example

Here's how to use all three commands together:

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
# - Ask if you want parallel or sequential execution
# - Work through each task systematically
# - Update progress and ask for approval between tasks
```

## Benefits

- **Structured Development**: Move from idea to implementation systematically
- **Clear Requirements**: PRDs ensure all stakeholders understand the feature
- **Task Management**: Break complex features into manageable chunks
- **Dependency Tracking**: Ensure tasks are completed in the correct order
- **Progress Visibility**: See exactly what's been done and what's remaining
- **Junior Developer Friendly**: Clear, explicit instructions in all outputs

## Notes

- All generated files are saved in a `tasks/` directory in your project
- Commands are designed to work together but can be used independently
- Task lists support dependency management with `[depends on: X.Y]` notation
- PRDs and task lists are written for junior developers to understand

## Contributing

To contribute to these commands, visit the [GitHub repository](https://github.com/niekcandaele/claude-helpers).