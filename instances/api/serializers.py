from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

from instances.models import Marvin


class MarvinSerializer(SerializerExtensionsMixin, HyperlinkedModelSerializer):
    class Meta:
        model = Marvin
        fields = ('id',
                  'instance_type',
                  'name', 'hostname',
                  'type', 'version',
                  'browser_name', 'browser_version',
                  'addresses',
                  'first_seen', 'last_seen',
                  '_url')
