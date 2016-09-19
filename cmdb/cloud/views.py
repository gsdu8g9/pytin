from __future__ import unicode_literals

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from assets.models import VirtualServer
from cloud.models import CloudTaskTracker, CmdbCloudConfig
from cloud.provisioning.backends.proxmox import ProxMoxJBONServiceBackend
from cloud.serializers import CloudTaskTrackerSerializer, StartStopSerializer, \
    CreateVpsSerializer
from cmdb.settings import logger


def error_response(exception, http_status=status.HTTP_400_BAD_REQUEST):
    assert exception

    return Response({'detail': exception.message}, status=http_status)


class CloudTaskTrackerViewSet(viewsets.mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
    """
    ViewSet used to control cloud tasks. Is only able to retrieve the state of the task.
    """
    queryset = CloudTaskTracker.objects.filter()
    serializer_class = CloudTaskTrackerSerializer
    pagination_class = PageNumberPagination


class VirtualServerViewSet(viewsets.mixins.CreateModelMixin,
                           viewsets.GenericViewSet):
    queryset = VirtualServer.active.filter()
    pagination_class = PageNumberPagination

    def create(self, request, *args, **kwargs):
        try:
            indata = CreateVpsSerializer(data=request.data)
            if not indata.is_valid():
                return Response(indata.errors,
                                status=status.HTTP_400_BAD_REQUEST)

            logger.info("Creating VPS: %s" % indata.data)

            # hardcoded backend
            cloud = CmdbCloudConfig()
            backend = ProxMoxJBONServiceBackend(cloud)

            tracker = backend.create_vps(**indata.data)

            serializer = CloudTaskTrackerSerializer(tracker)

            return Response(serializer.data)
        except Exception as ex:
            return error_response(ex)

    @detail_route(methods=['patch'])
    def start(self, request, pk=None):
        try:
            indata = StartStopSerializer(data=request.data)
            if not indata.is_valid():
                return Response(indata.errors,
                                status=status.HTTP_400_BAD_REQUEST)

            logger.info("Starting VPS: %s" % indata.data)

            # hardcoded backend
            cloud = CmdbCloudConfig()
            backend = ProxMoxJBONServiceBackend(cloud)

            tracker = backend.start_vps(**indata.data)

            serializer = CloudTaskTrackerSerializer(tracker)

            return Response(serializer.data)

        except Exception as ex:
            return error_response(ex)

    @detail_route(methods=['patch'])
    def stop(self, request, pk=None):
        try:
            indata = StartStopSerializer(data=request.data)
            if not indata.is_valid():
                return Response(indata.errors,
                                status=status.HTTP_400_BAD_REQUEST)

            logger.info("Stopping VPS: %s" % indata.data)

            # hardcoded backend
            cloud = CmdbCloudConfig()
            backend = ProxMoxJBONServiceBackend(cloud)

            tracker = backend.stop_vps(**indata.data)

            serializer = CloudTaskTrackerSerializer(tracker)

            return Response(serializer.data)

        except Exception as ex:
            return error_response(ex)
