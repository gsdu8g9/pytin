from django.conf.urls import url

from ipman.views import IpPoolNewIPs

urlpatterns = [
    url(r'^ippool/(?P<pk>[0-9]+)/newip$', IpPoolNewIPs.as_view()),
]
