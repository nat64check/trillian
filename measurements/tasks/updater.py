import sys
from urllib.parse import urlsplit

import requests
from django.utils.translation import gettext_lazy as _
from requests.auth import AuthBase
from uwsgi_tasks import RetryTaskException, task

from instances.models import Zaphod
from measurements.api.serializers import PlainInstanceRunSerializer
from measurements.tasks.utils import print_error, print_message, print_warning


class TokenAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, req):
        req.headers['Authorization'] = 'Token {}'.format(self.token)
        return req


@task(retry_count=5, retry_timeout=300)
def execute_update_zaphod(pk):
    from measurements.models import InstanceRun

    try:
        run = InstanceRun.objects.get(pk=pk)
        if not run.callback_url:
            print_warning(_("No callback URL provided for InstanceRun {pk}").format(pk=pk))

        print_message(_("Updating InstanceRun {run.pk} ({run.url}) on {run.callback_url}").format(run=run))

        url = urlsplit(run.callback_url)
        try:
            zaphod = Zaphod.objects.get(hostname=url.netloc)
            auth = TokenAuth(zaphod.token)
        except Zaphod.DoesNotExist:
            print_warning(_("Unknown Zaphod at {url.netloc}, not authenticating").format(url=url))
            auth = None

        response = requests.request(
            method='PUT',
            url=run.callback_url,
            auth=auth,
            timeout=(5, 15),
            json=PlainInstanceRunSerializer(instance=run, context={'request': None}).data
        )

        if response.status_code != 200:
            print_error(_("{run.callback_url} didn't accept our data ({response.status_code}), retrying later").format(
                run=run,
                response=response
            ))
            raise RetryTaskException

    except RetryTaskException:
        raise

    except InstanceRun.DoesNotExist:
        print_warning(_("InstanceRun {pk} does not exist anymore").format(pk=pk))
        return

    except Exception as ex:
        print_error(_('{name} on line {line}: {msg}').format(
            name=type(ex).__name__,
            line=sys.exc_info()[-1].tb_lineno,
            msg=ex
        ))

        raise RetryTaskException
