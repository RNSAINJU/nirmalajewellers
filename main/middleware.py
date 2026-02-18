from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    """Redirect anonymous users to login for all non-exempt paths."""

    def __init__(self, get_response):
        self.get_response = get_response
        # Only allow specific public paths - be restrictive!
        self.exempt_paths = {
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password_reset/',
            '/accounts/password_reset/done/',
            '/accounts/reset/',
        }
        # Public URL prefixes (no trailing slash - will use startswith)
        self.public_prefixes = {
            '/static/',
            '/media/',
            '/api/products/',
            '/shop',
            '/products/',
        }

    def __call__(self, request):
        path = request.path

        # Allow static/media files
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return self.get_response(request)
        
        # Allow specific login/auth paths
        if path in self.exempt_paths:
            return self.get_response(request)
        
        # Allow home page for customers (no deep paths)
        if path == '/':
            return self.get_response(request)

        # Everything else requires authentication
        if request.user.is_authenticated:
            return self.get_response(request)

        # Redirect to login with next param
        login_url = '/accounts/login/'
        return redirect(f"{login_url}?next={path}")
