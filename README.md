## Local development (no PostgreSQL required)

```bash
pip install -r requirements.txt
./scripts/run_local.sh
```

This uses SQLite (`db.sqlite3`), creates an `admin` user (`admin` / `admin123`), and starts the server at http://127.0.0.1:8000.

Manual alternative:

```bash
python manage.py migrate --settings=mysite.settings_local
python manage.py runserver --settings=mysite.settings_local
```

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
