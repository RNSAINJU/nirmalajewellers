"""Add columns that exist in models but are missing from older live databases."""

from common.migration_utils import PostgreSQLOnlyRunSQL
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_initial'),
    ]

    operations = [
        PostgreSQLOnlyRunSQL(
            sql="""
            ALTER TABLE order_order
                ADD COLUMN IF NOT EXISTS taxable_amount numeric(15, 2) NOT NULL DEFAULT 0;
            ALTER TABLE order_sale
                ADD COLUMN IF NOT EXISTS is_deleted boolean NOT NULL DEFAULT false;
            ALTER TABLE order_sale
                ADD COLUMN IF NOT EXISTS deleted_at timestamp with time zone NULL;
            """,
            reverse_sql="""
            ALTER TABLE order_order DROP COLUMN IF EXISTS taxable_amount;
            ALTER TABLE order_sale DROP COLUMN IF EXISTS is_deleted;
            ALTER TABLE order_sale DROP COLUMN IF EXISTS deleted_at;
            """,
        ),
    ]
