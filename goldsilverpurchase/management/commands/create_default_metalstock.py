from django.core.management.base import BaseCommand
from goldsilverpurchase.models import MetalStock, MetalStockType

class Command(BaseCommand):
    help = 'Auto-create default MetalStock for Gold and Silver with Raw and Refined types.'

    def handle(self, *args, **options):
        metals = ['gold', 'silver']
        stock_types = ['raw', 'refined']
        purities = ['24K', '22K']
        created = 0
        for metal in metals:
            for stype in stock_types:
                stock_type_obj, _ = MetalStockType.objects.get_or_create(name=stype)
                for purity in purities:
                    # Only create 22K for raw type
                    if stype == 'raw' or (stype == 'refined' and purity == '24K'):
                        obj, was_created = MetalStock.objects.get_or_create(
                            metal_type=metal,
                            stock_type=stock_type_obj,
                            purity=purity,
                            defaults={
                                'quantity': 0,
                                'unit_cost': 0,
                                'rate_unit': 'gram',
                            }
                        )
                        if was_created:
                            created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} default MetalStock records.'))
