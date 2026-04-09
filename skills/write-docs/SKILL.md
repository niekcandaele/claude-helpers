---
name: write-docs
description: Write or edit technical documentation following Google and Write the Docs best practices
argument-hint: <topic, file path, or description of what to document>
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - MultiEdit
  - Grep
  - Glob
  - Skill
---

# Write Technical Documentation

## Goal

Write or edit technical documentation following professional style guides. Produces clear, scannable prose that avoids common AI writing patterns.

## Input

`$ARGUMENTS` may contain:
- A file path to edit (e.g., `README.md`, `docs/api.md`)
- A topic to document (e.g., "authentication flow", "CLI usage")
- A description of what needs documenting

If no arguments provided, check conversation context for what the user wants documented.

## Process

1. **Determine scope:** Parse `$ARGUMENTS` or conversation to understand what needs documenting
2. **Read existing content:** If editing, read the file first
3. **Invoke the `technical-writer` skill:** Delegate the actual writing to the specialized skill
4. **Write output:** Save the documentation to the appropriate file

## Style Requirements

The `technical-writer` skill enforces these standards:

**Prose over bullets:** Use flowing prose unless items are truly equivalent and independent. Bullets fragment information that reads better as sentences.

**Voice:** Active voice, present tense, second person ("you").

**Brevity:** Sentences under 25 words, paragraphs 3 sentences max.

**Forbidden patterns:**
- Bolded first words of bullet points
- "It's not X, it's Y" comparisons
- Filler phrases ("It's important to note that...")
- Hedging language ("might", "could potentially")
- Generic AI patterns and formulaic structures

## Skill Invocation

Invoke `technical-writer` with this prompt structure:

```
Use the Skill tool to invoke `technical-writer` with the documentation task,
any existing content to edit, and the target file path.
```

The skill will produce documentation that follows Google Developer Documentation Style Guide and Write the Docs best practices.

## Output

Save the final documentation to the appropriate location:
- If user specified a file path, write there
- If documenting code, use conventional locations (`README.md`, `docs/`, etc.)
- If unclear, ask the user where to save
