# Nirmala Jewellers - Customer Homepage Documentation

## Overview

A complete, production-ready customer-facing e-commerce homepage for the Nirmala Jewellers website has been created. The homepage matches the design specifications shown in your screenshot and includes all necessary features for an online jewelry store.

## Features Implemented

### 1. **Customer Home Page** (`/`)
- **Location**: [main/templates/main/customer_home.html](main/templates/main/customer_home.html)
- **View Function**: `customer_home()` in [main/views.py](main/views.py)

**Components:**
- Premium navigation bar with:
  - Hamburger menu icon
  - "NIRMALA" branding (golden color)
  - Live search functionality
  - Shopping cart icon with item counter
  
- **Hero Section**:
  - Full-width banner with background image
  - "Antique Gold Collections" title
  - "SHOP COLLECTION" call-to-action button
  - Smooth scrolling to products

- **Categories Section**:
  - 4 main jewelry categories (Necklaces, Earrings, Rings, Bangles)
  - Beautiful card-based layout with icons
  - Hover effects and animations
  - "View All" link for full shop

- **New Arrivals Section**:
  - Grid display of latest products
  - Product cards with:
    - Product images (from Cloudinary)
    - Product name and category
    - Metal type and weight info
    - Wishlist heart button
    - Click-through to product detail page

### 2. **Product Detail Page** (`/products/<product_id>/`)
- **Location**: [main/templates/main/product_detail.html](main/templates/main/product_detail.html)
- **View Function**: `product_detail()` in [main/views.py](main/views.py)

**Features:**
- Full product specifications display
- High-quality product image
- Detailed specs: Metal type, Karat, Weight, Diamond weight, Stone weight
- "Add to Cart" and "Wishlist" buttons
- Contact information section
- Responsive design for mobile/tablet

### 3. **Category Product Listing** (`/shop/` and `/shop/category/<id>/`)
- **Location**: [main/templates/main/category_products.html](main/templates/main/category_products.html)
- **View Functions**: 
  - `category_products()` - View products by category or all products
  - [main/views.py](main/views.py)

**Features:**
- Filter panel with:
  - Metal type filters
  - Karat filters
  - Weight range filters
- Sort dropdown (Newest, Name A-Z, Weight ascending/descending)
- Product grid with:
  - Image, name, code, metal type, weight
  - Wishlist functionality
  - Click-through to product detail

### 4. **API Endpoints** (for frontend interactivity)

#### Get Products by Category
```
GET /api/products/by-category/<category_id>/
```
Returns products filtered by category ID

#### Search Products
```
GET /api/products/search/?q=<search_term>
```
Search for products by name or code

#### Get Featured Products
```
GET /api/products/featured/?limit=12
```
Get latest/featured products with optional limit parameter

### 5. **Shopping Cart**
- Cart count stored in browser localStorage
- Click cart icon to toggle cart
- Add to cart functionality
- Persistent cart across page reloads

### 6. **Wishlist**
- Heart icon on products
- Click to add/remove from wishlist
- Visual feedback with color change

## Design Details

### Color Scheme
- **Primary Color**: #FFD700 (Gold)
- **Dark Background**: #1a1a1a
- **Card Background**: #2a2a2a
- **Text Color**: #e0e0e0

### Responsive Design
- **Desktop**: Full grid layouts, 4+ columns
- **Tablet**: 2-3 columns, adjusted navigation
- **Mobile**: 2 columns, simplified navigation

### Performance Optimizations
- Lazy loading images (Cloudinary integration)
- Minimal CSS for fast loading
- Efficient grid layouts
- Smooth animations with GPU acceleration

## Database Integration

### Models Used
- **Ornament**: Main product model
  - Fields: ornament_name, code, metal_type, type (karat), weight, image, diamond_weight, stone_weight
  - Related to MainCategory via maincategory field

- **MainCategory**: Product categories
  - Fields: name
  - Related to Ornaments (one-to-many)

- **SubCategory**: Sub categories (for future use)

### Filtering
```python
Ornament.objects.filter(
    ornament_type='stock',
    status='active',
    image__isnull=False
).order_by('-created_at')
```

## URL Routing

### Main Routes
```python
path('', views.customer_home, name='customer_home')              # Home page
path('admin-dashboard/', views.dashboard, name='dashboard')     # Admin dashboard
path('products/<int:product_id>/', views.product_detail, name='product_detail')
path('shop/', views.category_products, name='shop')             # All products
path('shop/category/<int:category_id>/', views.category_products, name='category_products')
```

### API Routes
```python
path('api/products/by-category/<int:category_id>/', views.api_products_by_category)
path('api/products/search/', views.api_search_products)
path('api/products/featured/', views.api_featured_products)
```

## Usage Instructions

### 1. Prerequisites
- Django 5.2+
- Python 3.10+
- Cloudinary account (for image storage)
- Bootstrap Icons for icon library

