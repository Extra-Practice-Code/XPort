from django.urls import path
from . import views

urlpatterns = [
    path('generator/css/<str:organisation_slug>/<str:publication>/<str:sheet>', views.generator_css, name='generator-css'),
    path('generator/js/<str:organisation_slug>/<str:publication>/<str:script>/', views.generator_javascript, name='generator-javascript')
]