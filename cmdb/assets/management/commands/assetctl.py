from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.utils import timezone

from assets.models import PortConnection, SwitchPort, ServerPort, Server, InventoryResource
from cmdb.settings import logger
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
        server_cmd_parser.add_argument('ip-or-id', nargs='*', help="IDs or IPs of the server to view.")
        server_cmd_parser.add_argument('-o', '--with-options', action='store_true', help="Show server resource options")
        self._register_handler('server', self._handle_server)

    def _handle_server(self, *args, **options):
        if len(options['ip-or-id']) > 0:
            for server_ip_id in options['ip-or-id']:
                server = None
                if server_ip_id.find('.') > -1:
                    ips = IPAddress.objects.active(address=server_ip_id)
                    if len(ips) > 0 and issubclass(ips[0].parent.parent.as_leaf_class().__class__, InventoryResource):
                        print ips[0].parent.parent.type
                        server = ips[0].parent.parent.as_leaf_class()
                    else:
                        logger.warning("IP %s is not assigned to any server." % server_ip_id)
                else:
                    server = Server.objects.get(pk=server_ip_id)

                if server:
                    self._dump_server(server, options['with_options'])
                    logger.info("")
        else:
            for server in Server.objects.active():
                self._dump_server(server, options['with_options'])
                logger.info("")

    def _handle_switchlinks(self, *args, **options):
        device_id = options['device-id']
        switch = Resource.objects.get(pk=device_id)

        logger.info(switch)
        for switch_port in SwitchPort.objects.active(parent=switch):
            logger.info("\t%s", switch_port)
            for port_connection in PortConnection.objects.active(parent=switch_port):
                linked_server_port = port_connection.linked_port_id
                server_port = ServerPort.objects.get(pk=linked_server_port)

                if server_port.is_deleted:
                    port_connection.delete()
                    continue

                logger.info("\t\t%s %s (%s, %s)" % (server_port.parent.id, server_port.parent.as_leaf_class().label,
                                                    server_port.parent.get_option_value('group'),
                                                    server_port.parent.get_option_value('guessed_role')))

    def _dump_server(self, server, with_options=False):
        assert server

        logger.info("i-%d\t%s\t%s\t%s\t%s" % (server.id, server.parent_id, server.type, server, server.status))

        if with_options:
            logger.info("created_at = %s" % timezone.localtime(server.created_at))
            logger.info("updated_at = %s" % timezone.localtime(server.updated_at))
            logger.info("last_seen = %s" % timezone.localtime(server.last_seen))

            for option in server.get_options():
                logger.info("%s" % option)

        has_port = False
        has_connection = False
        has_ip = False
        for server_port in ServerPort.objects.active(parent=server):
            has_port = True
            for connection in PortConnection.objects.active(linked_port_id=server_port.id):
                has_connection = True
                logger.info("    [id:%s] %s <-> %s (%s Mbit)" % (
                    connection.id, server_port, connection.parent.as_leaf_class(), connection.link_speed_mbit))

            for ip_address in IPAddress.objects.active(parent=server_port):
                has_ip = True
                logger.info("    %s" % ip_address)

        if not has_port:
            logger.warning("Server %s has no ports defined" % server)
        else:
            if not has_connection:
                logger.warning("Server %s has no switch connection" % server)

            if not has_ip:
                logger.warning("Server %s has no IPs" % server)

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
