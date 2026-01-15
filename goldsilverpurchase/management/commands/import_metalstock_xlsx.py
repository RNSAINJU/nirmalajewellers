import openpyxl
from django.core.management.base import BaseCommand
from goldsilverpurchase.models import MetalStock, MetalStockType, MetalStockMovement
from decimal import Decimal
from django.utils.dateparse import parse_date

class Command(BaseCommand):
    help = 'Import MetalStock and their movements from an XLSX file exported by export_metalstock_xlsx.'

    def add_arguments(self, parser):
        parser.add_argument('xlsxfile', type=str, help='Path to the XLSX file to import')

    def handle(self, *args, **options):
        xlsxfile = options['xlsxfile']
        wb = openpyxl.load_workbook(xlsxfile)
        ws = wb.active
        stocks = {}
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        for row in rows:
            stock_id, metal_type, stock_type_name, purity, quantity, unit_cost, rate_unit, total_cost, location, remarks, \
            movement_id, movement_type, movement_qty, movement_rate, reference_type, reference_id, notes, movement_date, created_at = row
            if stock_id not in stocks:
                stock_type = MetalStockType.objects.filter(name=stock_type_name).first()
                stock, _ = MetalStock.objects.get_or_create(
                    id=stock_id,
                    defaults={
                        'metal_type': metal_type,
                        'stock_type': stock_type,
                        'purity': purity,
                        'quantity': Decimal(quantity or 0),
                        'unit_cost': Decimal(unit_cost or 0),
                        'rate_unit': rate_unit,
                        'total_cost': Decimal(total_cost or 0),
                        'location': location,
                        'remarks': remarks,
                    }
                )
                stocks[stock_id] = stock
            else:
                stock = stocks[stock_id]
            # Import movement if present
            if movement_id:
                MetalStockMovement.objects.get_or_create(
                    id=movement_id,
                    defaults={
                        'metal_stock': stock,
                        'movement_type': movement_type,
                        'quantity': Decimal(movement_qty or 0),
                        'rate': Decimal(movement_rate or 0),
                        'reference_type': reference_type,
                        'reference_id': reference_id,
                        'notes': notes,
                        'movement_date': parse_date(str(movement_date)) if movement_date else None,
                    }
                )
        self.stdout.write(self.style.SUCCESS('Import completed.'))
