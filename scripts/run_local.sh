#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export PATH="${HOME}/.local/bin:${PATH}"
SETTINGS="mysite.settings_local"

python3 manage.py migrate --settings="$SETTINGS" --noinput

if ! python3 manage.py shell --settings="$SETTINGS" -c "from django.contrib.auth.models import User; exit(0 if User.objects.filter(username='admin').exists() else 1)" 2>/dev/null; then
  DJANGO_SUPERUSER_PASSWORD=admin123 \
    python3 manage.py createsuperuser --settings="$SETTINGS" \
      --noinput --username admin --email admin@localhost
  echo "Created local admin user: admin / admin123"
fi

echo "Starting dev server at http://127.0.0.1:8000"
exec python3 manage.py runserver 0.0.0.0:8000 --settings="$SETTINGS"
