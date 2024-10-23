from django.urls import path, re_path, register_converter
from . import views
from ethertoff.urlconverters import DirectoryConverter, PadConverter

register_converter(DirectoryConverter, 'directory')
register_converter(PadConverter, 'pad')


## FIXME: if uncommenting url namespacing will be needed
# app_name = "ethertoff"


urlpatterns = [
    path('', views.home, name='home'),
    path('all/', views.all, name='all'),
    # path('public/', views.all_public, name='public'),
    path('register/<str:organisation_slug>', views.register, name='register'),
    path('manage/', views.manage, name='manage'),
    # path('manage/', views.manage, name='manage'),
    # path('manage/<path:path>/', views.manage, name='manage'),
    path('manage/<directory:directory>', views.manage, name='manage'),
    path('publish/', views.publish, name='publish'),
    path('generate/', views.generate, name='generate'),
    path('generate/<str:organisation_slug>', views.generate, name='generate'),
    path('index-labels/', views.index_labels, name='index-labels'),
    path('css-screen/', views.css, name='css-screen'),
    path('css-print/', views.cssprint, name='css-print'),
    path('css-offset/', views.offsetprint, name='css-offset'),
    path('css-slide/', views.css_slide, name='css-slide'),
    # path('css-generator-screen/<str:organisation_slug>/<str:folder>', views.css_generator_screen, name='css-generator-screen'),
    # path('css-generator-print/<str:organisation_slug>/<str:folder>', views.css_generator_print, name='css-generator-print'),
    # path('javascript-generator/<str:organisation_slug>/<str:folder>', views.javascript_generator, name='javascript-generator'),
    # path('javascript-generator-print/<str:organisation_slug>/<str:folder>', views.javascript_generator_print, name='javascript-generator-print'),
    path('create/', views.padCreate, name='pad-create'),
    path('create/<directory:prefix>/', views.padCreate, name='pad-create'),
    path('rename-folder/', views.RenameFolderView.as_view(), name='folder-rename'),
    path('rename-folder/<directory:prefix>/', views.RenameFolderView.as_view(), name='folder-rename'),
    # path('rename/<int:pk>/', views.padRename, name='pad-rename'),
    path('rename/<pad:pad>', views.padRename, name='pad-rename'),
    path('delete/<pad:pad>', views.padDelete, name='pad-delete'),
    path('public/<pad:pad>', views.padPublic, name='pad-public'),
    path('private/<pad:pad>', views.padPrivate, name='pad-private'),
    path('api/file/canonical-url/<int:pk>/', views.get_canoninical, name='get-canonical'),
    path('api/file/mime/<int:pk>/', views.get_mimetype, name='get-mime'),
    path('w/<pad:pad>', views.pad, name='pad-write'),
    re_path('api/labels(/(?P<slug>[^/]+)?)$', views.labels, name='api-labels'),
    re_path(r'(?P<mode>[r|s|p])/(?P<slug>[^/]+)$', views.pad_read, name='pad-read'),
    re_path(r'(?P<mode>[r|s|p])/(?P<slug>[^/]+)$', views.pad_read, name='pad'),
    re_path(r'(?P<mode>[w])/(?P<slug>[^/]+)$', views.pad, name='pad'),
    # re_path(r'w/(?P<slug>[^/]+)$', views.pad, name='pad-write'),
    re_path(r'^(?P<slug>[^/]+)\.xhtml$', views.xhtml, name='xhtml'),
]
