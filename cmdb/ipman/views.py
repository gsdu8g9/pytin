from rest_framework import generics
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from cmdb.settings import logger
from ipman.models import IPAddressPool
from ipman.serializers import IpAddressSerializer
from resources.models import Resource


class IpManagerRentIPs(generics.RetrieveAPIView):
    """
    Rent new IPs by locking them.
    """
    queryset = Resource.objects.all()
    serializer_class = IpAddressSerializer

    def get(self, request, format=None, *args, **kwargs):
        ip_pools = request.query_params.getlist('pool', None)
        ip_count = int(request.query_params.get('count', 1))

        if not ip_pools:
            raise ParseError()

        logger.info(request.query_params)
        logger.info("Getting %s new ip addresses from pools: %s" % (ip_count, ip_pools))

        rented_ips = IPAddressPool.globally_available(ip_pools, ip_count)

        serializer = self.get_serializer(rented_ips, many=True)

        response = {
            'count': len(rented_ips),
            'results': serializer.data
        }

        return Response(response)
