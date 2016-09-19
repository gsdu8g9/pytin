from __future__ import unicode_literals

from rest_framework import serializers

from ipman.models import IPAddressGeneric


class IpAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPAddressGeneric
        fields = (
            'id',
            'pool',
            'parent',
            'address',
            'status',
            'created_at',
            'updated_at',
            'last_seen',
            'main'
        )
