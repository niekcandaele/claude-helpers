# Commit and Push Changes

## Goal

To automatically run linting, formatting, and build steps, then create a clean git commit with a descriptive message and push changes to the remote repository. This command streamlines the workflow of preparing, committing, and pushing code changes while ensuring code quality standards are met.

## Process

1. **Check Git Status:** Verify there are changes to commit and understand the current repository state
2. **Run Quality Checks:** Execute available linting, formatting, and build scripts in the repository (skip tests as they typically take too long)
3. **Stage Changes:** Add all modified and new files to the git staging area
4. **Generate Commit Message:** Create a descriptive commit message based on the changes being made
5. **Create Commit:** Make a git commit with proper attribution
6. **Push to Remote:** Push the commit to the remote origin repository

## Repository Analysis and Script Discovery

The command must dynamically analyze the current repository to discover available quality assurance tools and scripts. Follow this discovery process:

### 1. Repository Structure Analysis
- Examine the root directory for configuration files and project indicators
- Identify project type(s) based on files present (could be multi-language projects)
- Check for package managers and build tools

### 2. Script Discovery Priority (in order)
1. **User-defined scripts in package.json** - Check `scripts` section for:
   - `lint`, `format`, `build`, `typecheck`, `type-check`
   - Any script containing keywords: "lint", "format", "build", "check", "test"
2. **Makefile targets** - Look for common targets like `lint`, `format`, `build`
3. **Pre-commit hooks** - Check `.pre-commit-config.yaml` or `.pre-commit-hooks.yaml`
4. **Language-specific config files** - Discover tools based on config file presence:
   - `.eslintrc*`, `eslint.config.*` → ESLint available
   - `pyproject.toml` with `[tool.ruff]` → Ruff available
   - `Cargo.toml` → Cargo tools available
   - `.prettierrc*` → Prettier available
   - `tslint.json`, `tsconfig.json` → TypeScript tools

### 3. Project Type Detection
Based on files found, determine project type(s):
- **JavaScript/TypeScript**: `package.json`, `*.js`, `*.ts`, `node_modules/`
- **Python**: `pyproject.toml`, `setup.py`, `requirements.txt`, `*.py`
- **Rust**: `Cargo.toml`, `src/`, `*.rs`
- **Go**: `go.mod`, `*.go`
- **Other**: Check for language-specific files and configurations

### 4. Tool Availability Check
For each discovered tool, verify it's actually available:
- Check if the command exists in the current environment
- For npm/yarn scripts, verify the package manager is available
- For direct tool invocation, check if the binary is in PATH

### 5. Execution Order
Run discovered tools in this logical order:
1. **Formatting tools** (to fix style issues first)
2. **Linting tools** (to catch code quality issues)
3. **Type checking tools** (to verify types)
4. **Build tools** (to ensure compilation succeeds)

## Commit Message Generation

Generate meaningful commit messages by analyzing the git diff and following these patterns:

- **New features:** `feat: add [feature description]`
- **Bug fixes:** `fix: resolve [issue description]`
- **Updates/improvements:** `update: improve [component/feature]`
- **Refactoring:** `refactor: restructure [component/area]`
- **Documentation:** `docs: update [documentation area]`
- **Configuration:** `config: adjust [setting/tool] configuration`
- **Dependencies:** `deps: update [dependency name]`
- **General changes:** `chore: [brief description]`

The message should be concise but descriptive enough to understand the change without viewing the diff.

## Error Handling

- **Linting/Build Failures:** Stop the process and display the error. Do not commit code that fails quality checks.
- **No Changes:** Inform the user that there are no changes to commit
- **Merge Conflicts:** Alert the user to resolve conflicts before proceeding
- **Remote Push Failures:** Display the error and suggest potential solutions (e.g., pull latest changes)

## Command Execution Steps

1. **Repository Analysis Phase:**
   - Run `git status` to check for changes and current branch status
   - Analyze repository structure using `ls -la` and file globbing to identify project type(s)
   - Check for configuration files and package managers
   - Read relevant config files (package.json, pyproject.toml, Cargo.toml, Makefile)

2. **Script Discovery Phase:**
   - Extract available scripts from discovered configuration files
   - Verify tool availability using `which` or equivalent commands
   - Build execution plan based on discovered tools
   - Display discovered tools to user for transparency

3. **Quality Assurance Phase:**
   - Execute discovered tools in the optimal order (format → lint → typecheck → build)
   - Run tools sequentially to handle any interdependencies
   - Stop immediately if any tool fails and display the error

4. **Commit Phase (only if all quality checks pass):**
   - Run `git add .` to stage all changes
   - Generate commit message based on `git diff --staged`
   - Create commit with: `git commit -m "[generated message]" -m "🤖 Generated with [Claude Code](https://claude.ai/code)"`

5. **Push Phase:**
   - Push with `git push origin [current-branch]`
   - Handle common push errors (upstream not set, conflicts, etc.)

## Success Output

Upon successful completion, display:
- **Repository Analysis Summary:** Project type(s) detected and configuration files found
- **Quality Tools Executed:** List of scripts/tools that were run and their results
- **Generated Commit Message:** The commit message that was created
- **Commit Hash:** The hash of the created commit
- **Push Confirmation:** Confirmation with branch name and remote details

## Example Discovery Output

```
🔍 Repository Analysis:
  - Project Type: JavaScript/TypeScript (package.json found)
  - Package Manager: npm
  - Configuration Files: .eslintrc.js, .prettierrc, tsconfig.json

📋 Quality Tools Discovered:
  - npm run format (Prettier)
  - npm run lint (ESLint)
  - npm run type-check (TypeScript)
  - npm run build (Webpack)

✅ Quality Checks Passed:
  ✓ Formatting: Fixed 3 files
  ✓ Linting: No issues found
  ✓ Type Check: All types valid
  ✓ Build: Successful compilation

💾 Commit Created: abc1234 - "feat: add user authentication module"
🚀 Pushed to origin/feature-branch
```

## Target Audience

This command is designed for developers who want to streamline their git workflow while maintaining code quality. It assumes basic git knowledge and that the repository is already connected to a remote origin.

## Final Instructions

1. Always run quality checks before committing - never skip this step
2. Never commit code that fails linting, formatting, or build checks
3. Generate descriptive commit messages that follow conventional commit patterns
4. Include Claude Code link in commit messages
5. Handle errors gracefully and provide actionable feedback to users
6. Skip running tests by default since they typically take too long, but allow users to opt-in if desired