# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

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
