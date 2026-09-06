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
    @echo "The skills themselves are prompts, not code: their correctness"
    @echo "harness is 'just validate'. Run that before committing."
    @echo ""
    @echo "The evaluation tooling is code, and 'just eval-test' checks it."
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

# --- Skill evaluations -------------------------------------------------

# List every evaluation case: id, skill, kind, harnesses
eval-list:
    @python3 scripts/evals/cases.py --list

# Validate every case and its generated config, without calling a model
eval-check:
    @python3 scripts/evals/cases.py --validate
    @python3 scripts/evals/prepare.py --check-config

# Evaluate one case and save the report: HARNESS is codex, claude-code, or both
eval-run CASE HARNESS="codex":
    @python3 scripts/evals/run.py --case {{ CASE }} --harness {{ HARNESS }}

# Open the saved results in the Promptfoo viewer (makes no model calls)
eval-view:
    @PROMPTFOO_CONFIG_DIR="$(python3 scripts/evals/prepare.py --promptfoo-home)" npx --no-install promptfoo view

# Model-free checks for the evaluation tooling (provider doubles)
eval-test:
    @python3 scripts/evals/test_evals.py

# One cheap live probe per harness: record the effective skill catalog and instructions
eval-probe HARNESS="codex":
    @python3 scripts/evals/run.py --probe --harness {{ HARNESS }}
