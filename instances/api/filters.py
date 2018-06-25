import django_filters

from instances.models import Marvin


class CharArrayFilter(django_filters.BaseCSVFilter, django_filters.CharFilter):
    pass


class MarvinFilter(django_filters.FilterSet):
    address = CharArrayFilter(name='addresses', lookup_expr='contains')

    class Meta:
        model = Marvin
        fields = {
            'name': ['exact', 'contains'],
            'hostname': ['exact', 'contains'],
            'type': ['exact'],
            'instance_type': ['exact'],
        }
