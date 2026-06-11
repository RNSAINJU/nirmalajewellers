#!/usr/bin/env bash
# Import a database dump into local PostgreSQL.
# Usage: ./scripts/import_db_dump.sh /path/to/dump.file
set -euo pipefail

DUMP_FILE="${1:-}"
if [[ -z "$DUMP_FILE" || ! -f "$DUMP_FILE" ]]; then
  echo "Usage: $0 /path/to/dump.{dump,sql,json}"
  exit 1
fi

DB_NAME="${DATABASE_NAME:-nirmalajewellers_db}"
DB_USER="${DATABASE_USER:-nirmalajewellers_user}"
DB_PASSWORD="${DATABASE_PASSWORD:-probook}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"

export PGPASSWORD="$DB_PASSWORD"

echo "=== Dropping and recreating database: $DB_NAME ==="
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true
sudo -u postgres dropdb --if-exists "$DB_NAME"
sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"

EXT="${DUMP_FILE##*.}"
case "$EXT" in
  dump|backup)
    echo "=== Restoring PostgreSQL custom dump ==="
    pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
      --no-owner --no-privileges "$DUMP_FILE"
    SYNC_SCHEMA=1
    ;;
  sql)
    echo "=== Restoring plain SQL dump ==="
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$DUMP_FILE"
    SYNC_SCHEMA=1
    ;;
  json)
    echo "=== Loading Django JSON fixture ==="
    export PATH="${HOME}/.local/bin:${PATH}"
    cd "$(dirname "$0")/.."
    python3 manage.py migrate --settings=mysite.settings_local --noinput
    python3 manage.py create_missing_tables --settings=mysite.settings_local
    python3 manage.py loaddata "$DUMP_FILE" --settings=mysite.settings_local
    ;;
  *)
    echo "Unsupported format: .$EXT (use .dump, .sql, or .json)"
    exit 1
    ;;
esac

if [[ "${SYNC_SCHEMA:-}" == "1" ]]; then
  echo "=== Syncing schema for tables added after dump ==="
  export PATH="${HOME}/.local/bin:${PATH}"
  cd "$(dirname "$0")/.."
  python3 manage.py migrate --settings=mysite.settings_local --noinput
  python3 manage.py create_missing_tables --settings=mysite.settings_local
fi

echo "=== Import complete ==="
