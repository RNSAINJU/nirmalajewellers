## Local development

```bash
pip install -r requirements.txt
./scripts/run_local.sh
```

With `.env` configured for PostgreSQL (see `.env.example`), local dev uses your imported dump.  
Without `DATABASE_*` vars, it falls back to SQLite.

### Import a database dump

```bash
# PostgreSQL custom format (.dump)
./scripts/import_db_dump.sh /path/to/backup.dump

# Plain SQL
./scripts/import_db_dump.sh /path/to/backup.sql

# Django JSON fixture
./scripts/import_db_dump.sh /path/to/full_db_dump.json
```

Then start the server:

```bash
./scripts/run_local.sh
```

Default local URL: http://127.0.0.1:8000

## Production setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit with your PostgreSQL and Cloudinary values
python manage.py migrate
python manage.py runserver
```

## Tests

Tests use an in-memory SQLite database (no PostgreSQL required):

```bash
python manage.py test --settings=mysite.settings_test
```

## Data import order

First import purchase and customer purchase, then order, ornaments, order_payments, and order_ornaments.
