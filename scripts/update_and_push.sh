#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/update_and_push.sh "Commit message"
# Stages all changes, commits, pulls (rebase), and pushes.

MSG="${1:-Update}"
BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo main)"

git add -A
git commit -m "$MSG" || echo "No changes to commit."

# Rebase pull to keep history linear
git pull --rebase origin "$BRANCH" || true

git push origin "$BRANCH"
echo "Pushed updates to branch '$BRANCH'."
