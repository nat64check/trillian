import base64
import io
import ipaddress
import logging
import socket
import sys
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from random import randrange
from traceback import format_exc
from urllib.parse import urlparse

import requests
import skimage.io
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, gettext_noop
from requests_futures.sessions import FuturesSession
from skimage.measure import compare_ssim
from uwsgi_tasks import RetryTaskException, get_current_task, task

from generic.utils import print_error, print_message, print_notice, print_warning, retry_get
from instances.models import Marvin
from measurements.models import InstanceRunMessage


# noinspection PyTypeChecker
def compare_base64_images(img1_b64, img2_b64):
    img1_bytes = base64.decodebytes(img1_b64.encode('ascii'))
    img1 = skimage.io.imread(io.BytesIO(img1_bytes))

    img2_bytes = base64.decodebytes(img2_b64.encode('ascii'))
    img2 = skimage.io.imread(io.BytesIO(img2_bytes))

    return compare_ssim(img1, img2, multichannel=True)


def get_eligible_marvins():
    # Find eligible Marvins
    marvins = Marvin.objects.filter(is_alive=True)
    possible_marvins = []
    for marvin in marvins:
        tasks = marvin.tasks
        if tasks < marvin.parallel_tasks_limit:
            possible_marvins.append((tasks, marvin))

    # Sort them by tasks
    possible_marvins.sort(key=lambda m: m[0])

    return [marvin[1] for marvin in possible_marvins]


def find_marvins(instance_types):
    # Prepare the output
    found = {}
    for instance_type in instance_types:
        found[instance_type] = None

    marvins = get_eligible_marvins()
    for marvin in marvins:
        # Skip if we don't need this type or if we already found one
        if marvin.instance_type not in instance_types or found[marvin.instance_type]:
            continue

        found[marvin.instance_type] = marvin

        # Stop if we found everything we need
        if all(found.values()):
            break

    return found


def get_marvins(instance_types):
    # We should now be the only spooler running this task
    marvins = find_marvins(instance_types)
    if not all(marvins.values()):
        timeout = randrange(5, 60)
        print_error(_("Not enough Marvins available, missing {types}: delaying by {timeout} seconds").format(
            types=[instance_type for instance_type, marvin in marvins.items() if marvin is None],
            timeout=timeout
        ))
        # Retry without lowering the retry count
        current_task = get_current_task()
        raise RetryTaskException(count=current_task.setup['retry_count'], timeout=timeout)

    print_message(_("Found Marvins: {}").format(', '.join(['{}: {}'.format(instance_type, marvin.name)
                                                           for instance_type, marvin in marvins.items()])))

    return marvins


