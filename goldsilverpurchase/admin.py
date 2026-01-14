from django.contrib import admin
from .models import GoldSilverPurchase, Party, MetalStock, MetalStockType, MetalStockMovement
from .forms import PurchaseForm, PartyForm

@admin.register(GoldSilverPurchase)
class GoldSilverPurchaseAdmin(admin.ModelAdmin):
    form = PurchaseForm
    
    list_display = ('bill_no', 'party', 'metal_type', 'purity', 'quantity', 'amount', 'bill_date')
    list_filter = ('metal_type', 'purity', 'party', 'bill_date')

    fields = (
        'bill_no',
        'bill_date',
        'party',    # <-- add here
        'particular',
        'metal_type',
        'purity',
        'quantity',
        'rate',
        'wages',
        'discount',
        'amount',
        'payment_mode'
    )

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    form = PartyForm

    list_display = ('party_name', 'panno')


@admin.register(MetalStockType)
class MetalStockTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class MetalStockMovementInline(admin.TabularInline):
    model = MetalStockMovement
    extra = 0
    fields = ('movement_type', 'quantity', 'reference_type', 'reference_id', 'notes', 'movement_date')
    readonly_fields = ('movement_date', 'created_at')


@admin.register(MetalStock)
class MetalStockAdmin(admin.ModelAdmin):
    list_display = ('metal_type', 'stock_type', 'purity', 'quantity', 'unit_cost', 'total_cost', 'location', 'last_updated')
    list_filter = ('metal_type', 'stock_type', 'purity', 'location')
    search_fields = ('location', 'remarks')
    readonly_fields = ('total_cost', 'created_at', 'last_updated')
    
    fieldsets = (
        ('Metal Information', {
            'fields': ('metal_type', 'stock_type', 'purity')
        }),
        ('Quantity & Cost', {
            'fields': ('quantity', 'rate_unit', 'unit_cost', 'total_cost')
        }),
        ('Storage', {
            'fields': ('location', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MetalStockMovementInline]


@admin.register(MetalStockMovement)
class MetalStockMovementAdmin(admin.ModelAdmin):
    list_display = ('metal_stock', 'movement_type', 'quantity', 'reference_type', 'reference_id', 'movement_date')
    list_filter = ('movement_type', 'metal_stock__metal_type', 'movement_date')
    search_fields = ('metal_stock__location', 'reference_id', 'notes')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Stock Movement', {
            'fields': ('metal_stock', 'movement_type', 'quantity')
        }),
        ('Reference', {
            'fields': ('reference_type', 'reference_id')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('movement_date', 'created_at'),
            'classes': ('collapse',)
        }),
    )