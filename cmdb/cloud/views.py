from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from assets.models import VirtualServer
from cloud.models import CloudTaskTracker
from cloud.serializers import CloudTaskTrackerSerializer, VirtualServerSerializer


class CloudTaskTrackerViewSet(viewsets.mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    """
    ViewSet used to control cloud tasks. Is able to retrieve the state of the task.
    """
    queryset = CloudTaskTracker.objects.filter()
    serializer_class = CloudTaskTrackerSerializer
    pagination_class = PageNumberPagination


class VirtualServerViewSet(viewsets.GenericViewSet):
    queryset = VirtualServer.active.filter()
    serializer_class = VirtualServerSerializer
    pagination_class = PageNumberPagination

    @detail_route(methods=['patch'])
    def start(self, request, pk=None):
        return Response({"start": request.data})

    @detail_route(methods=['patch'])
    def stop(self, request, pk=None):
        return Response({"stop": request.data})
