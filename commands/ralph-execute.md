---
description: Autonomously execute plan, verify, create PR, and pass CI - full cycle until human handoff
allowed-tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebSearch, WebFetch, TodoWrite, Task, SlashCommand
---

# Ralph Execute - Autonomous Full-Cycle Loop

Read the plan file and execute it to completion.

Run this command:

/ralph-loop:ralph-loop "Read the plan file and execute it to completion. Use TaskCreate and TaskUpdate to track your progress. After making all changes, run /cata-helpers:verify-non-interactive. If ANY issues are found, analyse each one, fix them, then run verify again. Repeat until verify reports 0 issues. Once clean, open a PR (or update the existing one). Check CI status with gh pr checks. If any checks are failing, read the logs, fix the failures, and re-run verify. Do NOT output the completion promise until ALL of the following are true: 1. verify-non-interactive reports 0 issues 2. A PR is open 3. All CI checks are green. When all three conditions are satisfied, output: <promise>DONE</promise>" --max-iterations 50 --completion-promise "DONE"
