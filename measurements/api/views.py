from rest_framework.permissions import DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

from measurements.api.serializers import InstanceRunResultsSerializer, InstanceRunSerializer
from measurements.models import InstanceRun, InstanceRunResult


class InstanceRunViewSet(SerializerExtensionsAPIViewMixin, ModelViewSet):
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
    permission_classes = (DjangoModelPermissions,)
    extensions_auto_optimize = True
    extensions_expand_id_only = {'messages', 'results'}
    extensions_exclude = {'results__id',
                          'results__instancerun',
                          'results__instancerun_id',
                          'results___url',
                          'results__marvin__id',
                          'results__marvin___url'}

    def get_extensions_mixin_context(self):
        context = super().get_extensions_mixin_context()
        if self.detail:
            context['expand'] = {'messages', 'results__marvin'}
        return context


class InstanceRunResultsViewSet(ModelViewSet):
    """
    list:
    Retrieve a list of instance run results.

    retrieve:
    Retrieve the details of a single instance run result.
    """
    queryset = InstanceRunResult.objects.all()
    serializer_class = InstanceRunResultsSerializer
    permission_classes = (DjangoModelPermissions,)
