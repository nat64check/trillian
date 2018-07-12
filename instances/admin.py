from django.contrib import admin

from instances.admin_filters import AliveFilter, VersionFilter
from instances.models import Marvin, Zaphod


@admin.register(Marvin)
class MarvinAdmin(admin.ModelAdmin):
    list_display = ('instance_type', 'name', 'type', 'display_version', 'parallel_tasks_limit',
                    'last_seen_display', 'alive')
    list_filter = (AliveFilter, 'instance_type', 'type', VersionFilter)
    search_fields = ('name', 'hostname')


@admin.register(Zaphod)
class ZaphodAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostname')
    search_fields = ('name', 'hostname')
