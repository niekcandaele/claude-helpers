# Claude Code Helpers - Development Commands

# Show available commands
default:
    @just --list

# Validate plugin structure
validate:
    @echo "Validating plugin structure..."
    @echo "\n--- cata-helpers plugin ---"
    @test -f plugins/cata-helpers/.claude-plugin/plugin.json || (echo "Missing cata-helpers plugin.json" && exit 1)
    @echo "✓ Found plugin.json"
    @jq empty plugins/cata-helpers/.claude-plugin/plugin.json && echo "✓ plugin.json is valid JSON"
    @echo "✓ Found $(find plugins/cata-helpers/commands -name '*.md' | wc -l | tr -d ' ') commands"
    @echo "✓ Found $(find plugins/cata-helpers/agents -name '*.md' | wc -l | tr -d ' ') agents"
    @echo "\n--- kubecon plugin ---"
    @test -f plugins/kubecon/.claude-plugin/plugin.json || (echo "Missing kubecon plugin.json" && exit 1)
    @echo "✓ Found plugin.json"
    @jq empty plugins/kubecon/.claude-plugin/plugin.json && echo "✓ plugin.json is valid JSON"
    @echo "✓ Found $(find plugins/kubecon/skills -name 'SKILL.md' | wc -l | tr -d ' ') skills"
    @echo "\n--- player-coach plugin ---"
    @test -f plugins/player-coach/.claude-plugin/plugin.json || (echo "Missing player-coach plugin.json" && exit 1)
    @echo "✓ Found plugin.json"
    @jq empty plugins/player-coach/.claude-plugin/plugin.json && echo "✓ plugin.json is valid JSON"
    @echo "✓ Found $(find plugins/player-coach/commands -name '*.md' | wc -l | tr -d ' ') commands"
    @echo "✓ Found $(find plugins/player-coach/agents -name '*.md' | wc -l | tr -d ' ') agents"
    @echo "\n--- marketplace ---"
    @test -f .claude-plugin/marketplace.json || (echo "Missing marketplace.json" && exit 1)
    @echo "✓ Found marketplace.json"
    @jq empty .claude-plugin/marketplace.json && echo "✓ marketplace.json is valid JSON"
    @echo "\n✓ Plugin validation passed!"

# Show plugin structure
structure:
    @tree -I '.git' . || find . -type f \( -name "*.md" -o -name "*.json" \) | grep -v ".git" | sort

# Show local testing instructions
test:
    @echo "To test this plugin locally:"
    @echo ""
    @echo "  1. Start Claude Code with the plugin directory:"
    @echo "     claude --plugin-dir $(pwd)"
    @echo ""
    @echo "  2. Or add the marketplace locally:"
    @echo "     /plugin marketplace add $(pwd)"
    @echo "     /plugin install cata-helpers"
    @echo "     /plugin install kubecon"
