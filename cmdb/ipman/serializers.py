from rest_framework import serializers

from ipman.models import IPAddress


class IpAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPAddress
        fields = (
            'id',
            'name',
            'parent',
            'address',
            'version',
            'beauty',
            'type',
            'status',
            'created_at',
            'updated_at',
            'last_seen')
