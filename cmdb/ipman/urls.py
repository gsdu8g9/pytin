from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from ipman.views import IpManagerRentIPsByPools, IpManagerRentIPsByDatacenter, IPAddressViewSet

router = DefaultRouter()
router.register('ip', IPAddressViewSet)

urlpatterns = [
    url(r'^ip/rent/pool$', IpManagerRentIPsByPools.as_view()),
    url(r'^ip/rent/dc$', IpManagerRentIPsByDatacenter.as_view()),
    url(r'^', include(router.urls)),
]
