# Working in this repository

This is a source repo for reusable agent skills. Nothing here is application
code — the skills are prompts, and `just validate` is the only correctness
harness. Use the `writing-for-agents` skill when creating or editing one.

## Commands

```bash
just validate    # the gate — run before committing
just structure   # show the skills tree
just try --list  # install from this checkout to try the skills
```

`just validate` needs `python3` with `pyyaml`, plus `jq`. It also runs in CI on
every pull request.

## Adding a skill

Three things, and `just validate` fails if you miss any of them:

1. `skills/<group>/<name>/SKILL.md`, with non-empty string `name` and
   `description` frontmatter. The `name` must equal the directory name, and must
   be unique across all groups — installation flattens the group directories, so
   two skills sharing a name would overwrite each other for every consumer.
2. `metadata.group` in that frontmatter, matching the parent directory.
3. The skill listed under the matching grouping in `skills.sh.json`.

If the skill invokes other skills in this repo, declare them:

```yaml
metadata:
  group: quality
  requires: [reviewer, tester]   # hard — the skill breaks without these
  optional: [rich-page]          # used on some paths only
```

Every name in `requires` and `optional` must resolve to a real skill. Both accept
inline or block-list YAML.

## House rules

**Frontmatter must parse as YAML.** A skill whose frontmatter is malformed is
*silently skipped* on install — it does not error, it just isn't there. This has
shipped to users before. Watch for unquoted values containing `: `; use a `>-`
block scalar when a description needs one.

**Skills are harness-neutral in their prose.** They don't assume a specific
runtime's directory layout, tool names, or built-in agent types. Where a skill
genuinely needs a runtime capability, state the capability first and name a
specific harness only as an example binding. Frontmatter is exempt — those keys
are each harness's own interface.

**Don't pin models.** State a cost tier in prose instead. The orchestrator picks
the model, because only it knows how hard the task is.

**Attribution travels with the file.** Skills derived from elsewhere carry a
one-line credit at the bottom. Keep it — the README invites people to copy
individual files, and MIT requires the notice to go with them.

This repository is a source repo for skills only. Do not reintroduce plugin
packaging, marketplace metadata, installer scripts, or repo-specific
version-bump logic.
