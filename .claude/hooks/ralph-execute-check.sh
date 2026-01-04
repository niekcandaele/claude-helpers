#!/bin/bash
# Ralph Execute Stop Hook
# Checks if loop should continue or allow Claude to stop

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

# Check if loop is active
if [ "$ACTIVE" != "true" ]; then
  exit 0
fi

# Check for completion markers
if grep -q "<!-- RALPH_COMPLETE -->" "$CONFIG_FILE"; then
  # Tasks complete - allow stop
  echo "✓ All tasks complete!" >&2
  exit 0
fi

if grep -q "<!-- RALPH_MAX_ITERATIONS -->" "$CONFIG_FILE"; then
  # Max iterations reached - allow stop
  echo "⚠ Max iterations reached" >&2
  exit 0
fi

# Check max iterations
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ] && [ "$MAX_ITERATIONS" -gt 0 ]; then
  # Hit max iterations - allow stop
  echo "⚠ Max iterations ($MAX_ITERATIONS) reached" >&2
  exit 0
fi

# Check task completion
TASKS_PATH="$CWD/$TASKS_FILE"
if [ -f "$TASKS_PATH" ]; then
  INCOMPLETE=$(grep -c '^\s*- \[ \]' "$TASKS_PATH" || echo "0")
  COMPLETE=$(grep -c '^\s*- \[x\]' "$TASKS_PATH" || echo "0")

  if [ "$INCOMPLETE" -eq 0 ] && [ "$COMPLETE" -gt 0 ]; then
    # All tasks complete - allow stop
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
