# Agent Skills - Development Commands

# Show available commands
default:
    @just --list

# Validate skill structure
validate:
    @echo "Validating skill structure..."
    @test -d skills || (echo "Missing skills/ directory" && exit 1)
    @test -n "$(find skills -mindepth 2 -maxdepth 2 -type d)" || (echo "No skill directories found" && exit 1)
    @missing="$(find skills -mindepth 2 -maxdepth 2 -type d ! -exec test -f '{}/SKILL.md' ';' -print)"; \
      test -z "${missing}" || (echo "Missing SKILL.md in:" && printf '%s\n' "${missing}" && exit 1)
    @stray="$(find skills -mindepth 2 -maxdepth 2 -name SKILL.md; find skills -mindepth 1 -maxdepth 1 -type f)"; \
      test -z "${stray}" || (echo "Skills must live in a group directory, not at the top level:" && printf '%s\n' "${stray}" && exit 1)
    @bad_frontmatter="$(find skills -name SKILL.md -exec sh -c 'for file do grep -q "^---$" "$file" && grep -q "^description:" "$file" || echo "$file"; done' sh {} +)"; \
      test -z "${bad_frontmatter}" || (echo "Invalid or incomplete frontmatter:" && printf '%s\n' "${bad_frontmatter}" && exit 1)
    @just _check-groupings
    @just _check-requires
    @legacy="$(rg -n '/plugin|/cata-helpers:|\.claude-plugin|plugins/|cata-' README.md AGENTS.md skills --glob '!.claude/settings.local.json' || true)"; \
      test -z "${legacy}" || (echo "Legacy references found:" && printf '%s\n' "${legacy}" && exit 1)
    @echo "✓ Found $(find skills -mindepth 2 -maxdepth 2 -type d | wc -l | tr -d ' ') skills in $(find skills -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') groups"
    @echo "✓ Every skill directory has SKILL.md"
    @echo "✓ Frontmatter sanity checks passed"
    @echo "✓ Directory layout matches skills.sh.json groupings"
    @echo "✓ Every declared dependency names a skill that exists"
    @echo "✓ No plugin-era references in tracked skill/docs files"
    @echo "\n✓ Skill validation passed!"

# Every skill's directory must match its skills.sh.json grouping, in both directions
_check-groupings:
    #!/usr/bin/env bash
    set -euo pipefail
    fail=0
    listed="$(jq -r '.groupings[] | .title as $t | .skills[] | "\($t | ascii_downcase)/\(.)"' skills.sh.json | sort)"
    onDisk="$(find skills -mindepth 2 -maxdepth 2 -type d | sed 's|^skills/||' | sort)"
    if ! diff <(echo "$listed") <(echo "$onDisk") >/dev/null; then
      echo "skills.sh.json and the skills/ tree disagree:"
      diff <(echo "$listed") <(echo "$onDisk") | sed 's/^</  only in skills.sh.json: /; s/^>/  only on disk: /' || true
      fail=1
    fi
    for skill in $(find skills -mindepth 2 -maxdepth 2 -type d); do
      group="$(basename "$(dirname "$skill")")"
      declared="$(sed -n '/^metadata:/,/^[a-z]/p' "$skill/SKILL.md" | sed -n 's/^  group: *//p' | head -1)"
      if [ -n "$declared" ] && [ "$declared" != "$group" ]; then
        echo "  $skill declares group '$declared' but lives in '$group'"
        fail=1
      fi
    done
    exit $fail

# Every metadata.requires entry must name a skill that exists in this repo
_check-requires:
    #!/usr/bin/env bash
    set -euo pipefail
    fail=0
    known="$(find skills -mindepth 2 -maxdepth 2 -type d -exec basename {} \; | sort -u)"
    for file in $(find skills -name SKILL.md); do
      deps="$(sed -n 's/^  \(requires\|optional\): *\[\(.*\)\]/\2/p' "$file" | tr ',' '\n' | tr -d ' ')"
      for dep in $deps; do
        echo "$known" | grep -qx "$dep" || { echo "  $file requires unknown skill '$dep'"; fail=1; }
      done
    done
    exit $fail

# Show skill structure
structure:
    @tree -I '.git|.claude' skills || find skills -type f | sort
    @printf '\nREADME.md\nAGENTS.md\nskills.sh.json\nJustfile\n'

# Show local testing instructions
test:
    @echo "This repository is a source repo for agent skills."
    @echo ""
    @echo "  1. Install them into a checkout to try them:"
    @echo "     npx skills add . --list"
    @echo "     npx skills add . --skill <name>"
    @echo ""
    @echo "  2. Your harness decides where skills live; the CLI handles the placement."
    @echo ""
    @echo "  3. Run just validate before committing changes here."
