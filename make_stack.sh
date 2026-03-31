#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"

git fetch origin
git checkout main
git pull --ff-only origin main

make_commit() {
  local branch="$1"
  local msg="$2"

  git checkout -b "$branch"
  printf '%s\n' "$msg" >> experiment.txt
  git add experiment.txt
  git commit -m "$msg"
  git push -u origin "$branch"
}

make_commit pr1 "pr1"
gh pr create \
  --repo "$REPO" \
  --base main \
  --head pr1 \
  --title "pr1" \
  --body "Stack experiment pr1"

make_commit pr2 "pr2"
gh pr create \
  --repo "$REPO" \
  --base pr1 \
  --head pr2 \
  --title "pr2" \
  --body "Stack experiment pr2"

make_commit pr3 "pr3"
gh pr create \
  --repo "$REPO" \
  --base pr2 \
  --head pr3 \
  --title "pr3" \
  --body "Stack experiment pr3"

make_commit pr4 "pr4"
gh pr create \
  --repo "$REPO" \
  --base pr3 \
  --head pr4 \
  --title "pr4" \
  --body "Stack experiment pr4"

echo "Done."