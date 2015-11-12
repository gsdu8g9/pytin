from __future__ import unicode_literals

from rest_framework import serializers

from cmdb.settings import logger
from resources.models import Resource, ResourceOption


class ResourceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceOption
        fields = ('id', 'name', 'value', 'format', 'updated_at')


class ResourceSerializer(serializers.ModelSerializer):
    options = ResourceOptionSerializer(source='resourceoption_set', many=True, required=False)

    class Meta:
        model = Resource
        fields = (
            'id', 'name', 'parent', 'type', 'status', 'created_at', 'updated_at', 'last_seen', 'options')

    def update(self, instance, validated_data):
        options_list = validated_data.pop('resourceoption_set', [])

        logger.debug(options_list)

        resource, created = Resource.active.update_or_create(
            id=instance.id,
            defaults=validated_data
        )

        for option_item in options_list:
            ResourceOption.objects.update_or_create(
                name=option_item['name'],
                resource=resource,
                defaults=option_item,
            )

        resource.refresh_from_db()

        return resource

    def create(self, validated_data):
        options_list = validated_data.pop('resourceoption_set')
        resource = Resource.objects.create(**validated_data)

        for option_item in options_list:
            ResourceOption.objects.update_or_create(
                name=option_item['name'],
                resource=resource,
                defaults=option_item
            )

        return resource
