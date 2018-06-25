from rest_framework import serializers

from instances.models import Marvin


class MarvinSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Marvin
        fields = ('id', 'instance_type',
                  'name', 'hostname',
                  'type', 'version',
                  'browser_name', 'browser_version',
                  'addresses',
                  '_url')
