from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from importer.importlib import CmdbImporter
from importer.providers.qtech.qsw8300 import QSW8300ArpTableFileDump, QSW8300MacTableFileDump, QSW8300ArpTableSnmp
from resources.models import Resource


class Command(BaseCommand):
    cmdb_importer = CmdbImporter()

    registered_handlers = {}
    registered_arp_providers = {
        'QSW8300': QSW8300ArpTableFileDump
    }

    registered_arp_providers_snmp = {
        'QSW8300': QSW8300ArpTableSnmp
    }

    registered_mac_providers = {
        'QSW8300': QSW8300MacTableFileDump
    }

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="CMDB data importer",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # IP address commands
        registered_providers_file = dict(self.registered_arp_providers)
        registered_providers_file.update(self.registered_mac_providers)

        file_cmd_parser = subparsers.add_parser('fromfile', help='Import data from dump files')
        file_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        file_cmd_parser.add_argument('provider', choices=registered_providers_file.keys(),
                                     help="Type of the device (or dump file format).")
        file_types_group = file_cmd_parser.add_mutually_exclusive_group()
        file_types_group.add_argument('--arpdump', help="Path to the ARP dump.")
        file_types_group.add_argument('--macdump', help="Path to the MAC dump.")
        self._register_handler('fromfile', self._handle_file_dumps)

        snmp_cmd_parser = subparsers.add_parser('snmp', help='Import data from SNMP')
        snmp_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        snmp_cmd_parser.add_argument('provider', choices=self.registered_arp_providers_snmp.keys(),
                                     help="Type of the device (or dump file format).")
        snmp_cmd_parser.add_argument('hostname', help="Hostname or IP address.")
        snmp_cmd_parser.add_argument('community', help="SNMP community string.")
        self._register_handler('snmp', self._handle_snmp)

    def _handle_snmp(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']
        hostname = options['hostname']
        community = options['community']

        source_switch = Resource.objects.get(pk=device_id)

        arp_provider = self.registered_arp_providers_snmp[provider_key](device_id, hostname, community)
        for arp_record in arp_provider:
            self.cmdb_importer.add_arp_record(source_switch, arp_record)

    def _handle_file_dumps(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']

        if options['arpdump']:
            provider = self.registered_arp_providers[provider_key]
            file_name = options['arpdump']
            self._import_from_arp(provider(file_name, device_id))
        elif options['macdump']:
            provider = self.registered_mac_providers[provider_key]
            file_name = options['macdump']
            self._import_from_mac(provider(file_name, device_id))
        else:
            raise Exception("Specify one of the dump files.")

    def _import_from_arp(self, arp_provider):
        assert arp_provider, "arp_provider must be defined."

        source_switch = Resource.objects.get(pk=arp_provider.device_id)

        for arp_record in arp_provider:
            self.cmdb_importer.add_arp_record(source_switch, arp_record)

    def _import_from_mac(self, mac_provider):
        assert mac_provider, "mac_provider must be defined."

        source_switch = Resource.objects.get(pk=mac_provider.device_id)

        for mac_record in mac_provider:
            self.cmdb_importer.add_mac_record(source_switch, mac_record)

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
