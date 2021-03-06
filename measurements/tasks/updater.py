# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

import sys
from traceback import print_exc
from urllib.parse import urlsplit

import requests
from django.utils.translation import gettext_lazy as _
from requests.auth import AuthBase
from uwsgi_tasks import RetryTaskException, task

from generic.utils import print_error, print_message, print_warning, retry_get
from instances.models import Zaphod
from measurements.api.serializers import InstanceRunSerializer


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
        run = retry_get(InstanceRun.objects.all(), pk=pk)
        if not run.callback_url:
            print_warning(_("No callback URL provided for InstanceRun {pk}").format(pk=pk))
            return

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
            json=InstanceRunSerializer(instance=run, context={
                'expand': {
                    'messages',
                    'results__marvin'
                },
                'exclude': {
                    'id',
                    '_url',
                    'results__id',
                    'results__instancerun',
                    'results__instancerun_id',
                    'results___url',
                    'results__marvin__id',
                    'results__marvin___url'
                }
            }).data
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
        print_exc()

        raise RetryTaskException
