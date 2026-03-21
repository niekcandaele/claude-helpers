---
description: Review a pull/merge request by fetching PR details, checking CI, and running verification agents on the changes
argument-hint: <PR URL, e.g. https://github.com/org/repo/pull/123>
allowed-tools: Read, Bash, Grep, Glob, Task, AskUserQuestion
---

# Review Pull Request

## Goal

Review an external pull request (GitHub) or merge request (GitLab) by fetching its details, checking CI status, and running verification agents on the changed code. Produces a combined report. This is a **read-only** operation — never push, comment on the PR, or modify code.

## Input

Required: `$ARGUMENTS` — a PR/MR URL.

Supported formats:
- GitHub: `https://github.com/{owner}/{repo}/pull/{number}`
- GitLab: `https://gitlab.com/{owner}/{repo}/-/merge_requests/{number}`

Options:
- `--with-ux`: Also run `cata-ux-reviewer` and `cata-exerciser` (skipped by default)

If no URL provided, show:
```
Usage: /review-pr <PR URL>
Example: /review-pr https://github.com/acme/api/pull/42
```

## Process

### 1. Parse PR URL

Extract from the URL:
- **Platform**: `github.com` → GitHub, `gitlab.com` (or other) → GitLab
- **Owner/Repo**: e.g. `acme/api`
- **PR Number**: e.g. `42`

If the URL doesn't match either pattern, error with usage example.

### 2. Validate Local Repository

This command MUST be run from within the correct repository clone.

```bash
# Confirm we're in a git repo
git rev-parse --git-dir

# Get local remote URL
REMOTE_URL=$(git remote get-url origin)
```

Extract `owner/repo` from `REMOTE_URL` (handle both SSH and HTTPS formats):
- HTTPS: `https://github.com/acme/api.git` → `acme/api`
- SSH: `git@github.com:acme/api.git` → `acme/api`

Compare with the `owner/repo` from the PR URL (case-insensitive, strip `.git` suffix).

If they don't match, **stop immediately** with:
```
ERROR: Wrong repository.

This PR belongs to: {pr-owner}/{pr-repo}
You are currently in: {local-owner}/{local-repo}

To review this PR, first navigate to your local clone of {pr-owner}/{pr-repo}, then run:
  /review-pr {original URL}
```

### 3. Verify CLI Tool

**GitHub:**
```bash
which gh && gh auth status
```

**GitLab:**
```bash
which glab && glab auth status
```

If the CLI is not installed or not authenticated, error with installation/auth instructions and stop.

### 4. Fetch PR Metadata

**GitHub:**
```bash
gh pr view {number} --json title,body,author,baseRefName,headRefName,state,labels,additions,deletions,changedFiles,url
```

**GitLab:**
```bash
glab mr view {number}
```

Display a brief PR summary to the user before proceeding.

### 5. Checkout PR Branch

**GitHub:**
```bash
gh pr checkout {number}
```

**GitLab:**
```bash
glab mr checkout {number}
```

This ensures all code is available locally for verification agents.

### 6. Get Changed Files and Diff

**GitHub:**
```bash
# File list (scope for agents)
gh pr diff {number} --name-only

# Full diff (for scope line ranges)
gh pr diff {number}
```

**GitLab:**
```bash
glab mr diff {number}
```

Parse the diff to build a scope list with file paths and changed line ranges.

### 7. Check CI Status

**GitHub:**
```bash
gh pr checks {number}
```

**GitLab:**
```bash
glab ci status
```

Record the status of each check/job (pass/fail/pending/running). Do NOT wait for pending checks — report current state.

### 8. Launch Verification Agents

Launch agents **in parallel** using the Task tool. Each agent prompt MUST include the PR scope context.

**Agents to launch:**
- `cata-reviewer` — Code review scoped to PR diff
- `cata-tester` — Run test suite with scope awareness
- `cata-coherence` — Pattern/consistency check on changed files
- `cata-architect` — Architectural health analysis
- `cata-security` — Security vulnerability detection
- `cata-coderabbit` — CodeRabbit CLI analysis

**If `--with-ux` flag is present**, also launch:
- `cata-ux-reviewer` — UX review of changed surfaces
- `cata-exerciser` — Manual E2E testing

**Scope context template for each agent prompt:**

```
VERIFICATION SCOPE (PR #{number}: {title}):
Files in scope:
- {file1} (modified, lines X-Y, A-B)
- {file2} (added, entire file)
- {file3} (deleted)

CRITICAL SCOPE CONSTRAINTS:
- ONLY flag issues in code that was ADDED or MODIFIED in the PR diff
- DO NOT flag issues in surrounding context or old code unless it blocks the new changes
- DO NOT flag issues in files not listed in scope
- Focus exclusively on the quality of the NEW or CHANGED code

Exception: You MAY flag issues in old code IF:
1. The new changes directly interact with or depend on that old code
2. The old code issue causes the new code to be incorrect
3. The old code issue creates a blocker for the new functionality

[Agent-specific instructions follow...]
```

Use the same agent invocation patterns as `/verify` — see `commands/verify.md` for the detailed prompt templates per agent.

### 9. Generate Combined Report

Combine all information into a single report:

```
# PR Review Report

## PR Overview

| Field | Value |
|-------|-------|
| Title | {title} |
| Author | {author} |
| Branch | {head} → {base} |
| Changes | +{additions} / -{deletions} across {changedFiles} files |
| URL | {url} |

**Description:** {first ~200 chars of body, or "No description provided"}

---

## CI Status

| Check | Status | Details |
|-------|--------|---------|
| {check1} | PASS/FAIL/PENDING | {duration or error} |
| {check2} | PASS/FAIL/PENDING | {duration or error} |

**Overall:** {N} passed, {N} failed, {N} pending

---

## Agent Results Summary

| Agent | Status | Notes |
|-------|--------|-------|
| cata-tester | X passed, Y failed | [brief note] |
| cata-reviewer | Completed | Found N items |
| cata-coherence | Completed | Found N items |
| cata-architect | Completed | Found N items |
| cata-security | Completed | Found N items |
| cata-coderabbit | Completed / FAILED | Found N items / NOT INSTALLED |
| cata-ux-reviewer | Completed / Skipped | [if --with-ux] |
| cata-exerciser | PASSED / FAILED / Skipped | [if --with-ux] |

---

## Issues Found

[Deduplicated issues from all agents, sorted by severity descending]

| ID | Sev | Title | Sources | Location | Description |
|----|-----|-------|---------|----------|-------------|
| RI-1 | 9 | [Title] | tester, reviewer | file:line | [Combined description] |
| RI-2 | 7 | [Title] | security | file:line | [Description] |

*Severity: 9-10 Critical | 7-8 High | 5-6 Moderate | 3-4 Low | 1-2 Trivial*

**Total: N issues from M agent findings (deduplicated)**

---

## Verdict

[One-paragraph overall assessment: is this PR ready to merge, or what needs attention?]
```

Issue IDs use **RI-{n}** prefix (Review Issue) to distinguish from /verify's VI-{n} prefix.

### 10. Present Report and STOP

Present the full report to the user, then **STOP**.

Do NOT:
- Auto-fix any issues
- Comment on the PR
- Approve or reject the PR
- Start interactive triage
- Suggest running /verify again

The user decides what to do next.

## Issue Deduplication

Same approach as `/verify`:
1. Collect all findings from each agent
2. Identify duplicates (same file/location, same root cause, same symptom from different angles)
3. Merge into single issue with all source agents listed and highest severity used
4. Assign sequential RI-{n} IDs
5. Sort by severity descending
