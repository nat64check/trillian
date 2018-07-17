from rest_framework import serializers

from instances.api.serializers import PlainMarvinSerializer
from measurements.models import InstanceRun, InstanceRunMessage, InstanceRunResult


class InstanceRunResultsSerializer(serializers.HyperlinkedModelSerializer):
    marvin = PlainMarvinSerializer(read_only=True)

    class Meta:
        model = InstanceRunResult
        fields = ('id', 'instancerun', 'instancerun_id', 'marvin', 'when', 'ping_response', 'web_response', '_url')
        read_only_fields = ('marvin', 'instance_type', 'ping_response', 'web_response')


class PlainInstanceRunResultsSerializer(serializers.HyperlinkedModelSerializer):
    marvin = PlainMarvinSerializer(read_only=True)

    class Meta:
        model = InstanceRunResult
        fields = ('marvin', 'when', 'ping_response', 'web_response')


class PlainInstanceRunMessageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InstanceRunMessage
        fields = ('severity', 'message')


class PlainInstanceRunSerializer(serializers.HyperlinkedModelSerializer):
    results = PlainInstanceRunResultsSerializer(many=True, read_only=True)
    messages = PlainInstanceRunMessageSerializer(many=True, read_only=True)

    class Meta:
        model = InstanceRun
        fields = ('url',
                  'callback_url',
                  'requested', 'started', 'finished',
                  'dns_results',
                  'results', 'messages')
        read_only_fields = ('started', 'finished', 'dns_results')


class InstanceRunSerializer(PlainInstanceRunSerializer):
    class Meta(PlainInstanceRunSerializer.Meta):
        fields = ('id',) + PlainInstanceRunSerializer.Meta.fields + ('_url',)
