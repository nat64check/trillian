from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from measurements.models import InstanceRun
from measurements.tasks import execute_instancerun, execute_update_zaphod


# noinspection PyUnusedLocal
@receiver(post_save, sender=InstanceRun, dispatch_uid='schedule_execution')
def schedule_execution(instance: InstanceRun, **kwargs):
    if instance.started:
        return

    # Schedule execution for the spooler
    execute_instancerun.setup['at'] = max(instance.requested,
                                          timezone.now() + timedelta(seconds=1))
    execute_instancerun(instance.pk)


# noinspection PyUnusedLocal
@receiver(post_save, sender=InstanceRun, dispatch_uid='schedule_updater')
def schedule_updater(instance: InstanceRun, **kwargs):
    # Schedule update in the spooler
    execute_update_zaphod.setup['at'] = timezone.now() + timedelta(seconds=1)
    execute_update_zaphod(instance.pk)
