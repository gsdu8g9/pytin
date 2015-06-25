from __future__ import unicode_literals

import django_filters
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from resources.models import Resource
from resources.serializers import ResourceSerializer


class ResourceFilter(django_filters.FilterSet):
    class Meta:
        model = Resource

class ResourcesViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.active()
    serializer_class = ResourceSerializer
    filter_class = ResourceFilter
    pagination_class = PageNumberPagination

    def get_queryset(self):
        params = {}
        for field_name in self.request.query_params:
            params[field_name] = self.request.query_params.get(field_name)

        return Resource.objects.active(**params)
