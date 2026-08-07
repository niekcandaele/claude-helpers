# Agent Skills - Development Commands

# Show available commands
default:
    @just --list

# Validate the skills tree — layout, frontmatter, groupings, dependencies
validate:
    @python3 scripts/validate.py

# Show skill structure
structure:
    @tree -I '.git|.claude' skills || find skills -type f | sort
    @printf '\nREADME.md\nAGENTS.md\nCONTEXT.md\nNOTICE.md\nLICENSE\nskills.sh.json\nJustfile\n'

# Install these skills into the current directory to try them
try *ARGS:
    @npx -y skills@latest add . {{ ARGS }}

# Show local testing instructions
test:
    @echo "This repo has no test suite — the skills are prompts, not code."
    @echo "Its correctness harness is 'just validate'. Run that before committing."
    @echo ""
    @echo "To try the skills from this checkout, install them somewhere else:"
    @echo "    cd /tmp/scratch && npx skills add /home/catalysm/code/skills --list"
    @echo ""
    @echo "Or from this directory, into this directory:"
    @echo "    just try --list          # see what is on offer"
    @echo "    just try --skill verify  # install one"
    @echo ""
    @echo "Installed skills land where your harness looks for them; the CLI"
    @echo "picks the directory and prints the path it used."
