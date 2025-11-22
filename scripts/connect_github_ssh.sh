#!/usr/bin/env bash
set -euo pipefail

# Usage:
  ./scripts/connect_github_ssh.sh <rnsainju> [nirmalajewellers]
  
# Example:
#   ./scripts/connect_github_ssh.sh rnsainju nirmalajewellers
#
# - Generates SSH key if missing
# - Adds it to ssh-agent
# - Adds key to GitHub via gh (if available), otherwise prints the key
# - Creates the GitHub repo via gh (if available)
# - Sets remote to SSH and pushes current branch

GH_USER="${1:?GitHub username required}"
REPO="${2:-nirmalajewellers}"

# Ensure git is installed
command -v git >/dev/null 2>&1 || { sudo apt update && sudo apt install -y git; }

# Start ssh-agent if not running
if ! pgrep -u "$USER" ssh-agent >/dev/null 2>&1; then
  eval "$(ssh-agent -s)"
fi

KEY="${HOME}/.ssh/id_ed25519"
if [ ! -f "$KEY" ]; then
  ssh-keygen -t ed25519 -C "${GH_USER}@github" -f "$KEY" -N ""
fi
ssh-add "$KEY"

PUB_KEY="${KEY}.pub"

# If gh is available, add SSH key and create repo if missing
if command -v gh >/dev/null 2>&1; then
  gh auth status || gh auth login
  # Add SSH key (ignore if already added)
  gh ssh-key add "$PUB_KEY" -t "${REPO}-key" || true

  # Create repo if it doesn't exist
  if ! gh repo view "${GH_USER}/${REPO}" >/dev/null 2>&1; then
    gh repo create "${GH_USER}/${REPO}" --private --source=. --push || true
  fi
else
  echo "GitHub CLI (gh) not found. Install: sudo apt install -y gh && gh auth login"
  echo "Add this public key at https://github.com/settings/ssh/new:"
  cat "$PUB_KEY"
  echo "Title: ${REPO}-key"
fi

# Set remote to SSH
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "git@github.com:${GH_USER}/${REPO}.git"
else
  git remote add origin "git@github.com:${GH_USER}/${REPO}.git"
fi

# Ensure branch and initial commit
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  git add .
  git commit -m "Initial commit"
fi
git branch -M "$DEFAULT_BRANCH"

# Push
CURRENT_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo "$DEFAULT_BRANCH")"
git push -u origin "$CURRENT_BRANCH"
echo "Connected via SSH and pushed branch '$CURRENT_BRANCH' to git@github.com:${GH_USER}/${REPO}.git"
