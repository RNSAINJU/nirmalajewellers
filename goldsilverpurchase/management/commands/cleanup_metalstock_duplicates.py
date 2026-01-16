from django.core.management.base import BaseCommand
from goldsilverpurchase.models import MetalStock
from collections import defaultdict

class Command(BaseCommand):
    help = 'Remove duplicate MetalStock rows with same metal_type and stock_type, keeping only one.'

    def handle(self, *args, **options):
        dupes = defaultdict(list)
        for stock in MetalStock.objects.all():
            key = (stock.metal_type, stock.stock_type_id)
            dupes[key].append(stock)

        total_deleted = 0
        for key, stocks in dupes.items():
            if len(stocks) > 1:
                # Keep the first, delete the rest
                for s in stocks[1:]:
                    self.stdout.write(f"Deleting duplicate MetalStock: id={s.id}, metal_type={s.metal_type}, stock_type_id={s.stock_type_id}")
                    s.delete()
                    total_deleted += 1
        self.stdout.write(self.style.SUCCESS(f"Deleted {total_deleted} duplicate MetalStock rows."))
