from __future__ import unicode_literals

import django_filters
from rest_framework import generics
from rest_framework import mixins
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cmdb.settings import logger
from ipman.models import IPAddressRenter, IPAddressPoolGeneric, IPAddressGeneric
from ipman.serializers import IpAddressSerializer
from resources.models import Resource


class IPAddressFilter(django_filters.FilterSet):
    class Meta:
        model = IPAddressGeneric


class IPAddressViewSet(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    queryset = IPAddressGeneric.objects.filter()
    serializer_class = IpAddressSerializer
    filter_class = IPAddressFilter
    pagination_class = PageNumberPagination

    def get_queryset(self):
        skip_fields = [self.pagination_class.page_query_param, self.pagination_class.page_size_query_param]
        params = {}
        for field_name in self.request.query_params:
            if field_name in skip_fields:
                continue

            params[field_name] = self.request.query_params.get(field_name)

        return IPAddressGeneric.objects.filter(**params)


class IpManagerRentIPsBase(generics.RetrieveAPIView):
    queryset = IPAddressGeneric.objects.all()
    serializer_class = IpAddressSerializer

    def error_response(self, exception, http_status=status.HTTP_400_BAD_REQUEST):
        assert exception

        return Response({'detail': exception.message}, status=http_status)

    def rent_ips(self, renter, ip_count):
        assert renter
        assert isinstance(renter, IPAddressRenter)
        assert ip_count > 0

        rented_ips = renter.rent(count=ip_count)
        serializer = self.get_serializer(rented_ips, many=True)

        response = {
            'count': len(rented_ips),
            'results': serializer.data
        }

        return Response(response)


class IpManagerRentIPsByDatacenter(IpManagerRentIPsBase):
    """
    Rent new IPs by locking them.
    """

    def get(self, request, format=None, *args, **kwargs):
        try:
            datacenter_id = int(request.query_params.get('dc', None))
            ip_version = int(request.query_params.get('v', 4))
            ip_count = int(request.query_params.get('count', 1))

            if not datacenter_id:
                raise ValidationError("Undefined datacenter_id.")

            if ip_count <= 0:
                ip_count = 1

            logger.debug(request.query_params)
            logger.info("Getting %s new ip addresses from datacenter: %s" % (ip_count, datacenter_id))

            renter = IPAddressRenter.from_datacenter(Resource.objects.get(pk=datacenter_id), ip_version=ip_version)

            return self.rent_ips(renter, ip_count)
        except Exception as ex:
            return self.error_response(ex)


class IpManagerRentIPsByPools(IpManagerRentIPsBase):
    """
    Rent new IPs by locking them.
    """

    def get(self, request, format=None, *args, **kwargs):
        try:
            ip_pools = request.query_params.getlist('pool', None)
            ip_count = int(request.query_params.get('count', 1))

            if not ip_pools:
                raise ValueError()

            logger.debug(request.query_params)
            logger.info("Getting %s new ip addresses from pools: %s" % (ip_count, ip_pools))

            renter = IPAddressRenter()
            for pool_id in ip_pools:
                renter.add_source(IPAddressPoolGeneric.objects.get(pk=pool_id))

            return self.rent_ips(renter, ip_count)

        except Exception as ex:
            return self.error_response(ex)
