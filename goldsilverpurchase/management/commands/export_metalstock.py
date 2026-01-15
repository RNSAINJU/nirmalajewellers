import csv
from django.core.management.base import BaseCommand
from goldsilverpurchase.models import MetalStock, MetalStockMovement
from django.utils import timezone

class Command(BaseCommand):
    help = 'Export all MetalStock and their movements to a CSV file.'

    def handle(self, *args, **options):
        filename = f"metalstock_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'StockID', 'MetalType', 'StockType', 'Purity', 'Quantity', 'UnitCost', 'RateUnit', 'TotalCost', 'Location', 'Remarks',
                'MovementID', 'MovementType', 'MovementQty', 'MovementRate', 'ReferenceType', 'ReferenceID', 'Notes', 'MovementDate', 'CreatedAt'
            ])
            for stock in MetalStock.objects.all():
                base_row = [
                    stock.id, stock.metal_type, stock.stock_type.name if stock.stock_type else '', stock.purity, stock.quantity, stock.unit_cost, stock.rate_unit, stock.total_cost, stock.location, stock.remarks
                ]
                movements = stock.movements.all()
                if movements.exists():
                    for m in movements:
                        writer.writerow(base_row + [
                            m.id, m.movement_type, m.quantity, m.rate, m.reference_type, m.reference_id, m.notes, m.movement_date, m.created_at
                        ])
                else:
                    writer.writerow(base_row + ['','','','','','','','',''])
        self.stdout.write(self.style.SUCCESS(f'Exported to {filename}'))
