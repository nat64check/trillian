# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

from rest_framework import viewsets

from instances.api.filters import MarvinFilter
from instances.api.serializers import MarvinSerializer
from instances.models import Marvin


class MarvinViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Retrieve a list of Marvins.
    Whenever a Marvin is updated a new object will be created so that old tests can keep referring to the Marvin
    as it was when running the test. Therefore multiple Marvins with the same name can appear in the list.

    retrieve:
    Retrieve the details of a single Marvin.
    """
    queryset = Marvin.objects.all()
    serializer_class = MarvinSerializer
    filter_class = MarvinFilter
