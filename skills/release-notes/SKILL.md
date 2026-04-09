---
name: release-notes
description: >
  Generate user-facing release notes from technical change information (commits,
  PRs, diffs, branch comparisons, or raw text). Goes deep — follows commit
  references to PRs, issues, and bug reports to understand the full story behind
  each change, then produces narrative prose that communicates what changed and
  why it matters. Works with GitHub, GitLab, and Jira. Use this skill whenever
  the user asks for release notes, changelogs, "what's new" summaries, or wants
  to communicate changes to users, stakeholders, or customers — even if they
  just say "write up what changed" or "summarize the release."
argument-hint: "[v1.2.0..v1.3.0 | #42 #43 #44 | main..release/1.3 | raw change description]"
---

# Release Notes Generator

Generate user-facing release notes from: $ARGUMENTS

Release notes are for humans, not machines. The goal is to communicate what changed and why it matters — at the level your audience cares about. A commit documents code evolution; a release note documents significance to the user.

## Step 1: Parse Input

Detect what the user provided and gather the raw change data accordingly.

**Version/tag range** (matches `v1.2.0..v1.3.0` or `1.2..1.3`):
```bash
git log --format='%H %s' $RANGE
git log --format='%B---COMMIT_BOUNDARY---' $RANGE
git diff --stat $RANGE
```

**Branch comparison** (matches `main..feature` or `origin/main..HEAD`):
```bash
git log --format='%H %s' $RANGE
git log --format='%B---COMMIT_BOUNDARY---' $RANGE
git diff --stat $RANGE
```

**PR numbers** (matches `#42`, `#43`, etc.):
```bash
gh pr view <num> --json title,body,commits,labels
```

**Raw text**: If the input doesn't match any pattern above, treat it as a direct description of changes. Skip git commands and work from the text. Also skip Steps 2 and 3 — go straight to Step 4.

**No arguments**: Compare current branch against base:
```bash
CURRENT_BRANCH=$(git branch --show-current)
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
# Fallback: try main, master, develop
git log --format='%H %s' $DEFAULT_BRANCH..$CURRENT_BRANCH
git log --format='%B---COMMIT_BOUNDARY---' $DEFAULT_BRANCH..$CURRENT_BRANCH
git diff --stat $DEFAULT_BRANCH..$CURRENT_BRANCH
```

## Step 2: Detect Platform

Figure out where this project lives and where its issues are tracked. These can be different — a project might host code on GitHub but track issues in Jira.

### Code host

Parse the git remote to detect the platform:
```bash
git remote get-url origin
```

- `github.com` → GitHub, use `gh` CLI
- `gitlab.com` (or a custom GitLab domain) → GitLab, use `glab` CLI
- Anything else → git-only mode (skip PR/issue lookups)

### Issue tracker

Scan the commit messages gathered in Step 1 for reference patterns:

- `#123` style references → issues live on the code host (GitHub or GitLab)
- `PROJ-123` style references (uppercase letters, dash, number) → Jira. Use the Atlassian MCP tools if available (`mcp__claude_ai_Atlassian__getJiraIssue`)
- Both patterns can appear in the same project — check for both

If the platform tools aren't available or authentication fails, fall back gracefully to git-only mode. Don't block on this.

## Step 3: Deep Dive — Follow the References

This is what turns a commit log paraphrase into real release notes. Commits tell you _what_ changed in code. PRs tell you _why_ it was done. Issues tell you _who asked for it and what problem they had_. All three are important.

### Extract references

Scan every commit message from Step 1 for:
- PR/MR numbers: `#123` (GitHub), `!123` (GitLab)
- Issue numbers: `#456` (GitHub/GitLab), `PROJ-789` (Jira)
- URLs pointing to PRs or issues

Deduplicate — many commits reference the same PR. Build a unique list of PRs and issues to fetch.

### Fetch PRs/MRs

For each unique PR reference:

