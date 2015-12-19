from __future__ import unicode_literals

from rest_framework import serializers

from assets.models import VirtualServer
from cloud.models import CloudTaskTracker


class StartStopSerializer(serializers.Serializer):
    vmid = serializers.IntegerField(required=True)
    node = serializers.IntegerField(required=True)
    user = serializers.CharField(max_length=25)

    def validate(self, data):
        if data['vmid'] <= 0:
            raise serializers.ValidationError("vmid must be defined")

        if data['node'] <= 0:
            raise serializers.ValidationError("node must be defined")

        return data


class CloudTaskTrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CloudTaskTracker
        fields = ('id', 'task_class', 'status', 'created_at', 'updated_at', 'error', 'context_json', 'return_json')


class VirtualServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualServer
        fields = ('id', 'label', 'tech')
