from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.utils import timezone

from assets.models import PortConnection, SwitchPort, ServerPort, AssetResource, Rack, RackMountable, Server, \
    NetworkPort
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

        # switch
        switch_cmd_parser = subparsers.add_parser('switch', help='Show what is linked to switch.')
        switch_cmd_parser.add_argument('switch-id', help="Resource ID of the switch.")
        switch_cmd_parser.add_argument('-p', '--port', nargs='*', help="Specify switch ports to list connections.")
        self._register_handler('switch', self._handle_switch)

        # unit
        unit_cmd_parser = subparsers.add_parser('unit', help='Manage Rack units.')
        unit_cmd_parser.add_argument('ip-or-id', nargs='*', help="IDs or IPs of the unit device to view.")
        unit_cmd_parser.add_argument('-o', '--with-options', action='store_true',
                                     help="Show unit device options.")
        unit_cmd_parser.add_argument('-r', '--update-parent-rack', action='store_true',
                                     help="Auto update unit device parent Rack based on Switch port connections.")
        unit_cmd_parser.add_argument('--set-position', type=int, metavar='POS',
                                     help="Set the unit device position in the parent Rack.")
        unit_cmd_parser.add_argument('--set-size', type=int, metavar='SIZE',
                                     help="Set the unit device size in Units.")
        unit_cmd_parser.add_argument('--set-on-rails', metavar='RAILS',
                                     help="Set unit device is on rails or not.")
        self._register_handler('unit', self._handle_rack_unit)

        # server
        server_cmd_parser = subparsers.add_parser('server', help='Manage Servers.')
        server_cmd_parser.add_argument('ip-or-id', help="ID or IP of the server.")
        server_cmd_parser.add_argument('--add-port', metavar='MAC', help="Add new server port by MAC.")
        server_cmd_parser.add_argument('--number', metavar='NUM', help="Specify port number.")
        server_cmd_parser.add_argument('--link', metavar='MAC', help='Link server port to switch port.')
        server_cmd_parser.add_argument('--to-switch-port', metavar='SWITCH:PORT',
                                       help="SWITCH:PORT of the switch and port: switch_id:port.")
        self._register_handler('server', self._handle_server)

        # rack
        rack_cmd_parser = subparsers.add_parser('rack', help='Get rack info.')
        rack_cmd_parser.add_argument('id', nargs='*', help="IDs of the racks to query info.")
        rack_cmd_parser.add_argument('-l', '--layout', action='store_true', help="Show racks layout.")
        rack_cmd_parser.add_argument('--set-size', type=int,
                                     help="Set the Rack size in Units.")
        self._register_handler('rack', self._handle_rack)

    def _handle_server(self, *args, **options):
        server = self._get_server_by_ip_or_id(options['ip-or-id'])
        if not server:
            raise Exception('Invalid server IP or ID: %s' % options['ip-or-id'])

        if options['add_port']:
            port_num = 0 if not options['number'] else options['number']

            normalized_mac = NetworkPort.normalize_mac(options['add_port'])
            ports = ServerPort.active.filter(parent=server, mac=normalized_mac)
            if len(ports) > 0:
                raise Exception('Port with mac %s already exists.' % normalized_mac)
            ServerPort.objects.create(mac=normalized_mac, parent=server, number=port_num)
        elif options['link']:
            normalized_mac = NetworkPort.normalize_mac(options['link'])
            server_port = ServerPort.active.get(parent=server, mac=normalized_mac)

            (switch_id, port_number) = options['to_switch_port'].split(':')
            switch = Resource.active.get(pk=switch_id)
            switch_port = switch.get_port(port_number)

            PortConnection.create(switch_port, server_port)

        self._dump_server(server, with_options=True)

    def _handle_rack(self, *args, **options):
        rack_ids = options['id']

        query = {}
        if len(rack_ids) > 0:
            query['pk__in'] = rack_ids
        for rack in Rack.active.filter(**query):

            if options['set_size']:
                rack.size = options['set_size']
            elif options['layout']:
                print "*** {:^44} ***".format(
                    "%s::%s (id:%s)" % (rack.parent if rack.parent else 'global', rack, rack.id))

                unsorted_servers = []
                for rack_resource in rack:
                    if RackMountable.is_rack_mountable(rack_resource):
                        unsorted_servers.append(rack_resource)

                sorted_servers = sorted(unsorted_servers, key=lambda s: s.position, reverse=True)

                if len(sorted_servers) <= 0:
                    continue

                # sorted_servers must be sorted by position in reverse order
                rack_layout_map = {}
                curr_position = rack.size  # max position
                for sorted_server in sorted_servers:
                    curr_pos = sorted_server.position
                    if not curr_pos:
                        logger.warning("Server %s position is not set." % sorted_server)

                    if curr_pos in rack_layout_map:
                        while curr_pos in rack_layout_map:
                            curr_pos += 1

                        sorted_server.position = curr_pos

                    rack_layout_map[sorted_server.position] = sorted_server

                    if sorted_server.position > curr_position:
                        curr_position = sorted_server.position

                while curr_position > 0:
                    if curr_position in rack_layout_map:
                        server = rack_layout_map[curr_position]

                        print "[{:>3s}|  {:<40s}  |{:s}]".format(str(server.position), server,
                                                                 'o' if server.on_rails else ' ')
                    else:
                        print "[{:>3s}|{:-^46s}]".format(str(curr_position), '')

                    curr_position -= 1

                # print free space
                while curr_position > 0:
                    print "[{:>3s}|{:-^46s}]".format(str(curr_position), '')
                    curr_position -= 1

                print "\n"

    def _handle_rack_unit(self, *args, **options):
        unit_devices = []
        if len(options['ip-or-id']) > 0:
            for server_ip_id in options['ip-or-id']:
                server = self._get_server_by_ip_or_id(server_ip_id)

                if RackMountable.is_rack_mountable(server):
                    unit_devices.append(server)
        else:
            for server in Resource.active.all():
                if RackMountable.is_rack_mountable(server):
                    unit_devices.append(server)

        # perform commands on RackMountables
        for unit_device in unit_devices:
            if options['update_parent_rack']:
                if Server.is_server(unit_device):
                    self._update_server_parent_rack(unit_device)

            if options['set_position']:
                unit_device.position = options['set_position']

            if options['set_size']:
                unit_device.unit_size = options['set_size']

            if not options['set_on_rails'] is None:
                unit_device.on_rails = options['set_on_rails']

            self._dump_server(unit_device, options['with_options'])
            logger.info("")

    def _get_server_by_ip_or_id(self, server_ip_id):
        """
        Find server by IP or ID. If nothing found, return None
        :param server_ip_id:
        :return:
        """
        assert server_ip_id

        server = None
        if server_ip_id.find('.') > -1:
            ips = IPAddress.active.filter(address=server_ip_id)
            if len(ips) > 0 and isinstance(ips[0].parent.parent.as_leaf_class(), AssetResource):
                print ips[0].parent.parent.type
                server = ips[0].parent.parent.as_leaf_class()
            else:
                logger.warning("IP %s is not assigned to any server." % server_ip_id)
        else:
            server = Resource.objects.get(pk=server_ip_id)

        return server

    def _update_server_parent_rack(self, server):
        assert server
        assert isinstance(server, Server)

        for server_port in ServerPort.active.filter(parent=server):
            switch_port = server_port.switch_port
            if not switch_port:
                continue

            switch = switch_port.parent.as_leaf_class()

            if switch.is_mounted:
                if server.parent_id != switch.parent_id:
                    logger.info("Update server %s parent %s->%s" % (server, server.parent_id, switch.parent_id))

                    server.mount(switch.parent.as_leaf_class())

    def _handle_switch(self, *args, **options):
        device_id = options['switch-id']
        switch = Resource.objects.get(pk=device_id)

        logger.info("*** %s ***" % switch)
        query = dict(parent=switch)

        if options['port'] and len(options['port']) > 0:
            query['number__in'] = options['port']

        for switch_port in SwitchPort.active.filter(**query).order_by('-name'):
            logger.info("%s", switch_port)
            for port_connection in PortConnection.active.filter(parent=switch_port):
                linked_server_port_id = port_connection.linked_port_id
                server_ports = Resource.active.filter(pk=linked_server_port_id)
                if len(server_ports) > 0:
                    for server_port in server_ports:
                        logger.info("%s %s (%s, %s)" % (server_port.parent.id, server_port.parent.as_leaf_class().label,
                                                        server_port.parent.get_option_value('group'),
                                                        server_port.parent.get_option_value('guessed_role')))
                else:
                    logger.warning("PortConnection %s linked to unexistent ServerPort %s" % (
                        port_connection, linked_server_port_id))
                    continue

    def _dump_server(self, server, with_options=False):
        assert server

        logger.info("i-%d\t%s\t%s\t%sU\t%s\t%s" % (
            server.id, server.parent_id, server.type, server.unit_size, server, server.status))

        if with_options:
            logger.info("created_at = %s" % timezone.localtime(server.created_at))
            logger.info("updated_at = %s" % timezone.localtime(server.updated_at))
            logger.info("last_seen = %s" % timezone.localtime(server.last_seen))

            if server.is_mounted:
                logger.info("    * mounted in Rack %s, at position %s. On rails: %s" % (
                    server.parent, server.position, 'YES' if server.on_rails else 'NO'))
            else:
                logger.warning("    server is NOT mounted or there is no positional info.")

            has_port = False
            has_connection = False
            has_ip = False
            for server_port in ServerPort.active.filter(parent=server):
                has_port = True
                logger.info("    %s" % server_port)
                for connection in PortConnection.active.filter(linked_port_id=server_port.id):
                    has_connection = True

                    logger.info("    [conn:%s] %s (%s) <-> %s (%s Mbit)" % (
                        connection.id, server_port.id, server_port, connection.parent.as_leaf_class(),
                        connection.link_speed_mbit))

                for ip_address in IPAddress.active.filter(parent=server_port):
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
