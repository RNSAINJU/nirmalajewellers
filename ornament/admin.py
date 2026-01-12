from django.contrib import admin
from .models import MainCategory, SubCategory, Ornament
from .models import Kaligar, Kaligar_Ornaments, Kaligar_CashAccount, Kaligar_GoldAccount

@admin.register(MainCategory)
class MainCategory(admin.ModelAdmin):
    list_display=('id', 'name')

@admin.register(SubCategory)
class SubCategory(admin.ModelAdmin):
    list_display=('id', 'name')

@admin.register(Ornament)
class OrnamentAdmin(admin.ModelAdmin):
    list_display = ('code','maincategory','subcategory', 'ornament_name', 'kaligar', 'weight', 'jarti', 'ornament_type', 'status')
    list_filter = ('type', 'ornament_type', 'status')
    search_fields = ('code', 'ornament_name')
    ordering = ('-ornament_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['mark_as_destroyed']

    def mark_as_destroyed(self, request, queryset):
        """Action to mark ornaments as destroyed."""
        updated = queryset.update(status='destroyed')
        self.message_user(request, f'{updated} ornament(s) marked as destroyed.')
    mark_as_destroyed.short_description = "Mark selected ornaments as destroyed"


class KaligarOrnamentsInline(admin.TabularInline):
    model = Kaligar_Ornaments
    extra = 1  # Number of empty forms to show
    readonly_fields = ('gold_loss',)  # if you want some fields read-only

class KaligarCashAccountInline(admin.TabularInline):
    model = Kaligar_CashAccount
    extra = 1

class KaligarGoldAccountInline(admin.TabularInline):
    model = Kaligar_GoldAccount
    extra = 1

@admin.register(Kaligar)
class KaligarAdmin(admin.ModelAdmin):
    list_display = ('name', 'panno', 'phone_no', 'address')
    search_fields = ('name', 'panno', 'phone_no')
    inlines = [KaligarOrnamentsInline, KaligarCashAccountInline, KaligarGoldAccountInline]

