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
