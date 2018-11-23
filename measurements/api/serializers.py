# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

from instances.api.serializers import MarvinSerializer
from measurements.models import InstanceRun, InstanceRunMessage, InstanceRunResult


class InstanceRunResultsSerializer(SerializerExtensionsMixin, HyperlinkedModelSerializer):
    class Meta:
        model = InstanceRunResult
        fields = ('id', 'instancerun', 'instancerun_id', 'marvin', 'when', 'ping_response', 'web_response', '_url')
        read_only_fields = ('marvin', 'instance_type', 'ping_response', 'web_response')
        expandable_fields = dict(
            marvin=dict(
                serializer=MarvinSerializer,
                read_only=True,
            )
        )


class InstanceRunMessageSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = InstanceRunMessage
        fields = ('severity', 'message')


class InstanceRunSerializer(SerializerExtensionsMixin, HyperlinkedModelSerializer):
    class Meta:
        model = InstanceRun
        fields = ('id',
                  'url',
                  'callback_url',
                  'requested', 'started', 'finished',
                  'dns_results',
                  '_url')
        read_only_fields = ('started', 'finished', 'dns_results')
        expandable_fields = dict(
            results=dict(
                serializer=InstanceRunResultsSerializer,
                many=True,
                read_only=True,
            ),
            messages=dict(
                serializer=InstanceRunMessageSerializer,
                many=True,
                read_only=True,
            ),
        )
