from common.migration_utils import PostgreSQLOnlyRunSQL
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goldsilverpurchase', '0002_initial'),
    ]

    operations = [
        PostgreSQLOnlyRunSQL(
            sql="""
            ALTER TABLE goldsilverpurchase_customerpurchase
                ADD COLUMN IF NOT EXISTS bill_no varchar(20);
            ALTER TABLE goldsilverpurchase_customerpurchase
                ADD COLUMN IF NOT EXISTS diamond_weight numeric(10, 3);
            ALTER TABLE goldsilverpurchase_customerpurchase
                ADD COLUMN IF NOT EXISTS diamond_rate numeric(12, 2);
            ALTER TABLE goldsilverpurchase_customerpurchase
                ADD COLUMN IF NOT EXISTS diamond_amount numeric(12, 2);
            ALTER TABLE goldsilverpurchase_customerpurchase
                ADD COLUMN IF NOT EXISTS total_amount numeric(12, 2);
            CREATE INDEX IF NOT EXISTS goldsilverpurchase_customerpurchase_bill_no_idx
                ON goldsilverpurchase_customerpurchase (bill_no);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS goldsilverpurchase_customerpurchase_bill_no_idx;
            ALTER TABLE goldsilverpurchase_customerpurchase DROP COLUMN IF EXISTS total_amount;
            ALTER TABLE goldsilverpurchase_customerpurchase DROP COLUMN IF EXISTS diamond_amount;
            ALTER TABLE goldsilverpurchase_customerpurchase DROP COLUMN IF EXISTS diamond_rate;
            ALTER TABLE goldsilverpurchase_customerpurchase DROP COLUMN IF EXISTS diamond_weight;
            ALTER TABLE goldsilverpurchase_customerpurchase DROP COLUMN IF EXISTS bill_no;
            """,
        ),
    ]
