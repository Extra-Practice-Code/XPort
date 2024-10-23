from django.urls import path

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# This is to allow the website to work under a subfolder
# i.e. http://ethertoff.be/2015/
# Define SUBFOLDER in your local_settings.py
BASE_URL = '^'
try:
    BASE_URL = r'^' + settings.SUBFOLDER
    if BASE_URL and not BASE_URL.endswith(r'/'):
        BASE_URL += r'/'
except AttributeError:
    pass

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^filer/', include('filer.urls')),
    path('', include("generator.urls")),
    path('', include("ethertoff.urls")),
    path('', include("going_hybrid.urls"))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#urlpatterns = [
    #path(BASE_URL , include(base_urlpatterns)),
#]
