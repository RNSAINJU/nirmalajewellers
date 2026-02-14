from django.contrib import admin
from django.db.models import Q
from django.contrib.admin import helpers
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from .models import MainCategory, SubCategory, Ornament
from .models import Kaligar, Kaligar_Ornaments, Kaligar_CashAccount, Kaligar_GoldAccount
from common.generate_product_images import generate_images_for_products

@admin.register(MainCategory)
class MainCategory(admin.ModelAdmin):
    list_display=('id', 'name')

@admin.register(SubCategory)
class SubCategory(admin.ModelAdmin):
    list_display=('id', 'name')

@admin.register(Ornament)
class OrnamentAdmin(admin.ModelAdmin):
    list_display = ('code','maincategory','subcategory', 'ornament_name', 'kaligar', 'weight', 'jarti', 'ornament_type', 'status', 'has_image_display')
    list_filter = ('type', 'ornament_type', 'status')
    search_fields = ('code', 'ornament_name')
    ordering = ('-ornament_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['mark_as_destroyed', 'generate_ai_images_replicate', 'generate_ai_images_stability']

    def has_image_display(self, obj):
        """Display whether product has an image."""
        if obj.image:
            return format_html('<span style="color: green;">✓ Has Image</span>')
        return format_html('<span style="color: red;">✗ No Image</span>')
    has_image_display.short_description = "Image Status"

    def mark_as_destroyed(self, request, queryset):
        """Action to mark ornaments as destroyed."""
        updated = queryset.update(status='destroyed')
        self.message_user(request, f'{updated} ornament(s) marked as destroyed.')
    mark_as_destroyed.short_description = "Mark selected ornaments as destroyed"

    def generate_ai_images_replicate(self, request, queryset):
        """Generate AI images using Replicate API (free-tier)."""
        return self._generate_ai_images(request, queryset, method='replicate')
    generate_ai_images_replicate.short_description = "Generate AI images (Replicate - Free)"

    def generate_ai_images_stability(self, request, queryset):
        """Generate AI images using Stability AI (premium quality)."""
        return self._generate_ai_images(request, queryset, method='stability')
    generate_ai_images_stability.short_description = "Generate AI images (Stability AI - Premium)"

    def _generate_ai_images(self, request, queryset, method='replicate'):
        """Core method to generate AI images for products without images."""
        # Filter products without images that are in stock and active
        products_to_process = queryset.filter(
            Q(image__isnull=True) | Q(image=''),
            ornament_type='stock',
            status='active'
        )
        
        if not products_to_process.exists():
            self.message_user(request, 
                'No products without images found in the selected items.',
                level='WARNING'
            )
            return
        
        count = products_to_process.count()
        
        # Check environment variable
        import os
        if method == 'replicate' and not os.environ.get('REPLICATE_API_TOKEN'):
            self.message_user(request,
                'Error: REPLICATE_API_TOKEN environment variable not set. '
                'Please set it and try again.',
                level='ERROR'
            )
            return
        
        if method == 'stability' and not os.environ.get('STABILITY_API_KEY'):
            self.message_user(request,
                'Error: STABILITY_API_KEY environment variable not set. '
                'Please set it and try again.',
                level='ERROR'
            )
            return
        
        # Start generation
        try:
            results = generate_images_for_products(products_to_process, method=method)
            
            # Build success message
            message = (
                f'✓ Generated: {results["success"]}/{count} images\n'
                f'✗ Failed: {results["failed"]}/{count} images\n'
                f'Method: {method.upper()}'
            )
            
            if results['errors']:
                message += f'\n\nErrors: {", ".join(results["errors"][:3])}'
                if len(results['errors']) > 3:
                    message += f' +{len(results["errors"]) - 3} more'
            
            if results['success'] > 0:
                self.message_user(request, message, level='SUCCESS')
            else:
                self.message_user(request, message, level='ERROR')
                
        except Exception as e:
            self.message_user(request,
                f'Error generating images: {str(e)}',
                level='ERROR'
            )


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

