from django.db import migrations


class PostgreSQLOnlyRunSQL(migrations.RunSQL):
    """Run raw SQL only on PostgreSQL (skip on SQLite test databases)."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != 'postgresql':
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor != 'postgresql':
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)
