from __future__ import unicode_literals
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    url(r'^v1/auth/', obtain_auth_token),
    url(r'^v1/', include('resources.urls')),
    url(r'^v1/', include('ipman.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
