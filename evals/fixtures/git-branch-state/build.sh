#!/usr/bin/env bash
# Build the git-branch-state fixture into $1.
#
# manifest.json is the single source of truth: it declares the commits, the
# overlays that make them, and the facts the assertion module grades against.
# Commit dates are pinned there, so two builds produce identical commit hashes.
#
# Prints the resulting HEAD sha on stdout. Needs bash, git and jq.
set -euo pipefail

DEST="${1:?usage: build.sh <destination-directory>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$HERE/manifest.json"
FILES="$HERE/files"

rm -rf "$DEST"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"

read -r AUTHOR_NAME AUTHOR_EMAIL <<<"$(jq -r '.author | "\(.name)\t\(.email)"' "$MANIFEST" | tr '\t' ' ')"

git -C "$DEST" init --quiet --initial-branch="$(jq -r .base_branch "$MANIFEST")"
git -C "$DEST" config user.name "$AUTHOR_NAME"
git -C "$DEST" config user.email "$AUTHOR_EMAIL"
git -C "$DEST" config commit.gpgsign false
git -C "$DEST" config tag.gpgsign false
git -C "$DEST" config gc.auto 0

# No host hook may fire inside a trial workspace.
mkdir -p "$DEST/.git/empty-hooks"
git -C "$DEST" config core.hooksPath "$DEST/.git/empty-hooks"

previous_branch="$(jq -r .base_branch "$MANIFEST")"
step_count="$(jq '.steps | length' "$MANIFEST")"

for i in $(seq 0 $((step_count - 1))); do
    branch="$(jq -r ".steps[$i].branch" "$MANIFEST")"
    subject="$(jq -r ".steps[$i].subject" "$MANIFEST")"
    date="$(jq -r ".steps[$i].date" "$MANIFEST")"
    overlay="$(jq -r ".steps[$i].overlay // empty" "$MANIFEST")"

    if [ "$branch" != "$previous_branch" ]; then
        git -C "$DEST" checkout --quiet -b "$branch"
        previous_branch="$branch"
    fi

    if [ -n "$overlay" ]; then
        cp -R "$FILES/$overlay/." "$DEST/"
    fi

    while IFS= read -r path; do
        [ -n "$path" ] || continue
        git -C "$DEST" rm --quiet "$path"
    done < <(jq -r ".steps[$i].delete[]?" "$MANIFEST")

    git -C "$DEST" add -A
    GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" \
        git -C "$DEST" commit --quiet --no-verify -m "$subject"
done

uncommitted_overlay="$(jq -r '.uncommitted.overlay // empty' "$MANIFEST")"
if [ -n "$uncommitted_overlay" ]; then
    cp -R "$FILES/$uncommitted_overlay/." "$DEST/"
fi

git -C "$DEST" rev-parse HEAD
