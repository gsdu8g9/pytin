from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from cloud.views import CloudTaskTrackerViewSet, VirtualServerViewSet

router = DefaultRouter()
router.register('cloud_tasks', CloudTaskTrackerViewSet)
router.register('vps', VirtualServerViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
