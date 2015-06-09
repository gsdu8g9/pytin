from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from resources.views import ResourcesViewSet

router = DefaultRouter()
router.register('resources', ResourcesViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
