from __future__ import unicode_literals

from rest_framework import viewsets

from resources.models import Resource
from resources.serializers import ResourceSerializer


class ResourcesViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.active()
    serializer_class = ResourceSerializer
