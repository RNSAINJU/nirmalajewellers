# nirmalajewellers

Django jewelry management system.

## Initialize local Git repo
1) Make sure you are in the project root (this README is here).
2) Run the init script:
   - chmod +x scripts/init_repo.sh
   - ./scripts/init_repo.sh

Optionally pass a remote and set your name/email:
- GIT_USER_NAME="Your Name" GIT_USER_EMAIL="you@example.com" ./scripts/init_repo.sh https://github.com/<username>/nirmalajewellers.git

## Create and push to GitHub (using GitHub CLI)
- sudo apt update && sudo apt install -y gh
- gh auth login
- gh repo create <username>/nirmalajewellers --source=. --private --push
# nirmalajewellers


## Fix: GitHub password auth error
GitHub no longer accepts username+password for Git pushes. Use one of:

1) SSH (recommended)
- Run:
  - chmod +x scripts/setup_git_ssh.sh
  - ./scripts/setup_git_ssh.sh <github_username> nirmalajewellers
- This generates an SSH key, adds it to your agent, registers it with GitHub, switches your remote to SSH, and pushes.

2) Personal Access Token (HTTPS)
- Create a PAT at https://github.com/settings/tokens with "repo" scope.
- Run:
  - export GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXX
  - chmod +x scripts/setup_git_pat.sh
  - ./scripts/setup_git_pat.sh <github_username> nirmalajewellers
- This stores your token for Git and pushes via HTTPS.

3) GitHub CLI (one-liner)
- sudo apt install -y gh
- gh auth login
- gh repo create <username>/nirmalajewellers --source=. --private --push
