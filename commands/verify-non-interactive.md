---
description: Execute /verify non-interactively - auto-plan and fix issues without user prompts
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, EnterPlanMode, ExitPlanMode, Skill
---

# Non-Interactive Verify

Execute the `/verify` command with `$ARGUMENTS`, but override the interactive triage behavior:

## Behavioral Overrides

1. **No user prompts** — `AskUserQuestion` is deliberately excluded from allowed-tools. Do not attempt to ask the user anything at any point.

2. **Auto-accept non-trivial issues** — Instead of presenting issues in batches for user triage, automatically accept all issues with severity >= 3 and plan+execute fixes for them.

3. **Skip trivial issues** — Issues with severity < 3 are noted in the final report but not acted on.

4. **Auto-proceed through all phases** — Do not stop and wait for user input between verification, triage, and fix execution. Run the full pipeline end-to-end.

## Execution

Invoke the `/verify` skill with the provided arguments, applying the overrides above throughout the entire flow.
