from rest_framework import generics
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from cmdb.settings import logger
from ipman.serializers import IpAddressSerializer
from resources.models import Resource


class IpManagerRentIPs(generics.RetrieveAPIView):
    """
    Rent new IPs by locking them.
    """
    queryset = Resource.objects.all()
    serializer_class = IpAddressSerializer

    class InfiniteList:
        def __init__(self, list):
            if not list:
                raise ValueError('list')

            self.list = list

        def __iter__(self):
            idx = 0
            while True:
                yield self.list[idx % len(self.list)]
                idx += 1

    def get(self, request, format=None, *args, **kwargs):
        ip_pools = request.query_params.getlist('pool', None)
        ip_count = int(request.query_params.get('count', 1))

        if not ip_pools:
            raise ParseError()

        logger.info(request.query_params)
        logger.info("Getting %s new ip addresses from pools: %s" % (ip_count, ip_pools))

        rented_ips = []
        for ip_pool_id in self.InfiniteList(ip_pools):
            if len(rented_ips) >= ip_count:
                break

            ip_pool_resource = Resource.objects.get(pk=ip_pool_id)

            ip = ip_pool_resource.available().next()
            ip.lock()

            rented_ips.append(ip)

            logger.info("    locked IP: %s" % ip)

        serializer = self.get_serializer(rented_ips, many=True)

        responce = {
            'count': len(rented_ips),
            'results': serializer.data
        }

        return Response(responce)
