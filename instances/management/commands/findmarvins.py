import socket

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache

from instances.models import Marvin


class Command(BaseCommand):
    help = 'Scan for marvins'

    def handle(self, *args, **options):
        marvins = set()

        for info in socket.getaddrinfo('marvin', port=3001, proto=socket.IPPROTO_TCP):
            family, socktype, proto, canonname, sockaddr = info

            try:
                address, port = sockaddr[0:2]
                hostname = socket.gethostbyaddr(address)[0]

                if family == socket.AF_INET6:
                    address = '[{address}]'.format(address=address)
                response = requests.get('http://{address}:{port}/info'.format(address=address, port=port)).json()

                name = response['name']
                if name in marvins:
                    # We have already seen this Marvin
                    continue

                marvin, created = Marvin.objects.update_or_create(defaults={
                    'hostname': hostname,
                    'type': response['type'],
                    'version': response['version'],
                    'browser_name': response['browser']['name'],
                    'browser_version': response['browser']['version'],
                    'instance_type': response['instance_type'],
                    'addresses': response['network']['ipv4']['addresses'] + response['network']['ipv6']['addresses'],
                    'parallel_tasks_limit': response['limits']['parallel_tasks'],
                    'last_seen': timezone.now(),
                    'alive': True,
                }, name=name)

                marvin_key = 'marvin_{}'.format(marvin.name)
                cache.set(marvin_key, response['activity']['browse']['running'])

                marvins.add(name)

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        'New Marvin {marvin.name} ({marvin.instance_type}) detected'.format(marvin=marvin)
                    ))
                else:
                    self.stdout.write(
                        'Existing Marvin {marvin.name} ({marvin.instance_type}) updated'.format(marvin=marvin)
                    )
            except requests.exceptions.RequestException:
                self.stderr.write('Unable to connect to {sockaddr}'.format(sockaddr=sockaddr))
            except (KeyError, ValueError):
                self.stderr.write('Marvin {sockaddr} returned invalid JSON'.format(sockaddr=sockaddr))

        # Mark other Marvins as dead
        for marvin in Marvin.objects.filter(alive=True).exclude(name__in=marvins):
            marvin.alive = False
            marvin.save()

            self.stderr.write(self.style.WARNING(
                'Marvin {marvin.name} ({marvin.instance_type}) has gone'.format(marvin=marvin)
            ))
