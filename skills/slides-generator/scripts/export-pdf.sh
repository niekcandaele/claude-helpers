#!/usr/bin/env bash
# export-pdf.sh — deterministically render a slides-generator HTML deck to PDF.
#
# Uses headless Chrome's native print-to-PDF. No Python or Node dependencies.
# Page size, per-slide pagination, animation suppression, and nav-chrome
# hiding are all controlled by the `@media print` block in viewport-base.css
# so this script stays minimal and the deck's author has one place to tune
# behavior.
#
# Usage:
#   export-pdf.sh <slides.html> [-o output.pdf] [--chrome <binary>] [--wait-ms N]

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: export-pdf.sh <slides.html> [options]

Render a slides-generator HTML deck to a PDF using headless Chrome.
Each slide becomes one page; page size (1280x720 by default) comes from
the @page rule in viewport-base.css.

Arguments:
  <slides.html>          Path to the deck's HTML file.

Options:
  -o, --output PATH      Output PDF path. Default: replace .html with .pdf.
  --chrome PATH          Chromium/Chrome binary to use. Default: auto-detect
                         in PATH. Looks for chromium, chromium-browser,
                         google-chrome, google-chrome-stable, chrome.
  --wait-ms N            Milliseconds to let JS, fonts, and images settle
                         before snapshotting. Default: 10000 (10s).
  -h, --help             Show this help and exit.

Example:
  export-pdf.sh slides.html -o final.pdf

Dependencies:
  - Chromium or Google Chrome installed on the system.
  - The HTML deck must include the base @media print rules from
    viewport-base.css so pagination and animations behave.
EOF
}

INPUT=""
OUTPUT=""
CHROME=""
WAIT_MS=10000

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -o|--output)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
      OUTPUT="$2"; shift 2 ;;
    --chrome)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
      CHROME="$2"; shift 2 ;;
    --wait-ms)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 1; }
      WAIT_MS="$2"; shift 2 ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    *)
      if [[ -z "$INPUT" ]]; then
        INPUT="$1"
      else
        echo "Unexpected extra argument: $1" >&2; exit 1
      fi
      shift ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  usage >&2; exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "Input file not found: $INPUT" >&2; exit 1
fi

# Resolve input to an absolute path so file:// URLs work regardless of cwd.
INPUT_ABS="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="${INPUT_ABS%.html}.pdf"
  # If input doesn't end in .html, just append .pdf.
  if [[ "$OUTPUT" == "$INPUT_ABS" ]]; then
    OUTPUT="${INPUT_ABS}.pdf"
  fi
fi

# Auto-detect Chrome if not supplied.
if [[ -z "$CHROME" ]]; then
  for candidate in chromium chromium-browser google-chrome google-chrome-stable chrome; do
    if command -v "$candidate" >/dev/null 2>&1; then
      CHROME="$(command -v "$candidate")"
      break
    fi
  done
fi

if [[ -z "$CHROME" ]] || [[ ! -x "$CHROME" ]]; then
  cat >&2 <<EOF
Could not find chromium or chrome. Install one of the following, or pass
--chrome <path> explicitly:

  - chromium / chromium-browser (Debian/Ubuntu: apt install chromium)
  - google-chrome / google-chrome-stable
EOF
  exit 1
fi

echo "Chrome:  $CHROME"
echo "Input:   $INPUT_ABS"
echo "Output:  $OUTPUT"
echo "Wait:    ${WAIT_MS}ms for fonts/images/JS to settle"

# Use a private user-data-dir so we don't step on the user's Chrome profile
# (and so the run is reproducible — no stored state).
TMP_PROFILE="$(mktemp -d -t slides-export-XXXXXX)"
trap 'rm -rf "$TMP_PROFILE"' EXIT

# --headless=new : modern headless mode, better print fidelity.
# --virtual-time-budget : advance JS time until N ms pass (fires timers,
#                         loads fonts/images), then freeze — deterministic.
# --run-all-compositor-stages-before-draw : let layout/paint settle.
# --hide-scrollbars : irrelevant for print but keeps snapshots clean.
# --no-pdf-header-footer : drop Chrome's default URL/page-number header.
# --disable-pdf-tagging : smaller file, we don't need accessibility tags here.
# --no-sandbox : needed in many container/CI environments.
"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --hide-scrollbars \
  --no-pdf-header-footer \
  --disable-pdf-tagging \
  --virtual-time-budget="$WAIT_MS" \
  --run-all-compositor-stages-before-draw \
  --user-data-dir="$TMP_PROFILE" \
  --print-to-pdf="$OUTPUT" \
  "file://$INPUT_ABS"

if [[ ! -s "$OUTPUT" ]]; then
  echo "Chrome ran but produced an empty or missing PDF at $OUTPUT" >&2
  exit 1
fi

BYTES=$(wc -c <"$OUTPUT")
echo "✓ PDF written: $OUTPUT (${BYTES} bytes)"
