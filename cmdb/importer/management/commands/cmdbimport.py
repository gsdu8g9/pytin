from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from assets.models import ServerPort, ServerResource, VirtualServerResource

from importer.providers.qtech.qsw8300 import QSW8300ArpTableFileDump, QSW8300MacTableFileDump
from ipman.models import IPAddress, IPAddressPool
from resources.models import Resource


class Command(BaseCommand):
    registered_handlers = {}
    registered_arp_providers = (
        ('QSW8300', QSW8300ArpTableFileDump),
    )

    registered_mac_providers = (
        ('QSW8300', QSW8300MacTableFileDump),
    )

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="CMDB data importer",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # IP address commands
        registered_providers = self.registered_arp_providers + self.registered_mac_providers
        registered_providers_map = {}
        for registered_provider in registered_providers:
            registered_providers_map[registered_provider[0]] = 1

        file_cmd_parser = subparsers.add_parser('file', help='Import data from dump files')
        file_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        file_cmd_parser.add_argument('provider', choices=registered_providers_map.keys(),
                                     help="Type of the device (or dump file format).")

        file_types_group = file_cmd_parser.add_mutually_exclusive_group()
        file_types_group.add_argument('--arpdump', help="Path to the ARP dump.")
        file_types_group.add_argument('--macdump', help="Path to the MAC dump.")

        self._register_handler('file', self._handle_file_dumps)

    def _handle_file_dumps(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']

        if options['arpdump']:
            provider = self.registered_arp_providers[provider_key]
            file_name = options['arpdump']

            self._import_from_arp(provider(file_name))
        elif options['macdump']:
            provider = self.registered_mac_providers[provider_key]
            file_name = options['macdump']

            self._import_from_mac(provider(file_name))
        else:
            raise Exception("Specify one of the dump files.")

    def _import_from_arp(self, arp_provider):
        assert arp_provider, "arp_provider must be defined."

        available_ip_pools = IPAddressPool.get_all_pools()
        for arp_record in arp_provider:
            self._add_ip(arp_record, available_ip_pools)

        for arp_record in arp_provider:
            self._add_asset_port(arp_record)

    def _import_from_mac(self, mac_provider):
        assert mac_provider, "mac_provider must be defined."

        for arp_record in mac_provider:
            self._add_asset_port(arp_record)

    def _add_ip(self, arp_record, available_ip_pools):
        added = False
        for ip_pool in available_ip_pools:
            if ip_pool.can_add(arp_record.ip):
                ips = IPAddress.objects.active(address__exact=arp_record.ip)
                if len(ips) > 0:
                    ips[0].use()

                    if len(ips) > 1:
                        print "ERROR: Duplicate IP %s!" % arp_record.ip
                else:
                    print "Add %s to %s" % (arp_record.ip, ip_pool)
                    IPAddress.create(address=arp_record.ip, status=Resource.STATUS_INUSE, parent=ip_pool)

                added = True
                break
        if not added:
            print "!!! IP %s is not added" % arp_record.ip

    def _add_asset_port(self, arp_record):
        server_port = None
        ports = ServerPort.objects.active(mac=arp_record.mac)
        if len(ports) <= 0:
            # create server and port
            server = None
            if arp_record.vendor:
                server = ServerResource.create(label='Server', vendor=arp_record.vendor)
            else:
                server = VirtualServerResource.create(label='VPS')

            server_port = ServerPort.create(mac=arp_record.mac, parent=server)
        else:
            server_port = ports[0]

            if len(ports) > 1:
                print "ERROR: Duplicate ports found with mac: %s!" % arp_record.mac

        # add IP to the port
        ips = IPAddress.objects.active(address__exact=arp_record.ip)
        if len(ips) > 0:
            ips[0].parent = server_port
            ips[0].use()

            if len(ips) > 1:
                print "ERROR: Duplicate IP %s!" % arp_record.ip
        else:
            print "Add %s to %s" % (arp_record.ip, server_port)
            IPAddress.create(address=arp_record.ip, status=Resource.STATUS_INUSE, parent=server_port)

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
