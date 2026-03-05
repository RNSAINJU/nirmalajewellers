#!/bin/bash
# Quick deploy script — run this on the live server after pulling changes
set -e

PROJECT_DIR="/home/django_user/nirmalajewellers"
VENV="$PROJECT_DIR/venv/bin/activate"
SERVICE="nirmalajewellers"

echo "=== Pulling latest code ==="
cd "$PROJECT_DIR"
git pull origin main

echo "=== Installing any new packages ==="
source "$VENV"
pip install -r requirements.txt --quiet

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Restarting Gunicorn ==="
sudo systemctl restart "$SERVICE"
sudo systemctl status "$SERVICE" --no-pager -l

echo ""
echo "=== Done! Site is live with latest changes ==="
