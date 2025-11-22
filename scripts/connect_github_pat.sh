#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   GITHUB_TOKEN=<your_pat> ./scripts/connect_github_pat.sh <github_username> [repo_name]
# Example:
  GITHUB_TOKEN=ghp_XXXX ./scripts/connect_github_pat.sh rnsainju nirmalajewellers

# - Configures credential helper
# - Sets remote to HTTPS
# - Optionally creates repo via gh (if available)
# - Pushes current branch

GH_USER="${1:?GitHub username required}"
REPO="${2:-nirmalajewellers}"
TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "Error: GITHUB_TOKEN not set. Create a PAT with 'repo' scope and export it:"
  echo "  export GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  exit 1
fi

# Ensure git and (optionally) gh
command -v git >/dev/null 2>&1 || { sudo apt update && sudo apt install -y git; }
if command -v gh >/dev/null 2>&1; then
  gh auth status || gh auth login
  if ! gh repo view "${GH_USER}/${REPO}" >/dev/null 2>&1; then
    gh repo create "${GH_USER}/${REPO}" --private --source=. --push || true
  fi
fi

# Safer: cache creds in memory (avoid plaintext store)
git config --global credential.helper cache
git config --global credential.username "$GH_USER"

REMOTE_URL="https://github.com/${GH_USER}/${REPO}.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

# Initial commit if needed
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  git add .
  git commit -m "Initial commit"
fi
git branch -M "$DEFAULT_BRANCH"

# Push (Git will prompt: use username rnsainju and paste PAT as password)
CURRENT_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo "$DEFAULT_BRANCH")"
echo "When prompted for password, paste your PAT (not your account password)."
git push -u origin "$CURRENT_BRANCH"
echo "Connected via HTTPS and pushed branch '$CURRENT_BRANCH' to ${REMOTE_URL}"
