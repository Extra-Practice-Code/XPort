from django.contrib.auth import views as auth_views
from django.conf.urls import include
from django.urls import path, re_path
from . import views


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('all/', views.all, name='all'), # TemplateView.as_view(template_name = 'all.html')
    #re_path(r'manage/(?P<page>[\d]+)?/?$', views.manage, name='manage'),
    path('manage', views.manage, name='manage'),
    path('manage/', views.manage, name='manage'),
    path('manage/<path:path>', views.manage, name='manage'),
    path('publish/', views.publish, name='publish'),
    path('generate/', views.generate, name='generate'),
    path('css-screen/', views.css, name='css-screen'),
    path('css-print/', views.cssprint, name='css-print'),
    path('css-offset/', views.offsetprint, name='css-offset'),
    path('css-slide/', views.css_slide, name='css-slide'),
    re_path(r'^(?P<slug>[^/]+)\.xhtml$', views.xhtml, name='xhtml'),
    path('create/', views.padCreate, name='pad-create'),
    path('create/<path:prefix>', views.padCreate, name='pad-create'),
    re_path(r'^rename/(?P<pk>\d+)/$', views.padRename, name='pad-rename'),
    re_path(r'^delete/(?P<pk>\d+)/$', views.padDelete, name='pad-delete'),
    re_path(r'^public/(?P<pk>\d+)/$', views.padPublic, name='pad-public'),
    re_path(r'^private/(?P<pk>\d+)/$', views.padPrivate, name='pad-private'),
    re_path(r'(?P<mode>[r|s|p])/(?P<slug>[^/]+)$', views.pad_read, name='pad-read'),
    re_path(r'(?P<mode>[r|s|p])/(?P<slug>[^/]+)$', views.pad_read, name='pad'),
    re_path(r'(?P<mode>[w])/(?P<slug>[^/]+)$', views.pad, name='pad'),
    #re_path(r'r/(?P<slug>[^/]+)$', views.pad, name='pad-read'),
    #re_path(r's/(?P<slug>[^/]+)$', views.pad, name='pad-slide'),
    #re_path(r'p/(?P<slug>[^/]+)$', views.pad, name='pad-print'),
    re_path(r'w/(?P<slug>[^/]+)$', views.pad, name='pad-write')
]
