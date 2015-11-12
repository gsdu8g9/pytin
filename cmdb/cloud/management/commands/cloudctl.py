from __future__ import unicode_literals

import time
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from cloud.models import CloudConfig
from cloud.provisioning.backends.proxmox import ProxMoxJBONServiceBackend


class Command(BaseCommand):
    registered_handlers = {}
    backend = ProxMoxJBONServiceBackend(CloudConfig())

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Cloud management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # Cloud Services
        node_cmd_parser = subparsers.add_parser('vps', help='Manage VPS services.')
        node_cmd_parser.add_argument('-c', '--create', action="store_true",
                                     help="Create VPS service.")
        self.register_handler('vps', self._handle_vps)

    def _handle_vps(self, *args, **options):
        # tracker = self.backend.create_vps(vmid=int(time.time()), cpu=1, ram=1024, hdd=50)

        tracker = self.backend.start_vps(vmid=1447344425)

        print tracker.wait_to_end()

        print tracker

    def handle(self, *args, **options):
        subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
