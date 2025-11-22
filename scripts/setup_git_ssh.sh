#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/setup_git_ssh.sh <github_username> [repo_name]
# Example:
#   ./scripts/setup_git_ssh.sh youruser nirmalajewellers
#
# This will:
# - Generate an ed25519 SSH key if missing
# - Add it to the ssh-agent
# - Add the public key to GitHub via gh (if installed), otherwise print it
# - Switch your origin remote to SSH and push

GH_USER="${1:?GitHub username required}"
REPO="${2:-nirmalajewellers}"

# Ensure ssh-agent is running
if ! pgrep -u "$USER" ssh-agent >/dev/null 2>&1; then
  eval "$(ssh-agent -s)"
fi

KEY="${HOME}/.ssh/id_ed25519"
if [ ! -f "$KEY" ]; then
  ssh-keygen -t ed25519 -C "${GH_USER}@github" -f "$KEY" -N ""
fi

ssh-add "$KEY"

PUB_KEY="${KEY}.pub"
if command -v gh >/dev/null 2>&1; then
  gh auth status || gh auth login
  gh ssh-key add "$PUB_KEY" -t "${REPO}-key" || true
else
  echo "GitHub CLI (gh) not found. Install with: sudo apt install -y gh"
  echo "Copy this public key and add it at https://github.com/settings/ssh/new:"
  echo "-----BEGIN PUBLIC KEY-----"
  cat "$PUB_KEY"
  echo "-----END PUBLIC KEY-----"
  echo "Title: ${REPO}-key"
fi

# Set remote to SSH
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "git@github.com:${GH_USER}/${REPO}.git"
else
  git remote add origin "git@github.com:${GH_USER}/${REPO}.git"
fi

# Test GitHub SSH
ssh -T git@github.com || true

# Push
CURRENT_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo main)"
git push -u origin "$CURRENT_BRANCH"
echo "Done: pushed branch '$CURRENT_BRANCH' to git@github.com:${GH_USER}/${REPO}.git"
