from django.contrib.auth import views as auth_views
# from etherpadlite.views import padDelete
from django.urls import path, re_path
from . import views
#from django.conf.urls import *
from django.views.generic import TemplateView
from django.http import HttpResponse

from django.conf import settings
from django.conf.urls import include
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

app_name = "ethertoff"

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('all/', views.all, name='all'), # TemplateView.as_view(template_name = 'all.html')
    #re_path(r'manage/(?P<page>[\d]+)?/?$', views.manage, name='manage'),
    path('manage/', views.manage, name='manage'),
    path('manage/<path:path>', views.manage, name='manage'),
    path('publish/', views.publish, name='publish'),
    path('css-screen/', views.css, name='css-screen'),
    path('css-print/', views.cssprint, name='css-print'),
    path('css-offset/', views.offsetprint, name='css-offset'),
    path('css-slide/', views.css_slide, name='css-slide'),
    re_path(r'^(?P<slug>[^/]+)\.xhtml$', views.xhtml, name='xhtml'),
    path('accounts/login', auth_views.LoginView.as_view(),
        {'template_name': 'login.html'}, name='login'),
    path('accounts/logout', auth_views.LogoutView.as_view(),
        {'template_name': 'logout.html'}, name='logout'),
    path('accounts/password_change', auth_views.PasswordChangeView.as_view(), name="password_change"),
    path('accounts/password_change_done', auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path('create/', views.padCreate, name='pad-create'),
    path('create/<path:prefix>', views.padCreate, name='pad-create'),
    re_path(r'^rename/(?P<pk>\d+)/$', views.padRename, name='pad-rename'),
    re_path(r'^delete/(?P<pk>\d+)/$', views.padDelete, name='pad-delete'),
    re_path(r'^public/(?P<pk>\d+)/$', views.padPublic, name='pad-public'),
    re_path(r'^private/(?P<pk>\d+)/$', views.padPrivate, name='pad-private'),
    re_path(r'(?P<mode>[r|s|p])/(?P<slug>[^/]+)$', views.pad_read, name='pad-read'),
    #re_path(r'r/(?P<slug>[^/]+)$', views.pad, name='pad-read'),
    #re_path(r's/(?P<slug>[^/]+)$', views.pad, name='pad-slide'),
    #re_path(r'p/(?P<slug>[^/]+)$', views.pad, name='pad-print'),
    re_path(r'w/(?P<slug>[^/]+)$', views.pad, name='pad-write'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#urlpatterns = [
    #path(BASE_URL , include(base_urlpatterns)),
#]
