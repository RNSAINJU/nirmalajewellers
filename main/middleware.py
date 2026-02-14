from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    """Redirect anonymous users to login for all non-exempt paths."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_prefixes = {
            settings.LOGIN_URL.rstrip('/'),
            '/accounts',
            '/admin',
            '/order/api/search-ornaments',
            '/order/api/create-ornament-inline',
            '/',  # Customer home page
            '/shop',  # Shop pages
            '/products',  # Product detail pages
            '/api',  # API endpoints
        }
        self.static_prefix = getattr(settings, 'STATIC_URL', '/static/') or '/static/'
        self.media_prefix = getattr(settings, 'MEDIA_URL', '/media/') or '/media/'

    def __call__(self, request):
        path = request.path

        # Allow static/media
        if self.static_prefix and path.startswith(self.static_prefix):
            return self.get_response(request)
        if self.media_prefix and path.startswith(self.media_prefix):
            return self.get_response(request)

        # Allow admin and auth/account routes
        for prefix in self.exempt_prefixes:
            if prefix and path.startswith(prefix):
                return self.get_response(request)

        if request.user.is_authenticated:
            return self.get_response(request)

        # Redirect to login with next param
        login_url = settings.LOGIN_URL or '/accounts/login/'
        return redirect(f"{login_url}?next={path}")
