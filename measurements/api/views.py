from rest_framework import permissions, viewsets

from measurements.api.serializers import InstanceRunResultsSerializer, InstanceRunSerializer
from measurements.models import InstanceRun, InstanceRunResult


class InstanceRunViewSet(viewsets.ModelViewSet):
    """
    list:
    Retrieve a list of instance runs.

    create:
    Request a new instance run.

    retrieve:
    Retrieve the details of a single instance run.

    update:
    Update all the properties of an instance run.

    partial_update:
    Change one or more properties of an instance run.

    destroy:
    Remove an instance run.
    """
    queryset = InstanceRun.objects.all()
    serializer_class = InstanceRunSerializer
    permission_classes = (permissions.DjangoModelPermissions,)


class InstanceRunResultsViewSet(viewsets.ModelViewSet):
    """
    list:
    Retrieve a list of instance run results.

    retrieve:
    Retrieve the details of a single instance run result.
    """
    queryset = InstanceRunResult.objects.all()
    serializer_class = InstanceRunResultsSerializer
    permission_classes = (permissions.DjangoModelPermissions,)
