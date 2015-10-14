from __future__ import unicode_literals
from django.conf.urls import url

from ipman.views import IpManagerRentIPs

urlpatterns = [
    url(r'^ipman/rent$', IpManagerRentIPs.as_view()),
]
