from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from measurements.models import InstanceRun
from measurements.tasks.runner import execute_instancerun


@receiver(post_save, sender=InstanceRun, dispatch_uid='schedule_execution')
def schedule_execution(instance: InstanceRun, **kwargs):
    if instance.started:
        return

    execute_instancerun.setup['at'] = max(instance.requested,
                                          timezone.now() + timedelta(seconds=5))
    execute_instancerun(instance.pk)
