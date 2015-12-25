from __future__ import unicode_literals

from rest_framework import serializers

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


class CreateVpsSerializer(serializers.Serializer):
    # required
    vmid = serializers.IntegerField(required=True)
    cpu = serializers.IntegerField(required=True)
    ram = serializers.IntegerField(required=True)
    hdd = serializers.IntegerField(required=True)
    user = serializers.CharField(max_length=25, required=True)
    template = serializers.CharField(max_length=100, required=True)

    # optional
    node = serializers.IntegerField(required=False)
    rootpass = serializers.CharField(max_length=55, required=False)

    def validate(self, data):
        if data['vmid'] <= 0:
            raise serializers.ValidationError("vmid must be defined")

        if data['cpu'] <= 0:
            raise serializers.ValidationError("cpu must be defined")

        if data['ram'] <= 0:
            raise serializers.ValidationError("ram must be defined")

        if data['hdd'] <= 0:
            raise serializers.ValidationError("hdd must be defined")

        if not data['template']:
            raise serializers.ValidationError("template must be defined")

        if 'node' in data and data['node'] <= 0:
            raise serializers.ValidationError("node must be >= 0")

        return data


class CloudTaskTrackerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CloudTaskTracker
        fields = ('id', 'task_class', 'status', 'created_at', 'updated_at', 'error', 'context_json', 'return_json')

    def to_representation(self, instance):
        assert instance

        # refresh tracker state
        instance.poll()

        return super(CloudTaskTrackerSerializer, self).to_representation(instance)
