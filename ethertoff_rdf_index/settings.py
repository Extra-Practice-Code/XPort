from django.conf import settings

# OPTION_C = getattr(settings, '_'.join([NAMESPACE, 'OPTION_C']), None)
# if OPTION_C is None:
#     raise ImproperlyConfigured('...')
STORE = getattr(settings, "ETHERTOFF_RDF_STORE", {
    'ENGINE': 'sqlite',
    'NAME': 'aasniff.sqlite',
})