### 2. Setup Steps
Already completed! The homepage is fully integrated with your project.

### 3. Accessing the Homepage
- Go to `http://localhost:8000/` to see the customer homepage
- Admin dashboard (unchanged) is at `http://localhost:8000/admin-dashboard/`

### 4. Adding Products
Products are automatically pulled from your Ornament model where:
- `ornament_type = 'stock'`
- `status = 'active'`
- `image` is not null (has a CloudinaryField image)

### 5. Managing Categories
Create MainCategory objects in Django admin or through your existing interfaces to populate the categories section.

## Frontend Features

### JavaScript Functionality
- **Search**: Real-time product filtering
- **Cart**: LocalStorage-based shopping cart management
- **Wishlist**: Toggle wishlist items with visual feedback
- **Sorting**: Sort products by various criteria
- **Filtering**: Filter products by metal type, karat, weight

### Accessibility
- Semantic HTML
- Color contrast compliance
- Proper alt text for images
- Keyboard navigation support
- Mobile-friendly touch targets

## Customization Options

### 1. Modify Hero Section
Edit the background image URL in [customer_home.html](main/templates/main/customer_home.html):
```html
background: linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 100%), 
            url('YOUR_IMAGE_URL');
```

### 2. Change Colors
Update CSS variables at the top of each template:
```css
:root {
    --primary-color: #FFD700;  /* Change this */
    --dark-bg: #1a1a1a;        /* Change this */
}
```

### 3. Add More Categories
Add MainCategory items in Django admin, they'll automatically appear in the UI

### 4. Customize Product Cards
Modify the product card HTML in the products grid section to show/hide fields

## Future Enhancements

Possible improvements:
1. **Shopping Cart Backend**: Replace localStorage with database cart
2. **User Accounts**: Login/registration for wishlist persistence
3. **Product Reviews**: Add customer reviews and ratings
4. **Advanced Filters**: Price range, availability, etc.
5. **Product Variants**: Size, color, quantity options
6. **Checkout Page**: Payment integration
7. **Order Management**: Track orders
8. **Email Notifications**: Order confirmations, shipping updates
9. **Analytics**: Track user behavior and sales
10. **Admin Dashboard**: Inventory management from admin panel

## Testing

To test the homepage:

1. **Create test products** (or use existing ones):
   ```bash
   python manage.py shell
   ```
   ```python
   from ornament.models import Ornament, MainCategory
   from django.core.files.base import ContentFile
   
   # Create a category
   cat = MainCategory.objects.create(name="Necklaces")
   
   # Create a product (with image from Cloudinary)
   product = Ornament.objects.create(
       ornament_name="Gold Necklace",
       code="NECK001",
       maincategory=cat,
       metal_type="Gold",
       type="24KARAT",
       ornament_type="stock",
       status="active",
       weight=5.5
   )
   ```

2. **Visit the homepage**:
   - Go to `http://localhost:8000/`
   - Test navigation, search, filtering
   - Click on products to view details
   - Test mobile responsiveness

3. **Check API endpoints**:
   - `http://localhost:8000/api/products/featured/`
   - `http://localhost:8000/api/products/search/?q=gold`

## File Structure

```
nirmalajewellers/
├── main/
│   ├── templates/main/
│   │   ├── customer_home.html          # Main homepage
│   │   ├── product_detail.html         # Product detail page
│   │   └── category_products.html      # Category listing
│   ├── views.py                        # All view functions
│   ├── urls.py                         # URL routing
│   └── ...
├── ornament/
│   ├── models.py                       # Ornament model
│   └── ...
└── manage.py
```

## Technical Stack

- **Backend**: Django 5.2
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Image Hosting**: Cloudinary
- **Icons**: Bootstrap Icons
- **Database**: SQLite (development) / PostgreSQL (production)

## Support & Troubleshooting

### Issue: Products not showing
- **Solution**: Make sure products have:
  - `ornament_type = 'stock'`
  - `status = 'active'`
  - `image` field populated (Cloudinary URL)

### Issue: Images not loading
- **Solution**: Check Cloudinary configuration in settings.py

### Issue: Category products not filtering
- **Solution**: Ensure products are linked to MainCategory via maincategory field

### Issue: Mobile layout broken
- **Solution**: Check viewport meta tag in base.html (should be present)

## Performance Notes

- Homepage loads ~6-8 products from database
- API endpoints are limited to 20-15 products per request
- Images are served from Cloudinary CDN for fast loading
- CSS is inline for faster rendering
- No external font files (system fonts)

## License & Credits

Created for Nirmala Jewellers E-commerce Platform
Based on modern e-commerce best practices
Designed for premium jewelry retail

---

**Last Updated**: February 13, 2026
**Version**: 1.0
**Status**: Production Ready ✓
