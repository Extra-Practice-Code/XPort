from django.urls import reverse
from django.conf import settings
from ethertoff.utils import pathToSlug, dynamic_import

def generate (request, path, obj):
    return [(str(part), part.url) for part in path] + [(str(obj), obj.url)]

def breadcrumbs (request, path, obj):
    if settings.BREADCRUMB_GENERATOR:
        return dynamic_import(settings.BREADCRUMB_GENERATOR)(request, path, obj)
    else:
        return generate(request, path, obj)