import openpyxl
from openpyxl.utils import get_column_letter
from django.core.management.base import BaseCommand
from goldsilverpurchase.models import MetalStock, MetalStockMovement
from django.utils import timezone

class Command(BaseCommand):
    help = 'Export all MetalStock and their movements to an XLSX file.'

    def handle(self, *args, **options):
        filename = f"metalstock_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'MetalStock'
        headers = [
            'StockID', 'MetalType', 'StockType', 'Purity', 'Quantity', 'UnitCost', 'RateUnit', 'TotalCost', 'Location', 'Remarks',
            'MovementID', 'MovementType', 'MovementQty', 'MovementRate', 'ReferenceType', 'ReferenceID', 'Notes', 'MovementDate', 'CreatedAt'
        ]
        ws.append(headers)
        for stock in MetalStock.objects.all():
            base_row = [
                stock.id, stock.metal_type, stock.stock_type.name if stock.stock_type else '', stock.purity, stock.quantity, stock.unit_cost, stock.rate_unit, stock.total_cost, stock.location, stock.remarks
            ]
            movements = stock.movements.all()
            if movements.exists():
                for m in movements:
                    ws.append(base_row + [
                        m.id, m.movement_type, m.quantity, m.rate, m.reference_type, m.reference_id, m.notes, str(m.movement_date), str(m.created_at)
                    ])
            else:
                ws.append(base_row + ['','','','','','','','',''])
        # Auto-size columns
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[column].width = max_length + 2
        wb.save(filename)
        self.stdout.write(self.style.SUCCESS(f'Exported to {filename}'))
