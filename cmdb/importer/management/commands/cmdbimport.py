from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from assets.models import GatewaySwitch, Switch
from importer.importlib import CmdbImporter
from importer.providers.providers import ArpTableRecord
from importer.providers.qtech.qsw8300 import QSW8300ArpTableFileDump, QSW8300MacTableFileDump, QSW8300ArpTableSnmp, \
    QSW8300MacTableSnmp
from resources.models import Resource


class Command(BaseCommand):
    cmdb_importer = CmdbImporter()

    registered_handlers = {}

    registered_providers_file = {
        'QSW8300.arp': QSW8300ArpTableFileDump,
        'QSW3400.arp': QSW8300ArpTableFileDump,
        'QSW8300.mac': QSW8300MacTableFileDump,
        'QSW3400.mac': QSW8300MacTableFileDump,
    }

    registered_providers_snmp = {
        'QSW8300.arp': QSW8300ArpTableSnmp,
        'QSW3400.arp': QSW8300ArpTableSnmp,
        'QSW8300.mac': QSW8300MacTableSnmp,
        'QSW3400.mac': QSW8300MacTableSnmp,
    }

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="CMDB data importer",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # IP address commands
        file_cmd_parser = subparsers.add_parser('fromfile', help='Import data from dump files')
        file_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        file_cmd_parser.add_argument('provider', choices=self.registered_providers_file.keys(),
                                     help="Type of the device (or dump file format).")
        file_types_group = file_cmd_parser.add_mutually_exclusive_group()
        file_types_group.add_argument('--arpdump', help="Path to the ARP dump.")
        file_types_group.add_argument('--macdump', help="Path to the MAC dump.")
        self._register_handler('fromfile', self._handle_file_dumps)

        snmp_cmd_parser = subparsers.add_parser('snmp', help='Import data from SNMP')
        snmp_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        snmp_cmd_parser.add_argument('provider', choices=self.registered_providers_snmp.keys(),
                                     help="Type of the device (or dump file format).")
        snmp_cmd_parser.add_argument('hostname', help="Hostname or IP address.")
        snmp_cmd_parser.add_argument('community', help="SNMP community string.")
        self._register_handler('snmp', self._handle_snmp)

        auto_cmd_parser = subparsers.add_parser('auto', help='Import and update CMDB data based on resources.')
        self._register_handler('auto', self._handle_auto)

    def _handle_auto(self, *args, **options):
        # update via snmp
        for switch in Resource.objects.active(type__in=[GatewaySwitch.__name__, Switch.__name__]):
            print "Found switch: %s" % switch
            if switch.has_option('snmp_provider_key'):
                snmp_provider_key = switch.get_option_value('snmp_provider_key')
                if snmp_provider_key in self.registered_providers_snmp:
                    hostname = switch.get_option_value('snmp_host')
                    community = switch.get_option_value('snmp_community')

                    print "\tdata: ID:%d\t%s\t%s" % (switch.id, hostname, community)
                    provider = self.registered_providers_snmp[snmp_provider_key](switch.id, hostname, community)
                    self._import_record(switch, provider)

    def _handle_snmp(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']
        hostname = options['hostname']
        community = options['community']

        source_switch = Resource.objects.get(pk=device_id)

        provider = self.registered_providers_snmp[provider_key](device_id, hostname, community)
        self._import_record(source_switch, provider)

        source_switch.set_option('snmp_host', hostname)
        source_switch.set_option('snmp_community', community)
        source_switch.set_option('snmp_provider_key', provider_key)

    def _import_record(self, gw_switch, provider):
        assert gw_switch, "gw_switch must be defined."
        assert provider, "provider must be defined."

        for record in provider:
            if record.__class__ == ArpTableRecord:
                self.cmdb_importer.add_arp_record(gw_switch, record)
            else:
                self.cmdb_importer.add_mac_record(gw_switch, record)

    def _handle_file_dumps(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']

        if options['arpdump']:
            provider = self.registered_providers_file[provider_key]
            file_name = options['arpdump']
            self._import_from_arp(provider(file_name, device_id))
        elif options['macdump']:
            provider = self.registered_providers_file[provider_key]
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
