from rest_framework import serializers

from instances.models import Marvin


class PlainMarvinSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Marvin
        fields = ('instance_type',
                  'name', 'hostname',
                  'type', 'version',
                  'browser_name', 'browser_version',
                  'addresses',
                  'first_seen', 'last_seen')


class MarvinSerializer(PlainMarvinSerializer):
    class Meta(PlainMarvinSerializer.Meta):
        fields = ('id',) + PlainMarvinSerializer.Meta.fields + ('_url',)
