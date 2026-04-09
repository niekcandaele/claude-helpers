# Claude Code Skills - Development Commands

# Show available commands
default:
    @just --list

# Validate skill structure
validate:
    @echo "Validating skill structure..."
    @test -d skills || (echo "Missing skills/ directory" && exit 1)
    @test -n "$(find skills -mindepth 1 -maxdepth 1 -type d)" || (echo "No skill directories found" && exit 1)
    @missing="$(find skills -mindepth 1 -maxdepth 1 -type d ! -exec test -f '{}/SKILL.md' ';' -print)"; \
      test -z "${missing}" || (echo "Missing SKILL.md in:" && printf '%s\n' "${missing}" && exit 1)
    @bad_frontmatter="$(find skills -name SKILL.md -exec sh -c 'for file do grep -q "^---$" "$file" && grep -q "^description:" "$file" || echo "$file"; done' sh {} +)"; \
      test -z "${bad_frontmatter}" || (echo "Invalid or incomplete frontmatter:" && printf '%s\n' "${bad_frontmatter}" && exit 1)
    @legacy="$(rg -n '/plugin|/cata-helpers:|\.claude-plugin|plugins/|cata-' README.md CLAUDE.md skills --glob '!.claude/settings.local.json' || true)"; \
      test -z "${legacy}" || (echo "Legacy references found:" && printf '%s\n' "${legacy}" && exit 1)
    @echo "✓ Found $(find skills -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') skills"
    @echo "✓ Every skill directory has SKILL.md"
    @echo "✓ Frontmatter sanity checks passed"
    @echo "✓ No plugin-era references in tracked skill/docs files"
    @echo "\n✓ Skill validation passed!"

# Show skill structure
structure:
    @tree -I '.git|.claude' skills && printf '\nREADME.md\nCLAUDE.md\nJustfile\n' || (find skills -type f | sort && printf '\nREADME.md\nCLAUDE.md\nJustfile\n')

# Show local testing instructions
test:
    @echo "This repository is a source repo for skills."
    @echo ""
    @echo "  1. Sync or copy skills/* into a Claude skills directory:"
    @echo "     ~/.claude/skills/      or      .claude/skills/"
    @echo ""
    @echo "  2. Then start Claude Code in a repo where those skills should be available."
    @echo ""
    @echo "  3. Run just validate before committing changes here."
