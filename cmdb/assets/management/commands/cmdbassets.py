from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.utils import timezone

from assets.models import PortConnection, SwitchPort, ServerPort, Server, AssetResource, Rack, RackMountable
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

        file_cmd_parser = subparsers.add_parser('switch', help='Show what is linked to switch.')
        file_cmd_parser.add_argument('switch-id', help="Resource ID of the switch.")
        file_cmd_parser.add_argument('-p', '--port', nargs='*', help="IDs of the switch ports.")
        self._register_handler('switch', self._handle_switch)

        server_cmd_parser = subparsers.add_parser('server', help='Get server info.')
        server_cmd_parser.add_argument('ip-or-id', nargs='*', help="IDs or IPs of the server to view.")
        server_cmd_parser.add_argument('-o', '--with-options', action='store_true',
                                       help="Show server resource options.")
        server_cmd_parser.add_argument('--update-parent-rack', action='store_true',
                                       help="Update server parent rack based on switch port connections.")
        server_cmd_parser.add_argument('--set-position', type=int,
                                       help="Set the server position in the parent Rack.")
        self._register_handler('server', self._handle_server)

        server_cmd_parser = subparsers.add_parser('rack', help='Get rack info.')
        server_cmd_parser.add_argument('id', nargs='*', help="IDs of the racks to query info.")
        server_cmd_parser.add_argument('-l', '--layout', action='store_true', help="Show racks layout.")
        server_cmd_parser.add_argument('--set-size', type=int,
                                       help="Set the Rack size in Units.")
        self._register_handler('rack', self._handle_rack)

    def _handle_rack(self, *args, **options):
        rack_ids = options['id']

        query = {}
        if len(rack_ids) > 0:
            query['pk__in'] = rack_ids
        for rack in Rack.objects.active(**query):

            if options['set_size']:
                rack.size = options['set_size']
            elif options['layout']:
                print "*** {:^37} ***".format(
                    "%s::%s (id:%s)" % (rack.parent if rack.parent else 'global', rack, rack.id))

                rack_resources = Resource.objects.active(parent=rack)
                unsorted_servers = []
                for rack_resource in rack_resources:
                    if hasattr(rack_resource, 'is_rack_mountable') and rack_resource.is_rack_mountable:
                        unsorted_servers.append(rack_resource)

                sorted_servers = sorted(unsorted_servers, key=lambda s: s.position, reverse=True)

                if len(sorted_servers) <= 0:
                    continue

                curr_position = rack.size  # max position
                for server in sorted_servers:
                    if server.position > 0:
                        while curr_position > server.position:
                            print "[{:>3s}|{:-^39s}]".format(str(curr_position), '')
                            curr_position -= 1

                    if server.position == 0 or server.position == curr_position:
                        print "[{:>3s}|  {:<35s}  ]".format(str(server.position), server)
                        curr_position -= 1

                # print free space
                while curr_position > 0:
                    print "[{:>3s}|{:-^39s}]".format(str(curr_position), '')
                    curr_position -= 1

                print "\n"

    def _update_server_parent_rack(self, server):
        assert server
        assert isinstance(server, Server)

        for server_port in ServerPort.objects.active(parent=server):
            for port_connection in PortConnection.objects.active(linked_port_id=server_port.id):
                switch_port = port_connection.parent
                switch = switch_port.parent.as_leaf_class()

                if switch.is_mounted:
                    if server.parent_id != switch.parent_id:
                        logger.info("Update server %s parent %s->%s" % (server, server.parent_id, switch.parent_id))

                        server.mount(switch.parent.as_leaf_class())

    def _handle_server(self, *args, **options):
        if len(options['ip-or-id']) > 0:
            for server_ip_id in options['ip-or-id']:
                server = None
                if server_ip_id.find('.') > -1:
                    ips = IPAddress.objects.active(address=server_ip_id)
                    if len(ips) > 0 and isinstance(ips[0].parent.parent.as_leaf_class(), AssetResource):
                        print ips[0].parent.parent.type
                        server = ips[0].parent.parent.as_leaf_class()
                    else:
                        logger.warning("IP %s is not assigned to any server." % server_ip_id)
                else:
                    server = Server.objects.get(pk=server_ip_id)

                if server:
                    if options['update_parent_rack']:
                        self._update_server_parent_rack(server)

                    if options['set_position']:
                        server.position = options['set_position']

                    self._dump_server(server, options['with_options'])
                    logger.info("")
        else:
            for server in Server.objects.active():

                if options['update_parent_rack']:
                    self._update_server_parent_rack(server)

                self._dump_server(server, options['with_options'])
                logger.info("")

    def _handle_switch(self, *args, **options):
        device_id = options['switch-id']
        switch = Resource.objects.get(pk=device_id)

        logger.info("*** %s ***" % switch)
        query = dict(parent=switch)

        if options['port'] and len(options['port']) > 0:
            query['number__in'] = options['port']

        for switch_port in SwitchPort.objects.active(**query).order_by('-name'):
            logger.info("%s", switch_port)
            for port_connection in PortConnection.objects.active(parent=switch_port):
                linked_server_port_id = port_connection.linked_port_id
                server_ports = Resource.objects.active(pk=linked_server_port_id)
                if len(server_ports) > 0:
                    server_port = server_ports[0]
                else:
                    logger.warning("PortConnection %s linked to unexistent ServerPort %s" % (
                        port_connection, linked_server_port_id))
                    continue

                if server_port.is_deleted:
                    port_connection.delete()
                    continue

                logger.info("\t%s %s (%s, %s)" % (server_port.parent.id, server_port.parent.as_leaf_class().label,
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

        if server.is_mounted:
            logger.info("    mounted in Rack %s, at position %s." % (
                server.parent, server.get_option_value('rack_position', default=0)))
        else:
            logger.warning("    server is NOT mounted or there is no positional info.")

        has_port = False
        has_connection = False
        has_ip = False
        for server_port in ServerPort.objects.active(parent=server):
            has_port = True
            for connection in PortConnection.objects.active(linked_port_id=server_port.id):
                has_connection = True
                logger.info("    [conn:%s] %s (%s) <-> %s (%s Mbit)" % (
                    connection.id, server_port.id, server_port, connection.parent.as_leaf_class(),
                    connection.link_speed_mbit))

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
