---
description: Execute /verify non-interactively - auto-plan and fix issues without user prompts
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, EnterPlanMode, ExitPlanMode, Skill
---

# Non-Interactive Verify

Execute the `/verify` command with `$ARGUMENTS`, but override the interactive triage behavior:

## Behavioral Overrides

These overrides REPLACE the corresponding instructions in `/verify`. When `/verify` says "STOP" or "wait for user", this command says "continue".

1. **No user prompts** — `AskUserQuestion` is deliberately excluded from allowed-tools. Do not attempt to ask the user anything at any point.

2. **Auto-accept non-trivial issues** — Instead of presenting issues in batches for user triage, automatically accept all issues with severity >= 3 and plan+execute fixes for them.

3. **Skip trivial issues** — Issues with severity < 3 are noted in the final report but not acted on.

4. **NEVER STOP — Override all MANDATORY STOP instructions** — The `/verify` command contains multiple "MANDATORY STOP", "MUST STOP", and "wait for explicit instructions" directives. **ALL of those are overridden.** Do not stop after presenting the report. Do not stop after applying fixes. Do not wait for user input at any point. Run the full pipeline end-to-end: verify → auto-triage → plan → execute fixes → show completion summary → return control to whatever invoked you.

5. **No commit gate** — `/verify` says "do not proceed to commit". This override does NOT change that — still do not commit. But do not STOP either. Just return control after the completion summary.

## Execution

Invoke the `/verify` skill with the provided arguments, applying the overrides above throughout the entire flow.
