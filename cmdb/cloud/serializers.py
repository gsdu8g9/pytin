from __future__ import unicode_literals

from rest_framework import serializers

from assets.models import VirtualServer
from cloud.models import CloudTaskTracker


class CloudTaskTrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CloudTaskTracker
        fields = ('id', 'task_class', 'status', 'created_at', 'updated_at', 'error', 'context_json', 'return_json')


class VirtualServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualServer
        fields = ('id', 'label', 'tech')
