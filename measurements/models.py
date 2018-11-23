# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

import logging

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from instances.models import Marvin

severities = (
    (logging.CRITICAL, _('Critical')),
    (logging.ERROR, _('Error')),
    (logging.WARNING, _('Warning')),
    (logging.INFO, _('Info')),
    (logging.DEBUG, _('Debug')),
)


class InstanceRun(models.Model):
    url = models.URLField(_('URL'), db_index=True)

    callback_url = models.URLField(_('Callback URL'), blank=True)

    requested = models.DateTimeField(_('requested'), db_index=True)
    started = models.DateTimeField(_('started'), blank=True, null=True, db_index=True)
    finished = models.DateTimeField(_('finished'), blank=True, null=True, db_index=True)

    dns_results = ArrayField(models.GenericIPAddressField(), verbose_name=_('DNS results'), blank=True, default=list)

    class Meta:
        verbose_name = _('instance run')
        verbose_name_plural = _('instance runs')
        ordering = ('requested', 'started', 'finished')

    def __str__(self):
        if self.finished:
            return _('{url} completed on {when}').format(url=self.url,
                                                         when=date_format(self.finished, 'DATETIME_FORMAT'))
        elif self.started:
            return _('{url} started on {when}').format(url=self.url,
                                                       when=date_format(self.started, 'DATETIME_FORMAT'))
        else:
            return _('{url} requested on {when}').format(url=self.url,
                                                         when=date_format(self.requested, 'DATETIME_FORMAT'))


class InstanceRunMessage(models.Model):
    instancerun = models.ForeignKey(InstanceRun, verbose_name=_('instance run'), related_name='messages',
                                    on_delete=models.CASCADE)
    severity = models.PositiveSmallIntegerField(_('severity'), choices=severities)
    message = models.CharField(_('message'), max_length=200)

    class Meta:
        verbose_name = _('instance run message')
        verbose_name_plural = _('instance run messages')
        ordering = ('instancerun', '-severity')

    def __str__(self):
        return '{obj.instancerun}: {obj.message} [{obj.severity}]'.format(obj=self)


class InstanceRunResult(models.Model):
    instancerun = models.ForeignKey(InstanceRun, verbose_name=_('instance run'), related_name='results',
                                    on_delete=models.CASCADE)
    marvin = models.ForeignKey(Marvin, verbose_name=_('Marvin'), on_delete=models.PROTECT)

    when = models.DateTimeField(auto_now_add=True)

    ping_response = JSONField()
    web_response = JSONField()

    class Meta:
        verbose_name = _('instance run result')
        verbose_name_plural = _('instance run results')

    def __str__(self):
        return _('{obj.instancerun} on {obj.marvin}').format(obj=self)

    @property
    def instance_type(self):
        return self.marvin.instance_type
