#!/usr/bin/env bash
# export-pdf.sh — render a rich-page HTML file to PDF.
#
# Uses headless Chrome's native print-to-PDF. No Python or Node
# dependencies. The page's own @media print block (provided by
# assets/base.css) controls pagination, animation suppression, and
# nav-chrome hiding so this script stays minimal.
#
# Usage:
#   export-pdf.sh <page.html> [-o output.pdf] [--chrome <binary>] [--wait-ms N]

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: export-pdf.sh <page.html> [options]

Render a rich-page HTML file to PDF using headless Chrome. The page
prints with @media print rules from base.css applied (nav chrome
hidden, reveal animations forced visible, link URLs annotated).

Arguments:
  <page.html>            Path to the HTML file.

Options:
  -o, --output PATH      Output PDF path. Default: replace .html with .pdf.
  --chrome PATH          Chromium/Chrome binary to use. Default: auto-detect
                         in PATH. Looks for chromium, chromium-browser,
                         google-chrome, google-chrome-stable, chrome.
  --wait-ms N            Milliseconds to let JS, fonts, CDN libs, and
                         images settle before snapshotting. Default: 10000
                         (10s). Increase if charts/diagrams are missing
                         from the PDF — they may need more time to render.
  -h, --help             Show this help and exit.

Example:
  export-pdf.sh page.html -o report.pdf

Dependencies:
  - Chromium or Google Chrome installed on the system.
  - The HTML page should include the @media print rules from
    rich-page's assets/base.css so pagination behaves.
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

# Resolve input to absolute path so file:// URLs work regardless of cwd.
INPUT_ABS="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="${INPUT_ABS%.html}.pdf"
  if [[ "$OUTPUT" == "$INPUT_ABS" ]]; then
    OUTPUT="${INPUT_ABS}.pdf"
  fi
fi

# Auto-detect Chrome.
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
echo "Wait:    ${WAIT_MS}ms for fonts/CDN libs/images to settle"

# Private user-data-dir so we don't step on the user's Chrome profile.
TMP_PROFILE="$(mktemp -d -t rich-page-export-XXXXXX)"
trap 'rm -rf "$TMP_PROFILE"' EXIT

# --headless=new : modern headless mode, better print fidelity.
# --window-size=1280,1800 : tall viewport so long scrolling pages
#                            paginate cleanly. Adjust if page is wider/taller.
# --virtual-time-budget : advance JS time until N ms pass (fires timers,
#                         loads fonts/images from CDN), then freeze.
# --run-all-compositor-stages-before-draw : let layout/paint settle.
# --hide-scrollbars : keeps snapshots clean.
# --no-pdf-header-footer : drop Chrome's default URL/page-number header.
# --no-sandbox : needed in many container/CI environments.
"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --hide-scrollbars \
  --window-size=1280,1800 \
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
