# coding=utf-8
from __future__ import unicode_literals

from argparse import ArgumentParser
import argparse

from django.core.management.base import BaseCommand

from assets.analyzers import CmdbAnalyzer
from assets.models import PortConnection, SwitchPort, ServerPort, AssetResource, Rack, RackMountable, Server, Switch, \
    GatewaySwitch
from cmdb.settings import logger
from ipman.models import IPAddress
from resources.lib.console import ConsoleResourceWriter
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
        switch_cmd_parser.add_argument('-p', '--port', nargs=argparse.ZERO_OR_MORE,
                                       help="Specify switch ports to list connections.")
        self._register_handler('switch', self._handle_switch)

        # unit
        unit_cmd_parser = subparsers.add_parser('unit', help='Manage Rack units.')
        unit_cmd_parser.add_argument('ip-or-id', help="IDs or IPs of the unit device to view.")
        unit_cmd_parser.add_argument('-s', '--set', action='store_true',
                                     help="Set some unit options.")
        unit_cmd_parser.add_argument('--set-position', type=int, metavar='POS',
                                     help="Set the unit device position in the parent Rack.")
        unit_cmd_parser.add_argument('--set-unit-size', type=int, metavar='SIZE',
                                     help="Set the unit device size in Units.")
        unit_cmd_parser.add_argument('--set-on-rails', metavar='RAILS',
                                     help="Set unit device is on rails or not.")
        unit_cmd_parser.add_argument('--set-role', type=unicode, metavar='ROLE',
                                     help="Set the unit role.")
        self._register_handler('unit', self._handle_rack_unit)

        # rack
        rack_cmd_parser = subparsers.add_parser('rack', help='Get rack info.')
        rack_cmd_parser.add_argument('id', nargs=argparse.ONE_OR_MORE, help="IDs of the racks to query info.")
        rack_cmd_parser.add_argument('-l', '--layout', action='store_true', help="Show racks layout.")
        rack_cmd_parser.add_argument('--set-size', type=int,
                                     help="Set the Rack size in Units.")
        self._register_handler('rack', self._handle_rack)

        analyze_cmd_parser = subparsers.add_parser('analyze', help='CMDB analyzer.')
        analyze_cmd_parser.add_argument('--hypervisors', action='store_true',
                                        help="Search for hypervisors in CMDB and auto link VPS to them.")
        analyze_cmd_parser.add_argument('--merge-servers', action='store_true',
                                        help="Check if ports from the different servers are from the same server.")
        analyze_cmd_parser.add_argument('-r', '--update-parent-rack', metavar="IP_OR_ID_OR_ALL", default=None,
                                        help="Auto update parent Rack for the devices based on Switch port connections.")
        analyze_cmd_parser.add_argument('--dry-run', action='store_true', help="Do not modify the CMDB database.")
        self._register_handler('analyze', self._handle_analyze)

    def _handle_analyze(self, *args, **options):
        # hypervisors
        dry_run = options['dry_run']

        if options['update_parent_rack']:
            ip_or_id = options['update_parent_rack'].lower()
            ip_or_id = None if ip_or_id == 'all' else ip_or_id

            if ip_or_id:
                server = self._get_server_by_ip_or_id(ip_or_id)
                if Server.is_server(server):
                    self._update_server_parent_rack(server)
                else:
                    logger.warning("%s is not Server" % server)
            else:
                for server in Server.active.all():
                    if Server.is_server(server):
                        self._update_server_parent_rack(server)
                    else:
                        logger.warning("%s is not Server" % server)

        elif options['merge_servers']:
            logger.info("Check if ports from the different servers are from the same server.")

            for server_port1 in ServerPort.active.all().order_by('id'):
                mac1 = int(server_port1.mac, 16)

                for server_port2 in ServerPort.active.all().order_by('id'):
                    if server_port1.id == server_port2.id or server_port1.parent_id == server_port2.parent_id:
                        continue

                    mac2 = int(server_port2.mac, 16)

                    if abs(mac1 - mac2) <= 5:
                        logger.info(
                            "Check if servers are the same: %s and %s" % (server_port1.device, server_port2.device))
                        logger.info("  %s and %s" % (server_port1, server_port2))

        elif options['hypervisors']:
            logger.info("Search for hypervisors in CMDB...")

            for switch in Switch.active.all():
                for switch_port in SwitchPort.active.filter(parent=switch):
                    self._guess_hypervisor(switch_port, dry_run)

            for switch in GatewaySwitch.active.all():
                for switch_port in SwitchPort.active.filter(parent=switch):
                    self._guess_hypervisor(switch_port, dry_run)

    def _guess_hypervisor(self, switch_port, dry_run=False):
        """
        Поиск портов, на которых 1 физический сервер и несколько виртуальных.
        Определяем его как потенциальный гипервизор.
        :param switch_port:
        :param dry_run: If True, then role is set for guessed hypervisor (when 1 physical + many VMs).
        :return:
        """
        assert switch_port
        assert isinstance(switch_port, SwitchPort)

        result, pysical_srv, virtual_srv = CmdbAnalyzer.guess_hypervisor(switch_port)

        if result:
            logger.info("Found hypervisor: %s" % pysical_srv)

            if not dry_run:
                pysical_srv.set_option('role', 'hypervisor')
                for virtual_server in virtual_srv:
                    virtual_server.parent = pysical_srv
                    virtual_server.save()

                logger.warning("      role automatically set, virtual servers are linked to the hypervisor.")
        else:
            logger.info("Switch port: %s" % switch_port)
            logger.info("  physicals: %s, virtuals: %s." % (len(pysical_srv), len(virtual_srv)))

            logger.info("Physical servers:")
            for server in pysical_srv:
                logger.info(unicode(server))

            logger.info("Virtual servers:")
            for vserver in virtual_srv:
                logger.info(unicode(vserver))

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

                        print "[{:>3s}|  {:<40s}  |{:s}]".format(unicode(server.position), server,
                                                                 'o' if server.on_rails else ' ')
                    else:
                        print "[{:>3s}|{:-^46s}]".format(unicode(curr_position), '')

                    curr_position -= 1

                # print free space
                while curr_position > 0:
                    print "[{:>3s}|{:-^46s}]".format(unicode(curr_position), '')
                    curr_position -= 1

                print "\n"

    def _handle_rack_unit(self, *args, **options):
        server = self._get_server_by_ip_or_id(options['ip-or-id'])

        assert RackMountable.is_rack_mountable(server)

        for option_name in options:
            if option_name.startswith('set_'):
                prop_name = option_name[4:]
                if options[option_name]:
                    server.set_option(prop_name, options[option_name])

        self._dump_server(server)
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
            if len(ips) > 0 and isinstance(ips[0].parent.typed_parent, AssetResource):
                print ips[0].parent.parent.type
                server = ips[0].parent.typed_parent
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

            switch = switch_port.typed_parent

            if switch.is_mounted:
                if server.parent_id != switch.parent_id:
                    logger.info("Update server %s parent %s->%s" % (server, server.parent_id, switch.parent_id))

                    server.mount(switch.typed_parent)

    def _handle_switch(self, *args, **options):
        device_id = options['switch-id']
        switch = Resource.objects.get(pk=device_id)

        query = dict(parent=switch)

        if options['port'] and len(options['port']) > 0:
            query['number__in'] = options['port']

        port_link_data = []
        for switch_port in SwitchPort.active.filter(**query).order_by('-name'):
            for port_connection in PortConnection.active.filter(parent=switch_port):
                linked_server_port = port_connection.linked_port

                if linked_server_port:
                    if isinstance(linked_server_port, ServerPort):
                        port_link_data.append([
                            switch_port.number,
                            port_connection.link_speed_mbit,
                            linked_server_port.parent.name,
                            linked_server_port.typed_parent.label,
                            port_connection.last_seen
                        ])
                else:
                    logger.warning("PortConnection %s linked to missing ServerPort %s" % (
                        port_connection, linked_server_port.id))
                    continue

        if port_link_data:
            writer = ConsoleResourceWriter(port_link_data)
            writer.print_table(fields=['port_number', 'link_speed_mbit', 'server_name', 'label', 'last_seen'],
                               sort_by='port_number')
        else:
            logger.info("not connected")

    def _dump_server(self, server):
        assert server

        logger.info("%s %s" % (server.type, server))

        if server.is_mounted:
            logger.info("mounted %s, position %s, rails %s" % (server.typed_parent, server.position, server.on_rails))
        else:
            logger.info("not mounted")

        for server_port in ServerPort.active.filter(parent=server):
            conn = server_port.connection
            if conn:
                logger.info("  %s (seen %s)" % (conn, conn.last_seen))
            else:
                logger.info("  %s no connections" % server_port)

            for ip_address in IPAddress.active.filter(parent=server_port):
                logger.info("    %s (seen %s)" % (ip_address, ip_address.last_seen))

        logger.info("Options:")
        for option in server.get_options():
            logger.info("  %s" % option)

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
