from common.migration_utils import PostgreSQLOnlyRunSQL
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ornament', '0001_initial'),
    ]

    operations = [
        PostgreSQLOnlyRunSQL(
            sql="""
            ALTER TABLE ornament_kaligar_ornaments
                ADD COLUMN IF NOT EXISTS ornament_id bigint;
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'ornament_kaligar_ornaments_ornament_id_fk'
                ) THEN
                    ALTER TABLE ornament_kaligar_ornaments
                        ADD CONSTRAINT ornament_kaligar_ornaments_ornament_id_fk
                        FOREIGN KEY (ornament_id)
                        REFERENCES ornament_ornament(id)
                        ON DELETE SET NULL
                        DEFERRABLE INITIALLY DEFERRED;
                END IF;
            END $$;
            CREATE INDEX IF NOT EXISTS ornament_kaligar_ornaments_ornament_id_idx
                ON ornament_kaligar_ornaments (ornament_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS ornament_kaligar_ornaments_ornament_id_idx;
            ALTER TABLE ornament_kaligar_ornaments
                DROP CONSTRAINT IF EXISTS ornament_kaligar_ornaments_ornament_id_fk;
            ALTER TABLE ornament_kaligar_ornaments DROP COLUMN IF EXISTS ornament_id;
            """,
        ),
    ]
