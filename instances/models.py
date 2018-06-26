from django.contrib.gis.db import models
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.core.validators import RegexValidator, URLValidator
from django.utils.translation import gettext_lazy as _


class Marvin(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    hostname = models.CharField(_('hostname'), max_length=127, validators=[
        RegexValidator(URLValidator.host_re, message=_("Please provide a valid host name"))
    ])
    type = models.CharField(_('type'), max_length=50)
    version = ArrayField(models.PositiveSmallIntegerField(), verbose_name=_('version'))

    browser_name = models.CharField(_('browser name'), max_length=150)
    browser_version = ArrayField(models.PositiveSmallIntegerField(), verbose_name=_('browser version'))

    instance_type = models.CharField(_('instance type'), max_length=10, choices=[
        ('v4only', _('IPv4-only')),
        ('v6only', _('IPv6-only')),
        ('nat64', _('IPv6 with NAT64')),
    ])
    addresses = ArrayField(models.GenericIPAddressField(), verbose_name=_('addresses'), default=list)

    first_seen = models.DateTimeField(_('first seen'), auto_now_add=True)
    last_seen = models.DateTimeField(_('last seen'))

    alive = models.BooleanField(_('alive'), default=True)
    parallel_tasks_limit = models.PositiveIntegerField(_('parallel tasks limit'))

    class Meta:
        ordering = ('-alive', 'instance_type', '-last_seen')

    def __str__(self):
        return '{name} ({type}: {alive})'.format(name=self.name,
                                                 type=self.instance_type,
                                                 alive=self.alive and _('alive') or _('dead'))

    @property
    def cache_key(self):
        return 'marvin_{}'.format(self.name)

    @property
    def tasks(self):
        return cache.get(self.cache_key, 0)

    @tasks.setter
    def tasks(self, value):
        cache.set(self.cache_key, value)

    def __enter__(self):
        key = self.cache_key
        cache.add(key, 0)
        cache.incr(key)

    def __exit__(self, exc_type, exc_val, exc_tb):
        key = self.cache_key
        cache.add(key, 1)
        cache.decr(key)

    def display_version(self):
        return '.'.join(map(str, self.version))

    display_version.short_description = _('version')
    display_version.admin_order_field = 'version'

    def display_browser_version(self):
        return '.'.join(map(str, self.browser_version))

    display_browser_version.short_description = _('browser version')
    display_browser_version.admin_order_field = 'browser_version'

    def last_seen_display(self):
        return naturaltime(self.last_seen)

    last_seen_display.short_description = _('last seen')
    last_seen_display.admin_order_field = 'last_seen'
