"""
Cloudinary utilities for image optimization and URL generation
"""
import cloudinary.api
from cloudinary.utils import cloudinary_url
from django.conf import settings


class CloudinaryImageOptimizer:
    """
    Utility class for generating optimized Cloudinary URLs
    Compresses images without quality loss
    """
    
    # Preset optimization levels
    PRESETS = {
        'thumbnail': {
            'width': 200,
            'height': 200,
            'crop': 'fill',
            'quality': 'auto',
            'fetch_format': 'auto',
        },
        'medium': {
            'width': 600,
            'height': 600,
            'crop': 'fill',
            'quality': 'auto',
            'fetch_format': 'auto',
            'flags': 'progressive',
        },
        'large': {
            'width': 1200,
            'height': 1200,
            'crop': 'scale',
            'quality': 'auto',
            'fetch_format': 'auto',
            'flags': 'progressive',
        },
        'display': {  # For customer display pages
            'width': 800,
            'height': 800,
            'crop': 'fill',
            'quality': 'auto',
            'fetch_format': 'auto',
            'flags': 'progressive',
            'dpr': 'auto',  # Auto device pixel ratio
        }
    }
    
    @staticmethod
    def get_optimized_url(public_id, preset='display', **kwargs):
        """
        Generate optimized Cloudinary URL
        
        Args:
            public_id: Cloudinary public ID of the image
            preset: One of 'thumbnail', 'medium', 'large', 'display'
            **kwargs: Additional transformation parameters to override preset
            
        Returns:
            Optimized Cloudinary URL string
        """
        if not public_id:
            return ''
        
        # Get base transformation from preset
        transformation = CloudinaryImageOptimizer.PRESETS.get(preset, {}).copy()
        
        # Override with custom parameters
        transformation.update(kwargs)
        
        # Generate URL
        url, _ = cloudinary_url(public_id, **transformation)
        return url
    
    @staticmethod
    def get_responsive_url(public_id, max_width=800, quality='auto'):
        """
        Generate responsive image URL that adapts to device
        
        Args:
            public_id: Cloudinary public ID
            max_width: Maximum width in pixels
            quality: Quality setting ('auto', 85, 75, etc.)
            
        Returns:
            Optimized URL
        """
        url, _ = cloudinary_url(
            public_id,
            width=max_width,
            crop='scale',
            quality=quality,
            fetch_format='auto',
            flags='progressive',
            dpr='auto',
        )
        return url
    
    @staticmethod
    def get_multiple_urls(public_id):
        """
        Generate multiple optimized URLs for different use cases
        
        Returns:
            Dictionary with different optimized URLs
        """
        return {
            'thumbnail': CloudinaryImageOptimizer.get_optimized_url(public_id, 'thumbnail'),
            'medium': CloudinaryImageOptimizer.get_optimized_url(public_id, 'medium'),
            'large': CloudinaryImageOptimizer.get_optimized_url(public_id, 'large'),
            'display': CloudinaryImageOptimizer.get_optimized_url(public_id, 'display'),
        }


def generate_optimized_url(image_field, preset='display'):
    """
    Django template filter function
    Usage: {{ ornament.image|generate_optimized_url:"large" }}
    """
    if not image_field:
        return ''
    
    # If it's already a URL, return as is
    if isinstance(image_field, str) and image_field.startswith('http'):
        return image_field
    
    # Get public ID from CloudinaryField
    public_id = str(image_field)
    return CloudinaryImageOptimizer.get_optimized_url(public_id, preset)


# Django template filter registration
from django import template
register = template.Library()

@register.filter
def optimize_image(image_field, preset='display'):
    """
    Cloudinary image optimization filter for Django templates
    Usage: {{ ornament.image|optimize_image:"large" }}
    """
    return generate_optimized_url(image_field, preset)


@register.filter
def image_url_responsive(image_field):
    """
    Generate responsive image URL
    Usage: {{ ornament.image|image_url_responsive }}
    """
    if not image_field:
        return ''
    public_id = str(image_field)
    return CloudinaryImageOptimizer.get_responsive_url(public_id)
