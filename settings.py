# ... existing code ...
DEBUG = True  # dev only

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.trycloudflare.com']

CSRF_TRUSTED_ORIGINS = [
    'https://*.trycloudflare.com',
]
# Static files (recommended with WhiteNoise even in dev)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MIDDLEWARE = [
    # ... existing middleware ...
    'whitenoise.middleware.WhiteNoiseMiddleware',  # add for serving static files
    # ... existing middleware ...
]
# ... existing code ...
INSTALLED_APPS = [
    # ... existing Django apps ...
    'goldsilverpurchase',  # added
]
# ... existing code ...
