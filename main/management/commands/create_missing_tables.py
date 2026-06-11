"""Create database tables that are missing from older live dumps."""

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create any model tables that do not yet exist in the database.'

    def handle(self, *args, **options):
        existing = set(connection.introspection.table_names())
        created = []

        for model in apps.get_models():
            if model._meta.app_label in {'admin', 'auth', 'contenttypes', 'sessions'}:
                continue

            table = model._meta.db_table
            if table in existing:
                continue

            with connection.schema_editor() as editor:
                editor.create_model(model)
            existing.add(table)
            created.append(f'{model._meta.label} ({table})')

        if created:
            self.stdout.write(self.style.SUCCESS('Created tables:'))
            for name in created:
                self.stdout.write(f'  - {name}')
        else:
            self.stdout.write(self.style.SUCCESS('All tables already exist.'))
