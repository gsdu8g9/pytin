from rest_framework import serializers

from resources.models import Resource, ResourceOption


class ResourceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceOption
        fields = ('id', 'name', 'value', 'namespace', 'format', 'updated_at')


class ResourceSerializer(serializers.ModelSerializer):
    options = ResourceOptionSerializer(source='resourceoption_set', many=True, required=False)

    class Meta:
        model = Resource
        fields = (
            'id', 'name', 'parent', 'type', 'status', 'created_at', 'updated_at', 'last_seen', 'options')
