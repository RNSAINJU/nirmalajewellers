"""
Generate AI images for products without images using Replicate API.
Supports both image download/save and Cloudinary upload.
"""

import os
import requests
import json
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def generate_image_prompt(product):
    """Generate a detailed prompt from product data."""
    name = product.ornament_name or "jewelry"
    metal_type = product.get_metal_type_display() or "gold"
    product_type = product.get_type_display() or "jewelry"
    
    prompt = f"{name} {metal_type} {product_type} jewelry, detailed, high quality, professional product photography, white background, jewelry product photo"
    
    return prompt


def generate_image_with_replicate(product):
    """
    Generate image using Replicate API (free with credits).
    Requires: REPLICATE_API_TOKEN environment variable
    """
    try:
        import replicate
    except ImportError:
        return None
    
    api_token = os.environ.get('REPLICATE_API_TOKEN')
    if not api_token:
        print("Error: REPLICATE_API_TOKEN environment variable not set")
        return None
    
    prompt = generate_image_prompt(product)
    
    try:
        # Using Stable Diffusion or DALL-E via Replicate
        output = replicate.run(
            "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3d66f3d6a0bea0ff123218ec2e23c0d50b0950",
            input={"prompt": prompt, "width": 512, "height": 512}
        )
        
        if output and len(output) > 0:
            return output[0]  # Returns URL of generated image
        return None
    except Exception as e:
        print(f"Replicate API error: {str(e)}")
        return None


def generate_image_with_stability(product):
    """
    Generate image using Stability AI API.
    Requires: STABILITY_API_KEY environment variable
    """
    try:
        import base64
        from stability_sdk.client import StabilityInference
        from stability_sdk.models.engines import EngineID
        from stability_sdk.models.messages import Message, MessageType
    except ImportError:
        print("Install stability-sdk: pip install stability-sdk")
        return None
    
    api_key = os.environ.get('STABILITY_API_KEY')
    if not api_key:
        print("Error: STABILITY_API_KEY environment variable not set")
        return None
    
    prompt = generate_image_prompt(product)
    
    try:
        client = StabilityInference(
            api_key=api_key,
            engine_id=EngineID.STABLE_DIFFUSION_XL_1_0,
            verbose=True,
        )
        
        resp = client.generate(
            prompt=prompt,
            steps=30,
            cfg_scale=7.0,
            width=512,
            height=512,
            sampler="K_EULER_ANCESTRAL"
        )
        
        for resp_item in resp:
            if isinstance(resp_item, Message):
                for item in resp_item.message:
                    if item.type == MessageType.ARTIFACT:
                        return {
                            'data': item.binary,
                            'type': 'binary'
                        }
        return None
    except Exception as e:
        print(f"Stability AI error: {str(e)}")
        return None


def download_and_save_image(image_url, product):
    """
    Download image from URL and save to product.
    Works with both local storage and Cloudinary.
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Generate filename
        filename = f"products/{product.id}_ai_generated.jpg"
        
        # Save to storage (local or Cloudinary via CloudinaryStorage)
        file_content = ContentFile(response.content)
        product.image.save(filename, file_content, save=True)
        
        return True
    except Exception as e:
        print(f"Error downloading/saving image for product {product.id}: {str(e)}")
        return False


def save_binary_image(image_data, product):
    """Save binary image data directly to product."""
    try:
        filename = f"products/{product.id}_ai_generated.jpg"
        file_content = ContentFile(image_data)
        product.image.save(filename, file_content, save=True)
        return True
    except Exception as e:
        print(f"Error saving image for product {product.id}: {str(e)}")
        return False


def generate_images_for_products(product_queryset, method='replicate'):
    """
    Generate images for products without images.
    
    Args:
        product_queryset: QuerySet of products to process
        method: 'replicate' (free with credits) or 'stability' (paid but good quality)
    
    Returns:
        dict with success and error counts
    """
    results = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    products = product_queryset.filter(image__isnull=True) | product_queryset.filter(image='')
    results['total'] = products.count()
    
    print(f"Starting image generation for {results['total']} products...")
    
    for i, product in enumerate(products, 1):
        print(f"\n[{i}/{results['total']}] Processing: {product.ornament_name}")
        
        try:
            # Generate image
            if method == 'stability':
                image_result = generate_image_with_stability(product)
                if image_result and 'data' in image_result:
                    if save_binary_image(image_result['data'], product):
                        results['success'] += 1
                        print(f"✓ Image generated and saved for {product.ornament_name}")
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to save image for product {product.id}")
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to generate image for product {product.id}")
            else:  # replicate
                image_url = generate_image_with_replicate(product)
                if image_url:
                    if download_and_save_image(image_url, product):
                        results['success'] += 1
                        print(f"✓ Image generated and saved for {product.ornament_name}")
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to download image for product {product.id}")
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to generate image for product {product.id}")
                    
        except Exception as e:
            results['failed'] += 1
            error_msg = f"Error processing product {product.id}: {str(e)}"
            results['errors'].append(error_msg)
            print(f"✗ {error_msg}")
    
    return results
