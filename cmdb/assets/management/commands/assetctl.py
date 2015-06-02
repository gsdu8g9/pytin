from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from assets.models import PortConnection, SwitchPort, ServerPort, Server
from ipman.models import IPAddress
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

        server_cmd_parser = subparsers.add_parser('server', help='Server query')
        server_cmd_parser.add_argument('server-id', nargs='*', help="IDs of the server to view.")
        self._register_handler('server', self._handle_server)

    def _handle_server(self, *args, **options):
        if len(options['server-id']) > 0:
            for server_id in options['server-id']:
                server = Server.objects.get(pk=server_id)
                self._dump_server(server)
                print ""
        else:
            for server in Server.objects.active():
                self._dump_server(server)
                print ""

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

    def _dump_server(self, server):
        assert server

        print server
        has_port = False
        has_connection = False
        has_ip = False
        for server_port in ServerPort.objects.active(parent=server):
            has_port = True
            for connection in PortConnection.objects.active(linked_port_id=server_port.id):
                has_connection = True
                print "    eth link: %s (%s) <-> %s (%s Mbit)" % (
                    server_port, server_port.number, connection.parent.as_leaf_class(), connection.link_speed_mbit)

            for ip_address in IPAddress.objects.active(parent=server_port):
                has_ip = True
                print "    %s" % ip_address

        if not has_port:
            print "WARNING: server %s has no ports defined" % server
        else:
            if not has_connection:
                print "WARNING: server %s has no switch connection" % server

            if not has_ip:
                print "WARNING: server %s has no IPs" % server

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
