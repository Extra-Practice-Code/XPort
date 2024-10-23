from django.urls import path, register_converter
from . import views

from ethertoff.urlconverters import DirectoryConverter

register_converter(DirectoryConverter, 'directory')

urlpatterns = [
    path('generator/css/<str:organisation_slug>/<str:publication>/<str:sheet>', views.generator_css, name='generator-css'),
    path('generator/js/<str:organisation_slug>/<str:publication>/<str:script>/', views.generator_javascript, name='generator-javascript'),
    path('generator/publications', views.list_publications, name='generator-list-publications'),
    path('generator/generate', views.generate, name='generator-generate'),
    path('manage/<directory:directory>', views.manage, name='manage'),
    path('manage/', views.manage, name='manage'),
    path('manage', views.manage, name='manage'),
    path('generator/create-pad/<directory:directory>', views.padCreate, name='generator-pad-create')
]