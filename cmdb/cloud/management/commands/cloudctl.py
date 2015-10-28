from __future__ import unicode_literals
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from cloud.models import CloudService
from cmdb.lib import loader
from resources.lib.console import ConsoleResourceWriter


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Cloud management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # Cloud Services
        node_cmd_parser = subparsers.add_parser('service', help='Manage cloud services.')
        node_cmd_parser.add_argument('-l', '--list', action="store_true", help="List cloud services with nodes.")
        node_cmd_parser.add_argument('-c', '--create', action="store_true",
                                     help="Add or update cloud service.")
        node_cmd_parser.add_argument('-n', '--name', help="Service name.")
        node_cmd_parser.add_argument('-i', '--implementor', help="Service implementor class.")
        self.register_handler('service', self._handle_service)

    def _handle_service(self, *args, **options):
        if options['list']:
            service_items = []
            for service in CloudService.objects.all():
                service_items.append([
                    service.name,
                    service.implementor,
                    "\n".join(service.nodes)
                ])

            writer = ConsoleResourceWriter(service_items)
            writer.print_table(['name', 'implementor', 'nodes'])
        elif options['create']:
            assert options['name'], "Service name must be specified."
            assert options['implementor'], "Implementor class must be specified."

            name = options['name']
            implementor = options['implementor']

            try:
                loader.get_class(implementor)
            except:
                print "Class %s not found." % implementor
                return

            service, created = CloudService.objects.update_or_create(
                name=name,
                implementor=implementor
            )
            print "%s service %s" % ('Created' if created else 'Updated', service)

    def handle(self, *args, **options):
        subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
