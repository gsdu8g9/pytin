from __future__ import unicode_literals

from rest_framework import generics
from rest_framework.response import Response
from cmdb.settings import logger

from ipman.serializers import IpAddressSerializer
from resources.models import Resource


class IpPoolNewIPs(generics.RetrieveAPIView):
    queryset = Resource.objects.all()
    serializer_class = IpAddressSerializer

    def get(self, request, pk, format=None, *args, **kwargs):
        ip_pool = self.get_object()
        ip_count = int(request.query_params.get('count', 1))

        logger.info("Getting %s new ip addresses from pool %s" % (ip_count, ip_pool))

        found_ips = []
        for ip in ip_pool.available():
            if not ip_count:
                break

            found_ips.append(ip)
            ip_count -= 1

        serializer = self.get_serializer(found_ips, many=True)

        responce = {
            'count': len(found_ips),
            'items': serializer.data
        }

        return Response(responce)
