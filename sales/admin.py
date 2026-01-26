from django.contrib import admin
from . import models

# Register all models in the sales app
for model in models.__dict__.values():
    if isinstance(model, type) and issubclass(model, models.models.Model):
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass
