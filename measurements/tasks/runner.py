# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Copyright (c) 2018, S.J.M. Steffann. This software is licensed under the BSD
#  3-Clause License. Please see the LICENSE file in the project root directory.
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

import base64
import io
import ipaddress
import logging
import socket
import sys
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from ipaddress import IPv6Address
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


def get_marvins(instance_types, current_task):
    # We should now be the only spooler running this task
    marvins = find_marvins(instance_types)
    if not all(marvins.values()):
        timeout = randrange(5, 60)
        print_error(_("Not enough Marvins available, missing {types}: delaying by {timeout} seconds").format(
            types=[instance_type for instance_type, marvin in marvins.items() if marvin is None],
            timeout=timeout
        ))
        # Retry without lowering the retry count
        raise RetryTaskException(count=current_task.setup['retry_count'], timeout=timeout)

    print_message(_("Found Marvins: {}").format(', '.join(['{}: {}'.format(instance_type, marvin.name)
                                                           for instance_type, marvin in marvins.items()])))

    return marvins


@task(retry_count=5, retry_timeout=300)
def execute_instancerun(pk):
    from measurements.models import InstanceRun, InstanceRunResult

    current_task = get_current_task()

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

        # Log which instancerun we're working on
        print_message(_("Start working on InstanceRun {run.pk} ({run.url})").format(run=run))

        # Do a simple DNS lookup
        addresses = set()
        for info in socket.getaddrinfo(urlparse(run.url).hostname, port=80, proto=socket.IPPROTO_TCP):
            family, socktype, proto, canonname, sockaddr = info
            addresses.add(ipaddress.ip_address(sockaddr[0]))

        run.dns_results = list([str(address) for address in addresses])

        # First determine a baseline
        marvin = get_marvins(['dual-stack'], current_task)['dual-stack']
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

        # Determine which protocols to check
        site_v4_addresses = [address for address in addresses if address.version == 4]
        site_v6_addresses = [address for address in addresses if address.version == 6]
        instance_types = {'nat64', 'dual-stack'}
        if site_v4_addresses:
            instance_types.add('v4only')
        else:
            InstanceRunMessage.objects.create(
                instancerun=run,
                severity=logging.WARNING,
                message=gettext_noop('This website has no IPv4 addresses so the IPv4-only test is skipped'),
            )

        if site_v6_addresses:
            instance_types.add('v6only')
        else:
            InstanceRunMessage.objects.create(
                instancerun=run,
                severity=logging.WARNING,
                message=gettext_noop('This website has no IPv6 addresses so the IPv6-only test is skipped'),
            )

        marvins = get_marvins(instance_types, current_task)

        with FuturesSession(executor=ThreadPoolExecutor(max_workers=2 * len(marvins))) as session:
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
                            'timeout': 30,
                        },
                        timeout=(5, 65)
                    )

                ping_requests = {}
                for instance_type, marvin in marvins.items():
                    marvin_has_v4 = instance_type in ('v4only', 'dual-stack')
                    marvin_has_nat64 = instance_type in ('nat64',)
                    marvin_has_v6 = instance_type in ('v6only', 'dual-stack', 'nat64')

                    if marvin_has_v4:
                        for address in site_v4_addresses:
                            address_str = str(address)
                            ping_requests.setdefault(instance_type, {})[address_str] = session.request(
                                method='POST',
                                url='http://{}:3001/ping4'.format(marvin.name),
                                json={'target': address_str},
                                timeout=(5, 65)
                            )

                    if marvin_has_nat64:
                        for address in site_v4_addresses:
                            address_str = str(IPv6Address('64:ff9b::') + int(address))
                            ping_requests.setdefault(instance_type, {})[address_str] = session.request(
                                method='POST',
                                url='http://{}:3001/ping6'.format(marvin.name),
                                json={'target': address_str},
                                timeout=(5, 65)
                            )

                    if marvin_has_v6:
                        for address in site_v6_addresses:
                            address_str = str(address)
                            ping_requests.setdefault(instance_type, {})[address_str] = session.request(
                                method='POST',
                                url='http://{}:3001/ping6'.format(marvin.name),
                                json={'target': address_str},
                                timeout=(5, 65)
                            )

                # Wait for all the responses to come back in
                browse_responses = {}
                for instance_type, request in browse_requests.items():
                    browse_responses[instance_type] = request.result()

                ping_responses = {}
                for instance_type, address_requests in ping_requests.items():
                    for address, request in address_requests.items():
                        ping_responses[(instance_type, address)] = request.result()

            for req, response in list(browse_responses.items()) + list(ping_responses.items()):
                if response.status_code >= 300:
                    print_error("{req} {url} ({code}): {json}".format(code=response.status_code,
                                                                      req=req,
                                                                      url=response.url,
                                                                      json=response.json()))

            # Check if all tests succeeded
            if not all([response.status_code == 200
                        for response in list(browse_responses.values()) + list(ping_responses.values())]):
                timeout = randrange(5, 120)
                print_error(_("Not all tests completed successfully, retrying in {timeout} seconds").format(
                    timeout=timeout
                ))
                raise RetryTaskException(timeout=timeout)

            # Parse all JSON
            ping_responses_json = {}
            for (instance_type, address), response in ping_responses.items():
                ping_responses_json.setdefault(instance_type, {})
                ping_responses_json[instance_type][address] = response.json(object_pairs_hook=OrderedDict)
            browse_responses_json = {instance_type: response.json(object_pairs_hook=OrderedDict)
                                     for instance_type, response in browse_responses.items()}

            # Compare dual-stack to the baseline
            if len(baseline['resources']) != len(browse_responses_json['dual-stack']['resources']) or \
                    compare_base64_images(baseline['image'], browse_responses_json['dual-stack']['image']) < 0.98:
                InstanceRunMessage.objects.create(
                    instancerun=run,
                    severity=logging.WARNING,
                    message=gettext_noop('Two identical requests returned different results. '
                                         'Results are going to be unpredictable.'),
                )

            for instance_type in instance_types:
                InstanceRunResult.objects.update_or_create(
                    defaults={
                        'ping_response': ping_responses_json[instance_type],
                        'web_response': browse_responses_json[instance_type],
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
        print_error(format_exc())

        # Clear the started timestamp and messages so it can be retried, and trigger retry
        InstanceRun.objects.filter(pk=pk).update(started=None, finished=None)
        InstanceRunMessage.objects.filter(instancerun_id=pk).delete()
        raise RetryTaskException
