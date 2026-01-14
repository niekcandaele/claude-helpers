#!/bin/bash
# Ralph Execute Stop Hook
# Checks if loop should continue or allow Claude to stop
# Supports both ralph-execute (task completion) and full-execute (full cycle)

set -euo pipefail

# Read hook input JSON
INPUT=$(cat)

# Extract paths
CWD=$(echo "$INPUT" | jq -r '.cwd')
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# Prevent infinite hook loops
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

# Check if config exists
CONFIG_FILE="$CWD/.claude/ralph-loop.local.md"
if [ ! -f "$CONFIG_FILE" ]; then
  # No active loop
  exit 0
fi

# Extract YAML frontmatter
ACTIVE=$(grep "^active:" "$CONFIG_FILE" | awk '{print $2}')
ITERATION=$(grep "^iteration:" "$CONFIG_FILE" | awk '{print $2}')
MAX_ITERATIONS=$(grep "^max_iterations:" "$CONFIG_FILE" | awk '{print $2}')
TASKS_FILE=$(grep "^tasks_file:" "$CONFIG_FILE" | cut -d' ' -f2-)
# Phase field indicates full-execute mode (if present)
PHASE=$(grep "^phase:" "$CONFIG_FILE" | awk '{print $2}' || echo "")

# Check if loop is active
if [ "$ACTIVE" != "true" ]; then
  exit 0
fi

# Check for universal completion markers
if grep -q "<!-- RALPH_MAX_ITERATIONS -->" "$CONFIG_FILE"; then
  echo "⚠ Max iterations reached" >&2
  exit 0
fi

# Check max iterations
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ] && [ "$MAX_ITERATIONS" -gt 0 ]; then
  echo "⚠ Max iterations ($MAX_ITERATIONS) reached" >&2
  exit 0
fi

# ============================================
# FULL-EXECUTE MODE (has phase field)
# Requires full cycle: tasks + verify + PR + CI
# ============================================
if [ -n "$PHASE" ]; then
  # Full-execute mode - check for shipped marker
  if grep -q "<!-- RALPH_SHIPPED -->" "$CONFIG_FILE"; then
    echo "✓ Full cycle complete! Draft PR ready for review." >&2
    exit 0
  fi

  # Check phase-specific completion for progress reporting
  TASKS_DONE="no"
  VERIFY_CLEAN="no"
  PR_CREATED="no"
  CI_PASSED="no"

  grep -q "<!-- TASKS_COMPLETE -->" "$CONFIG_FILE" && TASKS_DONE="yes"
  grep -q "<!-- VERIFY_CLEAN -->" "$CONFIG_FILE" && VERIFY_CLEAN="yes"
  grep -q "<!-- PR_CREATED -->" "$CONFIG_FILE" && PR_CREATED="yes"
  grep -q "<!-- CI_PASSED -->" "$CONFIG_FILE" && CI_PASSED="yes"

  # Get task counts if tasks file exists
  COMPLETE=0
  INCOMPLETE=0
  TASKS_PATH="$CWD/$TASKS_FILE"
  if [ -f "$TASKS_PATH" ]; then
    INCOMPLETE=$(grep -c '^\s*- \[ \]' "$TASKS_PATH" 2>/dev/null) || INCOMPLETE=0
    COMPLETE=$(grep -c '^\s*- \[x\]' "$TASKS_PATH" 2>/dev/null) || COMPLETE=0
  fi

  # Build progress indicators
  IMPL_STATUS="$COMPLETE tasks done, $INCOMPLETE remaining"
  [ "$TASKS_DONE" = "yes" ] && IMPL_STATUS="$IMPL_STATUS ✓" || IMPL_STATUS="$IMPL_STATUS ⏳"
  [ "$VERIFY_CLEAN" = "yes" ] && VERIFY_STATUS="✓ Zero issues" || VERIFY_STATUS="⏳ Pending"
  [ "$PR_CREATED" = "yes" ] && PR_STATUS="✓ Draft PR created" || PR_STATUS="⏳ Pending"
  [ "$CI_PASSED" = "yes" ] && CI_STATUS="✓ Passed" || CI_STATUS="⏳ Pending"

  # Build progress report
  REASON="Continue full-execute iteration $((ITERATION + 1))/$MAX_ITERATIONS

Current phase: $PHASE

Phase Progress:
- Implementation: $IMPL_STATUS
- Verification: $VERIFY_STATUS
- PR Creation: $PR_STATUS
- CI Check: $CI_STATUS

The loop will continue until all phases complete or max iterations reached."

  OUTPUT=$(jq -n \
    --arg decision "block" \
    --arg reason "$REASON" \
    '{decision: $decision, reason: $reason}')

  echo "$OUTPUT"
  exit 0
fi

# ============================================
# RALPH-EXECUTE MODE (no phase field)
# Original behavior - stop when tasks complete
# ============================================

# Check for completion markers
if grep -q "<!-- RALPH_COMPLETE -->" "$CONFIG_FILE"; then
  echo "✓ All tasks complete!" >&2
  exit 0
fi

# Check task completion
TASKS_PATH="$CWD/$TASKS_FILE"
INCOMPLETE=0
COMPLETE=0
if [ -f "$TASKS_PATH" ]; then
  INCOMPLETE=$(grep -c '^\s*- \[ \]' "$TASKS_PATH" 2>/dev/null) || INCOMPLETE=0
  COMPLETE=$(grep -c '^\s*- \[x\]' "$TASKS_PATH" 2>/dev/null) || COMPLETE=0

  if [ "$INCOMPLETE" -eq 0 ] && [ "$COMPLETE" -gt 0 ]; then
    echo "✓ All $COMPLETE tasks complete!" >&2
    exit 0
  fi
fi

# Work not complete - block stop
REASON="Continue iteration $((ITERATION + 1))/$MAX_ITERATIONS

Current progress:
- Tasks complete: $COMPLETE
- Tasks remaining: $INCOMPLETE

The loop will continue working on incomplete tasks.
When all tasks are complete or max iterations is reached, the loop will stop automatically."

OUTPUT=$(jq -n \
  --arg decision "block" \
  --arg reason "$REASON" \
  '{decision: $decision, reason: $reason}')

echo "$OUTPUT"
exit 0
