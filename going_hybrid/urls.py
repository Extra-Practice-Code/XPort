from django.urls import path
from . import views

urlpatterns = [
    path('create-publication/', views.create_publication, name='publication-create'),
    path('create-publication/<str:organisation_slug>', views.create_publication, name='publication-create'),
    path('create-visual-styles/<str:prefix>', views.create_visual_styles, name='visual-styles-create')
]