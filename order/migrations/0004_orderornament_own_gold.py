from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_sync_live_schema_columns'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE order_orderornament
                ADD COLUMN IF NOT EXISTS own_gold numeric(10, 3) NOT NULL DEFAULT 0;
            """,
            reverse_sql="""
            ALTER TABLE order_orderornament DROP COLUMN IF EXISTS own_gold;
            """,
        ),
    ]
