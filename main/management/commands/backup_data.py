from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Backup or restore database data using dumpdata/loaddata."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["dump", "restore"], help="Action to perform.")
        parser.add_argument(
            "--backup-dir",
            default="backups",
            help="Directory for backup files (relative to BASE_DIR if not absolute).",
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Output file for dump (overrides auto filename).",
        )
        parser.add_argument(
            "--input",
            default=None,
            help="Input file for restore.",
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=2,
            help="JSON indent level for dumpdata.",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            default=[],
            help="App or model to exclude (repeatable).",
        )

    def handle(self, *args, **options):
        action = options["action"]
        backup_dir = options["backup_dir"]
        output = options["output"]
        input_path = options["input"]
        indent = options["indent"]
        exclude = options["exclude"]

        base_dir = Path(settings.BASE_DIR)
        backup_path = Path(backup_dir)
        if not backup_path.is_absolute():
            backup_path = base_dir / backup_path

        if action == "dump":
            backup_path.mkdir(parents=True, exist_ok=True)
            if output:
                output_path = Path(output)
                if not output_path.is_absolute():
                    output_path = backup_path / output_path
            else:
                timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
                output_path = backup_path / f"backup-{timestamp}.json"

            self.stdout.write(f"Creating backup: {output_path}")
            call_command(
                "dumpdata",
                output=str(output_path),
                indent=indent,
                exclude=exclude,
            )
            self.stdout.write(self.style.SUCCESS("Backup completed."))
            return

        if action == "restore":
            if not input_path:
                raise CommandError("--input is required for restore.")

            restore_path = Path(input_path)
            if not restore_path.is_absolute():
                restore_path = backup_path / restore_path

            if not restore_path.exists():
                raise CommandError(f"Backup file not found: {restore_path}")

            self.stdout.write(f"Restoring from: {restore_path}")
            call_command("loaddata", str(restore_path))
            self.stdout.write(self.style.SUCCESS("Restore completed."))
            return

        raise CommandError("Unknown action.")
