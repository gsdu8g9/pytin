from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from assets.models import PortConnection, SwitchPort, ServerPort
from resources.models import Resource


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="Assets manager",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # Query
        file_cmd_parser = subparsers.add_parser('switchlinks', help='Show what is linked to switch')
        file_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        self._register_handler('switchlinks', self._handle_switchlinks)

    def _handle_switchlinks(self, *args, **options):
        device_id = options['device-id']
        switch = Resource.objects.get(pk=device_id)

        print switch
        for switch_port in SwitchPort.objects.active(parent=switch):
            print "\t", switch_port
            for port_connection in PortConnection.objects.active(parent=switch_port):
                linked_server_port = port_connection.linked_port_id
                server_port = ServerPort.objects.get(pk=linked_server_port)

                if server_port.is_deleted:
                    port_connection.delete()
                    continue

                print "\t\t%s %s (%s, %s)" % (server_port.parent.id, server_port.parent.as_leaf_class().label,
                                              server_port.parent.get_option_value('group'),
                                              server_port.parent.get_option_value('guessed_role'))

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
