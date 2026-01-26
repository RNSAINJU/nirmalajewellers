from django.contrib import admin
from .models import GoldSilverPurchase, Party, MetalStock, MetalStockType, MetalStockMovement, CustomerPurchase
from .forms import PurchaseForm, PartyForm, MetalStockForm

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


@admin.register(CustomerPurchase)
class CustomerPurchaseAdmin(admin.ModelAdmin):
    list_display = ('sn', 'customer_name', 'metal_type', 'ornament_name', 'weight', 'final_weight', 'refined_status', 'refined_weight', 'profit_weight', 'amount', 'profit', 'purchase_date')
    list_filter = ('metal_type', 'purchase_date', 'customer_name')
    search_fields = ('sn', 'customer_name', 'phone_no', 'location')
    readonly_fields = (
        'sn',
        'final_weight',
        'profit_weight',
        'amount',
        'profit',
        'created_at',
        'updated_at',
        'saved_calculation_summary',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sn', 'purchase_date', 'customer_name', 'phone_no', 'location')
        }),
        ('Ornament Details', {
            'fields': ('metal_type', 'ornament_name')
        }),
        ('Weight Information', {
            'fields': ('weight', 'percentage', 'final_weight', 'refined_status', 'refined_weight', 'profit_weight')
        }),
        ('Pricing', {
            'fields': ('rate', 'rate_unit', 'amount', 'profit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def saved_calculation_summary(self, obj):
        if not obj:
            return ""
        return (
            f"<b>Final Weight:</b> {obj.final_weight}<br>"
            f"<b>Amount:</b> {obj.amount}<br>"
            f"<b>Profit Weight:</b> {obj.profit_weight}<br>"
            f"<b>Profit/Loss:</b> {obj.profit}"
        )
    saved_calculation_summary.short_description = "Saved Calculation Summary"
    saved_calculation_summary.allow_tags = True


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
    readonly_fields = ('quantity', 'total_cost', 'created_at', 'last_updated')
    form = MetalStockForm

    fieldsets = (
        ('Metal Information', {
            'fields': ('metal_type', 'stock_type', 'purity')
        }),
        ('Quantity & Cost', {
            'fields': ('quantity', 'rate_unit', 'unit_cost', 'total_cost', 'add_quantity', 'movement_notes')
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

    def save_model(self, request, obj, form, change):
        # Always save MetalStock first to ensure PK exists
        super().save_model(request, obj, form, change)
        add_quantity = form.cleaned_data.get('add_quantity')
        movement_notes = form.cleaned_data.get('movement_notes')
        # Only create movement if add_quantity is positive and this is an add (not edit)
        if add_quantity and add_quantity > 0:
            from .models import MetalStockMovement
            MetalStockMovement.objects.create(
                metal_stock=obj,
                movement_type='in',
                quantity=add_quantity,
                notes=movement_notes or '',
                reference_type='Manual Add',
                reference_id=None
            )
            # Update MetalStock quantity and save again
            obj.quantity += add_quantity
            obj.save()


@admin.register(MetalStockMovement)
class MetalStockMovementAdmin(admin.ModelAdmin):
    list_display = ('metal_stock', 'movement_type', 'quantity', 'reference_type', 'reference_id', 'movement_date')
    list_filter = ('movement_type', 'metal_stock__metal_type', 'movement_date')
    search_fields = ('metal_stock__location', 'reference_id', 'notes')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Stock Movement', {
            'fields': ('metal_stock', 'movement_type', 'quantity', 'kaligar')
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