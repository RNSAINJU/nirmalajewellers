from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE finance_loan
                ADD COLUMN IF NOT EXISTS final_interest_paid numeric(14, 2);
            ALTER TABLE finance_loan
                ADD COLUMN IF NOT EXISTS settlement_months smallint;
            ALTER TABLE finance_cashbank
                ADD COLUMN IF NOT EXISTS investment_date date;
            ALTER TABLE finance_cashbank
                ADD COLUMN IF NOT EXISTS investment_amount numeric(15, 2);
            ALTER TABLE finance_cashbank
                ADD COLUMN IF NOT EXISTS current_amount numeric(15, 2);
            """,
            reverse_sql="""
            ALTER TABLE finance_cashbank DROP COLUMN IF EXISTS current_amount;
            ALTER TABLE finance_cashbank DROP COLUMN IF EXISTS investment_amount;
            ALTER TABLE finance_cashbank DROP COLUMN IF EXISTS investment_date;
            ALTER TABLE finance_loan DROP COLUMN IF EXISTS settlement_months;
            ALTER TABLE finance_loan DROP COLUMN IF EXISTS final_interest_paid;
            """,
        ),
    ]
