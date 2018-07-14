from rest_framework import serializers

from instances.api.serializers import MarvinSerializer
from measurements.models import InstanceRun, InstanceRunResult


class InstanceRunResultsSerializer(serializers.HyperlinkedModelSerializer):
    marvin = MarvinSerializer(read_only=True)

    class Meta:
        model = InstanceRunResult
        fields = ('id', 'instancerun', 'instancerun_id', 'marvin', 'when', 'ping_response', 'web_response', '_url')
        read_only_fields = ('marvin', 'instance_type', 'ping_response', 'web_response')


class NestedInstanceRunResultsSerializer(serializers.HyperlinkedModelSerializer):
    marvin = MarvinSerializer(read_only=True)

    class Meta:
        model = InstanceRunResult
        fields = ('id', 'marvin', 'when', 'ping_response', 'web_response', '_url')
        read_only_fields = ('marvin', 'instance_type', 'ping_response', 'web_response')


class InstanceRunSerializer(serializers.HyperlinkedModelSerializer):
    results = NestedInstanceRunResultsSerializer(many=True, read_only=True)

    class Meta:
        model = InstanceRun
        fields = ('id', 'url',
                  'callback_url', 'callback_auth_code',
                  'requested', 'started', 'finished',
                  'dns_results',
                  'results',
                  '_url')
        read_only_fields = ('started', 'finished', 'dns_results')
