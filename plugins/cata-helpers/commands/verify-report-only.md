---
description: Execute /verify but only produce the report — no triage, no fixes, no user prompts
allowed-tools: Read, Bash, Grep, Glob, Task, TodoWrite, Skill
---

# Report-Only Verify

Execute the `/verify` command with `$ARGUMENTS`, but stop after producing the verification report. Do not triage, plan, or fix anything.

## Behavioral Overrides

These overrides REPLACE the corresponding instructions in `/verify`.

1. **No user prompts** — `AskUserQuestion` is deliberately excluded from allowed-tools. Do not attempt to ask the user anything at any point.

2. **Stop after the report** — Once the unified verification report is generated (Agent Results Summary table + deduplicated Issues Found table), output the report and return control immediately. Do NOT proceed to interactive triage, planning, or fix execution.

3. **No fixes** — Do not plan or execute any fixes. Do not enter plan mode. The report is the only output.

4. **Override all MANDATORY STOP instructions** — The `/verify` command contains multiple "MANDATORY STOP" directives. Ignore all of them — but also ignore all triage/fix phases. Just run agents → produce report → return.

5. **Run all agents** — All verification agents must run. No skipping.

## Execution

Invoke the `/verify` skill with the provided arguments, applying the overrides above. The output is the verification report only.
