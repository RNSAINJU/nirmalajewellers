#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   GITHUB_TOKEN=<your_pat> ./scripts/setup_git_pat.sh <github_username> [repo_name]
# Example:
#   GITHUB_TOKEN=ghp_XXXX ./scripts/setup_git_pat.sh youruser nirmalajewellers
#
# Creates a stored credential entry and sets remote to HTTPS.

GH_USER="${1:?GitHub username required}"
REPO="${2:-nirmalajewellers}"
TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "Error: GITHUB_TOKEN env var not set."
  echo "Create a PAT at https://github.com/settings/tokens with 'repo' scope and export it:"
  echo "  export GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  exit 1
fi

# Set credential helper to store (plaintext in ~/.git-credentials). Alternatively use 'cache'.
git config --global credential.helper store

# Write credentials (username + token)
CRED_FILE="${HOME}/.git-credentials"
LINE="https://${GH_USER}:${TOKEN}@github.com"
if ! grep -qF "$LINE" "$CRED_FILE" 2>/dev/null; then
  echo "$LINE" >> "$CRED_FILE"
fi

# Set remote to HTTPS
REMOTE_URL="https://github.com/${GH_USER}/${REPO}.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

CURRENT_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo main)"
git push -u origin "$CURRENT_BRANCH"
echo "Done: pushed branch '$CURRENT_BRANCH' to ${REMOTE_URL}"

# Note:
# - Using 'store' saves credentials in plaintext. For better security, use:
#     git config --global credential.helper cache
#   which keeps credentials in memory for a limited time.
