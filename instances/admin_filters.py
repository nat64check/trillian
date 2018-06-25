from django.contrib import admin
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _


class VersionFilter(admin.SimpleListFilter):
    title = _('version')
    parameter_name = 'version'
    field_name = 'version'

    def lookups(self, request, model_admin):
        versions = model_admin.model.objects.values_list(self.field_name, flat=True).distinct().order_by('version')
        for version_numbers in versions:
            version = '.'.join(map(str, version_numbers))
            yield (version, version)

    def queryset(self, request, queryset):
        version_str = self.value()
        if not version_str:
            return queryset

        version_numbers = map(int, version_str.split('.'))
        return queryset.filter(**{self.field_name: version_numbers})


class AliveFilter(admin.SimpleListFilter):
    title = _('alive')
    parameter_name = 'alive'

    def lookups(self, request, model_admin):
        return (
            ('all', _('All')),
            ('', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        alive = self.value() or ''
        if alive == 'all':
            return queryset
        elif alive == 'no':
            return queryset.filter(alive=False)
        else:
            return queryset.filter(alive=True)

    def choices(self, cl):
        alive = self.value() or ''

        for lookup, title in self.lookup_choices:
            if lookup:
                yield {
                    'selected': alive == force_text(lookup),
                    'query_string': cl.get_query_string({
                        self.parameter_name: lookup,
                    }, []),
                    'display': title,
                }
            else:
                yield {
                    'selected': alive == force_text(lookup),
                    'query_string': cl.get_query_string({}, [self.parameter_name]),
                    'display': title,
                }
