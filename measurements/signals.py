from django.db.models.signals import post_save
from django.dispatch import receiver

from measurements.models import InstanceRun
from measurements.tasks.runner import execute_instancerun


@receiver(post_save, sender=InstanceRun, dispatch_uid='schedule_execution')
def schedule_execution(instance: InstanceRun, **kwargs):
    if instance.started:
        return

    execute_instancerun.setup['at'] = instance.requested
    execute_instancerun(instance.pk)
