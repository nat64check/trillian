# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

import json
from copy import copy

from django.contrib import admin
from django.contrib.postgres.fields import JSONField
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from prettyjson import PrettyJSONWidget
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from measurements.models import InstanceRun, InstanceRunMessage, InstanceRunResult


class InstanceRunMessageAdmin(admin.TabularInline):
    model = InstanceRunMessage


class InlineInstanceRunResult(admin.TabularInline):
    model = InstanceRunResult
    fields = ('marvin', 'when', 'nice_ping_response', 'nice_web_response', 'data_image')
    readonly_fields = ('marvin', 'when', 'nice_ping_response', 'nice_web_response', 'data_image')
    extra = 0
    can_delete = False
    show_change_link = True

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget(attrs={'initial': 'parsed'})}
    }

    def has_add_permission(self, request):
        return False

    def nice_ping_response(self, instance):
        # Convert the data to sorted, indented JSON
        response = json.dumps(instance.ping_response, indent=2)
        formatter = HtmlFormatter(style='colorful')
        response = highlight(response, JsonLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style><br>"

        # Safe the output
        return mark_safe(style + response)

    nice_ping_response.short_description = _('ping response')

    def nice_web_response(self, instance):
        # Convert the data to sorted, indented JSON
        data = copy(instance.web_response)
        if data:
            if 'image' in data:
                del data['image']
            if 'resources' in data:
                del data['resources']
        response = json.dumps(data, indent=2)
        formatter = HtmlFormatter(style='colorful')
        response = highlight(response, JsonLexer(), formatter)
        style = "<style>" + formatter.get_style_defs() + "</style><br>"

        # Safe the output
        return mark_safe(style + response)

    nice_web_response.short_description = _('web response')

    def data_image(self, instance):
        try:
            return mark_safe('<img style="width: 300px" src="data:image/png;base64,{}">'.format(
                instance.web_response['image']
            ))
        except (KeyError, TypeError, AttributeError):
            return '-'

    data_image.short_description = _('image')


@admin.register(InstanceRun)
class InstanceRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'requested', 'started', 'finished')
    date_hierarchy = 'requested'
    fieldsets = (
        ('Request', {
            'fields': ('url',),
        }),
        ('Callback', {
            'fields': ('callback_url',),
        }),
        ('Timing', {
            'fields': ('requested', 'started', 'finished'),
        }),
        ('DNS', {
            'fields': ('nice_dns_results',),
        }),
    )
    inlines = [InstanceRunMessageAdmin, InlineInstanceRunResult]
    readonly_fields = ('nice_dns_results',)
    search_fields = ('url',)

    def nice_dns_results(self, instance):
        return mark_safe('<br>'.join(instance.dns_results))

    nice_dns_results.short_description = _('dns results')


@admin.register(InstanceRunResult)
class InstanceRunResultAdmin(admin.ModelAdmin):
    list_display = ('instancerun', 'marvin')
    list_filter = (('marvin', admin.RelatedOnlyFieldListFilter),)
    date_hierarchy = 'instancerun__requested'
    search_fields = ('instancerun__url',
                     'marvin_type',
                     'marvin__name',)
    autocomplete_fields = ('instancerun',)
