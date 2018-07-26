import django_filters

from instances.models import Marvin


class CharArrayFilter(django_filters.BaseCSVFilter, django_filters.CharFilter):
    pass


class MarvinFilter(django_filters.FilterSet):
    address = CharArrayFilter(name='addresses', lookup_expr='icontains')

    class Meta:
        model = Marvin
        fields = {
            'name': ['exact', 'icontains'],
            'hostname': ['exact', 'icontains'],
            'type': ['exact'],
            'instance_type': ['exact'],
        }
