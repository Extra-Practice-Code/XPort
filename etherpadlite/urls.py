from django.contrib.auth import views as auth_views
from django.conf.urls.defaults import patterns, url

from etherpadlite.models import *


urlpatterns = [
    #path('', 'django.contrib.auth.views.login',
        #{'template_name': 'etherpad-lite/login.html'}, name='login'),
    path('', auth_views.LoginView.as_view(),
        {'template_name': 'login.html'}, name='login'),
    path('etherpad', 'django.contrib.auth.views.login',
        {'template_name': 'etherpad-lite/login.html'}),
    path('logout', 'django.contrib.auth.views.logout',
        {'template_name': 'etherpad-lite/logout.html'}),
    path('accounts/profile/', 'etherpadlite.views.profile'),
    re_path(r'^etherpad/(?P<pk>\d+)/$', 'etherpadlite.views.pad'),
    re_path(r'^etherpad/create/(?P<pk>\d+)/$', 'etherpadlite.views.padCreate'),
    re_path(r'^etherpad/delete/(?P<pk>\d+)/$', 'etherpadlite.views.padDelete'),
    path('group/create/', 'etherpadlite.views.groupCreate')
]
