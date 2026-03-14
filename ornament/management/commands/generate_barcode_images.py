from django.core.management.base import BaseCommand
from django.db.models import Q
from ornament.models import Ornament


class Command(BaseCommand):
    help = 'Generate barcode images for all ornaments that have barcodes but no images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerate barcode images for all ornaments (even if they already have images)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of ornaments to process',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of ornaments to process in each batch',
        )

    def handle(self, *args, **options):
        regenerate = options['regenerate']
        limit = options['limit']
        batch_size = options['batch_size']

        # First, ensure all ornaments have barcodes using bulk_update for speed
        ornaments_without_barcodes = Ornament.objects.filter(barcode__isnull=True)
        if ornaments_without_barcodes.exists():
            count = ornaments_without_barcodes.count()
            self.stdout.write(self.style.WARNING(f'Generating barcodes for {count} ornaments without barcodes...'))
            
            ornaments_list = list(ornaments_without_barcodes)
            for ornament in ornaments_list:
                ornament.barcode = f"ORN-{ornament.pk:010d}"
            
            # Use bulk_update for faster updates
            Ornament.objects.bulk_update(ornaments_list, ['barcode'], batch_size=batch_size)
            self.stdout.write(self.style.SUCCESS(f'✓ Generated barcodes for {count} ornaments'))

        if regenerate:
            # Regenerate for all ornaments with barcodes
            ornaments = Ornament.objects.filter(barcode__isnull=False)
            self.stdout.write(self.style.WARNING('Regenerating barcode images for ALL ornaments with barcodes...'))
        else:
            # Only generate for ornaments with barcodes but without barcode images
            ornaments = Ornament.objects.filter(barcode__isnull=False).filter(Q(barcode_image__isnull=True) | Q(barcode_image=''))
            self.stdout.write('Generating barcode images for ornaments without images...')

        if limit:
            ornaments = ornaments[:limit]

        total = ornaments.count()
        self.stdout.write(f'\nProcessing {total} ornaments...\n')
        
        count = 0
        errors = 0
        
        for i, ornament in enumerate(ornaments, 1):
            try:
                if not ornament.barcode:
                    self.stdout.write(self.style.WARNING(f'⊘ [{i}/{total}] Skipping {ornament.code}: No barcode'))
                    continue
                    
                self.stdout.write(f'[{i}/{total}] Generating barcode for {ornament.code} ({ornament.barcode})...')
                ornament.generate_barcode_image()
                ornament.save(update_fields=['barcode_image'])
                self.stdout.write(self.style.SUCCESS(f'  ✓ Success: {ornament.barcode_image}'))
                count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error for {ornament.code}: {e}'))
                errors += 1

        self.stdout.write(self.style.SUCCESS(f'\n✓ Completed! Generated {count} barcode images. Errors: {errors}'))



