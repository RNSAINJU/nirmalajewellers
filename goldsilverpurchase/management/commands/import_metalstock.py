import csv
from django.core.management.base import BaseCommand
from goldsilverpurchase.models import MetalStock, MetalStockType, MetalStockMovement
from django.utils.dateparse import parse_date
from decimal import Decimal

class Command(BaseCommand):
    help = 'Import MetalStock and their movements from a CSV file exported by export_metalstock.'

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str, help='Path to the CSV file to import')

    def handle(self, *args, **options):
        csvfile = options['csvfile']
        with open(csvfile, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            stocks = {}
            for row in reader:
                stock_id = row['StockID']
                if stock_id not in stocks:
                    stock_type = MetalStockType.objects.filter(name=row['StockType']).first()
                    stock, _ = MetalStock.objects.get_or_create(
                        id=stock_id,
                        defaults={
                            'metal_type': row['MetalType'],
                            'stock_type': stock_type,
                            'purity': row['Purity'],
                            'quantity': Decimal(row['Quantity'] or '0'),
                            'unit_cost': Decimal(row['UnitCost'] or '0'),
                            'rate_unit': row['RateUnit'],
                            'total_cost': Decimal(row['TotalCost'] or '0'),
                            'location': row['Location'],
                            'remarks': row['Remarks'],
                        }
                    )
                    stocks[stock_id] = stock
                else:
                    stock = stocks[stock_id]
                # Import movement if present
                if row['MovementID']:
                    MetalStockMovement.objects.get_or_create(
                        id=row['MovementID'],
                        defaults={
                            'metal_stock': stock,
                            'movement_type': row['MovementType'],
                            'quantity': Decimal(row['MovementQty'] or '0'),
                            'rate': Decimal(row['MovementRate'] or '0'),
                            'reference_type': row['ReferenceType'],
                            'reference_id': row['ReferenceID'],
                            'notes': row['Notes'],
                            'movement_date': parse_date(row['MovementDate']) if row['MovementDate'] else None,
                        }
                    )
        self.stdout.write(self.style.SUCCESS('Import completed.'))