@task(retry_count=5, retry_timeout=300)
def execute_instancerun(pk):
    from measurements.models import InstanceRun, InstanceRunResult

    try:
        # Make sure we need to start and we don't start twice
        with transaction.atomic():
            run = retry_get(InstanceRun.objects.select_for_update(), pk=pk)
            if run.started:
                print_notice(_('InstanceRun {pk} has already started, skipping').format(pk=pk))
                return

            now = timezone.now()
            if run.requested > now:
                print_notice(_('InstanceRun {pk} is requested to start in the future, skipping').format(pk=pk))
                return

            # We are starting!
            run.started = now
            run.save()

        # Do a simple DNS lookup
        addresses = []
        for info in socket.getaddrinfo(urlparse(run.url).hostname, port=80, proto=socket.IPPROTO_TCP):
            family, socktype, proto, canonname, sockaddr = info
            addresses.append(sockaddr[0])

        run.dns_results = addresses

        # Log which instancerun we're working on
        print_message(_("Start working on InstanceRun {run.pk} ({run.url})").format(run=run))

        # First determine a baseline
        marvin = get_marvins(['dual-stack'])['dual-stack']
        with marvin:
            response = requests.request(
                method='POST',
                url='http://{}:3001/browse'.format(marvin.name),
                json={
                    'url': run.url,
                },
                timeout=(5, 65)
            )
            if response.status_code != 200:
                timeout = randrange(5, 120)
                print_error(_("Baseline test failed, retrying in {timeout} seconds").format(
                    timeout=timeout
                ))
                raise RetryTaskException(timeout=timeout)

            baseline = response.json()

        instance_types = ['v4only', 'v6only', 'nat64', 'dual-stack']
        marvins = get_marvins(instance_types)

        with FuturesSession(executor=ThreadPoolExecutor(max_workers=len(marvins))) as session:
            with ExitStack() as stack:
                # Signal usage of Marvins
                for marvin in marvins.values():
                    stack.enter_context(marvin)

                # Start requests
                browse_requests = {}
                for instance_type, marvin in marvins.items():
                    browse_requests[instance_type] = session.request(
                        method='POST',
                        url='http://{}:3001/browse'.format(marvin.name),
                        json={
                            'url': run.url,
                        },
                        timeout=(5, 65)
                    )

                ping_requests = {}
                for instance_type, marvin in marvins.items():
                    family = 4 if instance_type == 'v4only' else 6
                    ping_requests[instance_type] = session.request(
                        method='POST',
                        url='http://{}:3001/ping{}'.format(marvin.name, family),
                        json={
                            'target': urlparse(run.url).hostname,
                        },
                        timeout=(5, 65)
                    )

                # Wait for all the responses to come back in
                browse_responses = {}
                for instance_type, request in browse_requests.items():
                    browse_responses[instance_type] = request.result()

                ping_responses = {}
                for instance_type, request in ping_requests.items():
                    ping_responses[instance_type] = request.result()

            # Check if all tests succeeded
            if not all([response.status_code == 200
                        for response in list(browse_responses.values()) + list(ping_responses.values())]):
                timeout = randrange(5, 120)
                print_error(_("Not all tests completed successfully, retrying in {timeout} seconds").format(
                    timeout=timeout
                ))
                raise RetryTaskException(timeout=timeout)

            # Parse all JSON
            ping_responses = {instance_type: response.json(object_pairs_hook=OrderedDict)
                              for instance_type, response in ping_responses.items()}
            browse_responses = {instance_type: response.json(object_pairs_hook=OrderedDict)
                                for instance_type, response in browse_responses.items()}

            # Compare dual-stack to the baseline
            if len(baseline['resources']) != len(browse_responses['dual-stack']['resources']) or \
                    compare_base64_images(baseline['image'], browse_responses['dual-stack']['image']) < 0.98:
                InstanceRunMessage.objects.create(
                    instancerun=run,
                    severity=logging.WARNING,
                    message='Two identical requests returned different results. Results are going to be unpredictable.',
                )

            for instance_type in instance_types:
                InstanceRunResult.objects.update_or_create(
                    defaults={
                        'ping_response': ping_responses[instance_type],
                        'web_response': browse_responses[instance_type],
                    },
                    instancerun=run,
                    marvin=marvins[instance_type],
                )

        # We are starting!
        run.finished = timezone.now()
        run.save()

        print_message(_("Work on InstanceRun {run.pk} ({run.url}) completed").format(run=run))

    except RetryTaskException:
        # Clear the started timestamp and messages so it can be retried, and trigger retry
        InstanceRun.objects.filter(pk=pk).update(started=None, finished=None)
        InstanceRunMessage.objects.filter(instancerun_id=pk).delete()
        raise

    except InstanceRun.DoesNotExist:
        print_warning(_("InstanceRun {pk} does not exist anymore").format(pk=pk))
        return

    except Exception as ex:
        print_error(_('{name} on line {line}: {msg}').format(name=type(ex).__name__,
                                                             line=sys.exc_info()[-1].tb_lineno,
                                                             msg=ex))

        # Clear the started timestamp and messages so it can be retried, and trigger retry
        InstanceRun.objects.filter(pk=pk).update(started=None, finished=None)
        InstanceRunMessage.objects.filter(instancerun_id=pk).delete()
        raise RetryTaskException
