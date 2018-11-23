# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

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
    title = _('is alive')
    parameter_name = 'is_alive'

    def lookups(self, request, model_admin):
        return (
            ('all', _('All')),
            ('', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        is_alive = self.value() or ''
        if is_alive == 'all':
            return queryset
        elif is_alive == 'no':
            return queryset.filter(is_alive=False)
        else:
            return queryset.filter(is_alive=True)

    def choices(self, cl):
        is_alive = self.value() or ''

        for lookup, title in self.lookup_choices:
            if lookup:
                yield {
                    'selected': is_alive == force_text(lookup),
                    'query_string': cl.get_query_string({
                        self.parameter_name: lookup,
                    }, []),
                    'display': title,
                }
            else:
                yield {
                    'selected': is_alive == force_text(lookup),
                    'query_string': cl.get_query_string({}, [self.parameter_name]),
                    'display': title,
                }
