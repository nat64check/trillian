from rest_framework import serializers

from measurements.models import InstanceRun, InstanceRunResult


class InstanceRunResultsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InstanceRunResult
        fields = ('id', 'instancerun', 'instancerun_id', 'marvin', 'marvin_id',
                  'when', 'instance_type', 'ping_response', 'web_response', '_url')
        read_only_fields = ('marvin', 'instance_type', 'ping_response', 'web_response')


class NestedInstanceRunResultsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InstanceRunResult
        fields = ('id', 'marvin', 'marvin_id', 'when', 'instance_type', 'ping_response', 'web_response', '_url')
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
