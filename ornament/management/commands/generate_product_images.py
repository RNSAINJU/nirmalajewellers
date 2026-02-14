"""
Django management command to generate AI images for products without images.

Usage:
    python manage.py generate_product_images --method replicate [--limit 10]
    python manage.py generate_product_images --method stability [--limit 10]
    
Environment variables required:
    - REPLICATE_API_TOKEN (for replicate method)
    - STABILITY_API_KEY (for stability method)
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from ornament.models import Ornament
from common.generate_product_images import generate_images_for_products


class Command(BaseCommand):
    help = 'Generate AI images for products without images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            choices=['replicate', 'stability'],
            default='replicate',
            help='Image generation method: replicate (free credits) or stability (paid)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of products to process',
        )
        parser.add_argument(
            '--category',
            type=int,
            default=None,
            help='Process only products from specific category ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing',
        )

    def handle(self, *args, **options):
        method = options['method']
        limit = options['limit']
        category_id = options['category']
        dry_run = options['dry_run']

        # Build queryset
        queryset = Ornament.objects.filter(
            ornament_type='stock',
            status='active'
        )

        if category_id:
            queryset = queryset.filter(maincategory_id=category_id)

        # Filter products without images
        products_without_images = queryset.filter(
            Q(image__isnull=True) | Q(image='')
        )

        if limit:
            products_without_images = products_without_images[:limit]

        count = products_without_images.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No products without images found.'))
            return

        self.stdout.write(
            self.style.WARNING(
                f'Found {count} products without images.\n'
                f'Method: {method}\n'
            )
        )

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run - showing products that would be processed:'))
            for product in products_without_images[:10]:
                self.stdout.write(f'  - {product.id}: {product.ornament_name}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
            return

        # Confirm before proceeding
        confirm = input(
            f'\nThis will generate images for {count} products using {method}.\n'
            f'Continue? (yes/no): '
        ).strip().lower()

        if confirm != 'yes':
            self.stdout.write(self.style.ERROR('Operation cancelled.'))
            return

        # Generate images
        self.stdout.write('\nStarting image generation...\n')
        
        try:
            results = generate_images_for_products(
                products_without_images,
                method=method
            )

            # Print results
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('Image Generation Complete!'))
            self.stdout.write('='*60)
            self.stdout.write(f'Total processed: {results["total"]}')
            self.stdout.write(self.style.SUCCESS(f'✓ Successful: {results["success"]}'))
            self.stdout.write(self.style.ERROR(f'✗ Failed: {results["failed"]}'))

            if results['errors']:
                self.stdout.write('\nErrors:')
                for error in results['errors'][:10]:
                    self.stdout.write(f'  - {error}')
                if len(results['errors']) > 10:
                    self.stdout.write(f'  ... and {len(results["errors"]) - 10} more')

        except Exception as e:
            raise CommandError(f'Error during image generation: {str(e)}')
