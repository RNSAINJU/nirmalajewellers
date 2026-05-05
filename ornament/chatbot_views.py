"""
Ornament Chatbot API Views
Handles natural language queries about ornaments
"""

import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Ornament, MainCategory, SubCategory, Kaligar


def query_ornaments(query_text):
    """
    Process natural language query and return ornament details
    """
    query_lower = query_text.lower()
    ornaments = Ornament.objects.filter(status='active')
    response_text = ""
    found_ornaments = []
    
    # Filter by metal type
    if any(word in query_lower for word in ['gold', 'सोन', 'सुन']):
        ornaments = ornaments.filter(metal_type='Gold')
        if not response_text:
            response_text = "🏆 Gold ornaments available:"
    elif any(word in query_lower for word in ['silver', 'चाँदी']):
        ornaments = ornaments.filter(metal_type='Silver')
        if not response_text:
            response_text = "✨ Silver ornaments available:"
    elif any(word in query_lower for word in ['diamond', 'हिरा', 'हीरा']):
        ornaments = ornaments.filter(metal_type='Diamond')
        if not response_text:
            response_text = "💎 Diamond ornaments available:"
    
    # Filter by karat
    if '24' in query_lower:
        ornaments = ornaments.filter(type='24KARAT')
        response_text = "24 Karat gold ornaments:"
    elif '22' in query_lower:
        ornaments = ornaments.filter(type='22KARAT')
        response_text = "22 Karat gold ornaments:"
    elif '18' in query_lower:
        ornaments = ornaments.filter(type='18KARAT')
        response_text = "18 Karat gold ornaments:"
    
    # Filter by ornament type/category
    if any(word in query_lower for word in ['necklace', 'neck', 'ढोक', 'सुर्ता']):
        main_cat = MainCategory.objects.filter(name__icontains='necklace').first()
        if main_cat:
            ornaments = ornaments.filter(maincategory=main_cat)
        response_text = "💍 Necklaces available:"
    elif any(word in query_lower for word in ['earring', 'ear', 'कान', 'चर्चुली']):
        main_cat = MainCategory.objects.filter(name__icontains='earring').first()
        if main_cat:
            ornaments = ornaments.filter(maincategory=main_cat)
        response_text = "👂 Earrings available:"
    elif any(word in query_lower for word in ['ring', 'अँठी', 'अंठी']):
        main_cat = MainCategory.objects.filter(name__icontains='ring').first()
        if main_cat:
            ornaments = ornaments.filter(maincategory=main_cat)
        response_text = "💍 Rings available:"
    elif any(word in query_lower for word in ['bracelet', 'bangle', 'कंगना', 'चुडी']):
        main_cat = MainCategory.objects.filter(name__icontains='bangle').first()
        if main_cat:
            ornaments = ornaments.filter(maincategory=main_cat)
        response_text = "✨ Bracelets/Bangles available:"
    elif any(word in query_lower for word in ['pendant', 'लॉकेट', 'पेंडन्ट']):
        main_cat = MainCategory.objects.filter(name__icontains='pendant').first()
        if main_cat:
            ornaments = ornaments.filter(maincategory=main_cat)
        response_text = "🎁 Pendants available:"
    
    # Filter by weight range (light, medium, heavy)
    if any(word in query_lower for word in ['light', 'हल्का', 'कम तोल']):
        ornaments = ornaments.filter(weight__lt=10)
        response_text = "⬇️ Lightweight ornaments (under 10g):"
    elif any(word in query_lower for word in ['heavy', 'भारी', 'अधिक तोल']):
        ornaments = ornaments.filter(weight__gt=20)
        response_text = "⬆️ Heavy ornaments (over 20g):"
    elif any(word in query_lower for word in ['medium', 'मध्यम', 'सामान्य']):
        ornaments = ornaments.filter(weight__gte=10, weight__lte=20)
        response_text = "⚖️ Medium weight ornaments (10-20g):"
    
    # Filter by price range if mentioned
    if 'under' in query_lower or 'below' in query_lower or '<' in query_lower:
        try:
            # Extract price from query
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', query_lower)
            if match:
                price = float(match.group(1))
                # This would require a price field in Ornament model
                # For now, we'll just use weight as a proxy
        except:
            pass
    
    # Search by ornament name
    name_matches = ornaments.filter(
        Q(ornament_name__icontains=query_text) |
        Q(code__icontains=query_text) |
        Q(description__icontains=query_text)
    )
    
    if name_matches.exists():
        ornaments = name_matches
        response_text = f"✓ Found ornaments matching '{query_text}':"
    
    # Limit results
    found_ornaments = ornaments[:10]
    
    if not found_ornaments:
        response_text = "❌ Sorry, I couldn't find ornaments matching your criteria. Try searching by:"
        suggestions = [
            "• Metal type (Gold, Silver, Diamond)",
            "• Karat (24, 22, 18)",
            "• Type (Necklace, Ring, Bracelet, Earring)",
            "• Weight range (Light, Medium, Heavy)",
            "• Ornament name or code"
        ]
        response_text += "\n" + "\n".join(suggestions)
        return {
            'success': False,
            'response': response_text,
            'ornaments': []
        }
    
    if not response_text:
        response_text = "Found ornaments:"
    
    # Prepare ornament data for response
    ornament_data = []
    for ornament in found_ornaments:
        ornament_data.append({
            'id': ornament.id,
            'ornament_name': ornament.ornament_name,
            'code': ornament.code or 'N/A',
            'metal_type': ornament.metal_type,
            'type': ornament.type,
            'weight': float(ornament.weight),
            'diamond_weight': float(ornament.diamond_weight),
            'stone_weight': float(ornament.stone_weight),
            'kaligar': ornament.kaligar.name if ornament.kaligar else 'N/A',
            'category': ornament.maincategory.name if ornament.maincategory else 'N/A',
            'sub_category': ornament.subcategory.name if ornament.subcategory else 'N/A',
            'description': ornament.description or 'N/A',
        })
    
    return {
        'success': True,
        'response': f"{response_text} ({len(found_ornaments)} results)",
        'ornaments': ornament_data
    }


@require_http_methods(["POST"])
@csrf_exempt
def ornament_chat_api(request):
    """
    API endpoint for ornament chatbot
    Accepts POST with JSON payload: {"query": "user's question"}
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if not query:
            return JsonResponse({
                'success': False,
                'response': '❌ Please ask a question about ornaments!'
            })
        
        result = query_ornaments(query)
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'response': '❌ Invalid request format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'response': f'❌ Error: {str(e)}'
        }, status=500)
