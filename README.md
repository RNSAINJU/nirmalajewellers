## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit with your values
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