**GitHub:**
```bash
gh pr view <num> --json title,body,closingIssuesReferences,labels,commits
```

**GitLab:**
```bash
glab mr view <num> --output json
```

Read the PR description carefully — this is where developers explain:
- The motivation for the change
- What user-visible impact it has
- Design decisions and trade-offs
- Screenshots or before/after comparisons

### Fetch linked issues

For each issue referenced by PRs (via `closingIssuesReferences` on GitHub, or mentioned in PR/commit text):

**GitHub:**
```bash
gh issue view <num> --json title,body,labels
```

**GitLab:**
```bash
glab issue view <num> --output json
```

**Jira:**
Use `mcp__claude_ai_Atlassian__getJiraIssue` with the issue key (e.g., `PROJ-789`).

Issue bodies are where the real context lives — user stories, bug reports with reproduction steps, feature requests explaining what users need and why. This is gold for writing release notes that speak to users.

### Build a context map

For each logical change, you now have up to three layers of context:
- **Commits** — what changed in code
- **PR description** — why it was done, how it was approached
- **Issue body** — the original user request, bug report, or feature spec
- **Labels** — categorization hints (bug, feature, breaking-change, security, etc.)

Not every change will have all three. Some commits won't reference a PR. Some PRs won't link to issues. Use whatever is available — even one layer deeper than the commit message dramatically improves the release notes.

### Scaling for large releases

For releases with many commits (50+), focus your lookups on unique PRs — most commits map back to a small number of PRs. If there are too many to fetch individually, prioritize:
1. PRs with `breaking`, `security`, or `feature` labels
2. PRs that close issues (they have user-facing context)
3. PRs with the longest descriptions (more context to work with)

## Step 4: Understand the Project

Before writing anything, understand who will read these notes. Scan the repo quickly:

1. **Project type**: Check `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, or `README.md` to determine if this is a library, CLI tool, web app, API, framework, or plugin
2. **Audience**: Library → developers/API consumers. CLI → terminal users. Web app → end users. API → integrators
3. **Existing changelog**: Check for `CHANGELOG.md`, `CHANGES.md`, or `HISTORY.md`. If one exists, read its most recent entry and match its conventions (heading style, entry format, tone)

This context shapes every decision in the next steps — a library's notes can mention API changes directly, while an end-user app's notes should describe outcomes, not implementation.

## Step 5: Analyze and Curate

This is the core transformation — turning code changes into user-facing communication. Use the full context map from Step 3, not just commit messages.

### Filter out noise

Skip changes that don't affect users:
- CI/CD configuration changes (unless they affect release/deploy behavior users depend on)
- Linter/formatter config, whitespace fixes
- Internal refactoring with no behavior change
- Dependency version bumps (unless they fix a user-visible bug or security issue)
- Test-only changes

### Group related commits

Multiple commits that implement one feature or fix become **one entry**. Look for:
- Commits referencing the same PR or issue number
- Sequential commits touching the same files with related messages
- "fixup" or "address review" commits that follow an initial implementation

### Identify breaking changes

Scan for these signals — breaking changes must never be buried:
- `BREAKING CHANGE:` or `BREAKING:` in commit bodies
- `!` after the type in conventional commits (e.g., `feat!:`)
- Removed public APIs, changed function signatures, renamed config options
- Database migrations that require user action
- Changed default behavior
- Labels like `breaking`, `breaking-change` on PRs

### Transform language using the full context

This is where the deep dive pays off. Instead of just rephrasing commit messages, use the richer context:

- **Issue has a bug report?** Use the user's experience to frame the fix: "Players reported crashes when joining servers with custom mods" → "Fix crash when joining modded servers"
- **PR description explains user impact?** Prefer that framing over the commit title
- **Issue has a feature request with use cases?** Explain what users can now do, not what was implemented
- **Labels indicate category?** Use them to help with grouping (bug, feature, security, etc.)
- **No deeper context available?** Fall back to transforming the commit message as before

Examples of the transformation:
- Commit: "Fix null pointer in UserService.getProfile()" / Issue: "App crashes when I click my profile" → "Fix crash when viewing user profiles"
- Commit: "Add Redis caching to product queries" / PR: "Product search was taking 3+ seconds for large catalogs" → "Speed up product search — results now load instantly even for large catalogs"
- Commit: "Bump lodash from 4.17.20 to 4.17.21" → "Fix security vulnerability in lodash dependency" (if it's a security fix) or skip (if routine)

## Step 6: Write the Notes

The release notes should read as **short narrative prose** — a few paragraphs that tell the story of the release. Not a bullet list, not a categorized changelog. The raw commit/PR list already exists; the point of this skill is to produce something different: a human summary that someone can read in 30 seconds and understand what changed and why it matters.

### Structure

Group related changes into short paragraphs by theme. A natural flow is:

1. **Lead with the headline features** — what's new and exciting. Open with the version number in bold and go straight into what the biggest additions are, explaining what they enable for the user.
2. **Infrastructure or performance improvements** — if there are backend changes that affect the user experience (faster queries, better scalability), weave them into a paragraph.
3. **Smaller improvements and UX changes** — navigation improvements, new views, quality-of-life additions.
4. **Bug fixes** — close with a paragraph summarizing the reliability and bug fix work. You don't need to list every fix individually — group them by theme ("several reliability issues", "a handful of UI bugs") and call out the most notable ones specifically.

Not every release needs all four sections. A small patch release might be a single paragraph. A major release might need five or six. Let the content dictate the shape.

### Tone

- Write in **present tense**, conversational but not casual — like a thoughtful teammate explaining the release to someone who uses the product
- Use "you" to address the reader directly ("you can now import your shop listings")
- Technical terms are fine when the audience would know them — don't dumb things down, but don't use internal jargon either
- Keep it tight. Each paragraph should be 2-4 sentences. The whole thing should be readable in under a minute

### Breaking changes

If the release has breaking changes, lead with them before everything else. Be direct about what changed and what the user needs to do. This is the one place where a short bullet list is appropriate — breaking changes need to be scannable and unmissable.

### Example

Here's what good narrative release notes look like:

```markdown
**v0.5.0** introduces Shop Actions, a new module component type that lets you
create automated actions triggered by shop purchases — opening up new
possibilities for your in-game economy. You can now also react to player
inventory changes through hook events, enabling modules for loot tracking,
item-based triggers, and more.

On the infrastructure side, events are now stored in ClickHouse, which means
faster queries and better scalability as your player count grows. If you're
migrating from CSMM, you can now import your shop listings directly.

This release also fixes several reliability issues — database connection pool
exhaustion that could occur around midnight, cronjob failures under high load,
and a handful of UI bugs including the version number incorrectly showing as
"0.0.0".
```

Notice: no bullet lists, no category headers, no "Added/Fixed/Changed" taxonomy. Just clear prose that a user can read and understand.

## What to avoid

- **Bullet lists and categorized changelogs**: the raw changelog already exists — don't recreate it in a slightly different format. The value of this skill is the narrative transformation
- **Commit log dumps**: listing every commit verbatim defeats the purpose
- **Vague summaries**: "Various bug fixes and improvements" tells the reader nothing
- **Internal-only changes**: users don't care about CI pipeline config or dependency bumps
- **Jargon mismatch**: don't tell end users about "middleware refactoring" — tell them what's faster or fixed
- **Buried breaking changes**: if something breaks existing usage, it goes first

## Output

Present the release notes directly in the conversation. Do not write to a file unless the user explicitly asks — and if they do, ask where they want it (CHANGELOG.md, RELEASE_NOTES.md, etc.).

When writing to a GitHub release or file, structure it as:

1. The narrative summary at the top
2. A horizontal rule (`---`)
3. The full raw changelog below — visible, not hidden in a collapsible/spoiler tag. People will miss it otherwise.
