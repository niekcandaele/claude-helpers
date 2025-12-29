# Claude Code Helpers - Development Commands

# Show available commands
default:
    @just --list

# Validate plugin structure
validate:
    @echo "Validating plugin structure..."
    @test -f .claude-plugin/plugin.json || (echo "Missing plugin.json" && exit 1)
    @echo "✓ Found plugin.json"
    @test -f .claude-plugin/marketplace.json || (echo "Missing marketplace.json" && exit 1)
    @echo "✓ Found marketplace.json"
    @jq empty .claude-plugin/plugin.json && echo "✓ plugin.json is valid JSON"
    @jq empty .claude-plugin/marketplace.json && echo "✓ marketplace.json is valid JSON"
    @echo "✓ Found $(find commands -name '*.md' | wc -l | tr -d ' ') commands"
    @echo "✓ Found $(find agents -name '*.md' | wc -l | tr -d ' ') agents"
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
