from django.urls import path, re_path
from . import views

## FIXME: if uncommenting url namespacing will be needed
# app_name = "ethertoff"

urlpatterns = [
    path('', views.home, name='home'),
    path('all/', views.all, name='all'),
    path('manage/', views.manage, name='manage'),
    path('manage/<path:path>/', views.manage, name='manage'),
    path('publish/', views.publish, name='publish'),
    path('generate/', views.generate, name='generate'),
    path('css-screen/', views.css, name='css-screen'),
    path('css-print/', views.cssprint, name='css-print'),
    path('css-offset/', views.offsetprint, name='css-offset'),
    path('css-slide/', views.css_slide, name='css-slide'),
    path('create/', views.padCreate, name='pad-create'),
    path('create/<path:prefix>/', views.padCreate, name='pad-create'),
    path('rename-folder/', views.RenameFolderView.as_view(), name='folder-rename'),
    path('rename-folder/<path:prefix>/', views.RenameFolderView.as_view(), name='folder-rename'),
    path('rename/<int:pk>/', views.padRename, name='pad-rename'),
    path('delete/<int:pk>/', views.padDelete, name='pad-delete'),
    path('public/<int:pk>/', views.padPublic, name='pad-public'),
    path('private/<int:pk>/', views.padPrivate, name='pad-private'),
    re_path(r'(?P<mode>[r|s|p])/(?P<slug>[^/]+)$', views.pad_read, name='pad-read'),
    re_path(r'(?P<mode>[r|s|p])/(?P<slug>[^/]+)$', views.pad_read, name='pad'),
    re_path(r'(?P<mode>[w])/(?P<slug>[^/]+)$', views.pad, name='pad'),
    re_path(r'w/(?P<slug>[^/]+)$', views.pad, name='pad-write'),
    re_path(r'^(?P<slug>[^/]+)\.xhtml$', views.xhtml, name='xhtml'),
]
