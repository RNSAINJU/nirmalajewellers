from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class MigrationSmokeTest(TestCase):
    """Ensure committed migrations apply cleanly on a fresh database."""

    def test_migrations_apply_without_error(self):
        out = StringIO()
        call_command('migrate', verbosity=0, stdout=out)
