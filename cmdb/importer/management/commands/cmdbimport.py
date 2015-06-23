from argparse import ArgumentParser
import datetime

from django.core.management.base import BaseCommand

from django.utils import timezone

from assets.models import GatewaySwitch, Switch, VirtualServer, VirtualServerPort, PortConnection
from cmdb.settings import logger
from importer.importlib import CmdbImporter
from importer.providers.l3_switch import L3Switch
from importer.providers.vendors.dlink import DSG3200Switch
from importer.providers.vendors.hp import HP1910Switch
from importer.providers.vendors.qtech import QtechL3Switch, Qtech3400Switch
from importer.providers.vendors.sw3com import Switch3Com2250
from ipman.models import IPAddress
from resources.models import Resource


class Command(BaseCommand):
    cmdb_importer = CmdbImporter()

    registered_handlers = {}

    registered_providers = {
        'generic': L3Switch,
        '3com.2952': HP1910Switch,
        '3com.2250': Switch3Com2250,
        'dlink.dsg3200': DSG3200Switch,
        'hp.1910': HP1910Switch,
        'qtech': QtechL3Switch,
        'qtech.3400': Qtech3400Switch
    }

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="CMDB data importer",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # IP address commands
        file_cmd_parser = subparsers.add_parser('fromfile', help='Import data from dump files')
        file_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        file_cmd_parser.add_argument('provider', choices=self.registered_providers.keys(),
                                     help="Type of the device (or dump file format).")
        file_types_group = file_cmd_parser.add_mutually_exclusive_group()
        file_types_group.add_argument('--arpdump', help="Path to the ARP dump.")
        file_types_group.add_argument('--macdump', help="Path to the MAC dump.")
        self._register_handler('fromfile', self._handle_file_dumps)

        snmp_cmd_parser = subparsers.add_parser('snmp', help='Import data from SNMP')
        snmp_cmd_parser.add_argument('device-id', help="Resource ID of the device used to take the dump.")
        snmp_cmd_parser.add_argument('provider', choices=self.registered_providers.keys(),
                                     help="Type of the device (or dump file format).")
        snmp_cmd_parser.add_argument('hostname', help="Hostname or IP address.")
        snmp_cmd_parser.add_argument('community', help="SNMP community string.")
        self._register_handler('snmp', self._handle_snmp)

        auto_cmd_parser = subparsers.add_parser('auto', help='Import and update CMDB data based on resources.')
        self._register_handler('auto', self._handle_auto)

        household_cmd_parser = subparsers.add_parser('household', help='Cleanup unused resources.')
        self._register_handler('household', self._handle_household)

    def _handle_household(self, *args, **options):
        last_seen_old = timezone.now() - datetime.timedelta(days=100)

        logger.info("Clean missing virtual servers: %s" % last_seen_old)
        for vm in VirtualServer.objects.active(last_seen__lt=last_seen_old):
            logger.warning("    server %s not seen for 3 months. Removing..." % vm)
            for vm_port in VirtualServerPort.objects.active(parent=vm):
                for connection in PortConnection.objects.active(linked_port_id=vm_port.id):
                    connection.delete(cascade=True)
            vm.delete(cascade=True)

        logger.info("Clean missing IP addresses: %s" % last_seen_old)
        for ip in IPAddress.objects.active(last_seen__lt=last_seen_old):
            ip_pool_id = ip.get_option_value('ipman_pool_id')

            if ip_pool_id and Resource.objects.active(pk=ip_pool_id, status=Resource.STATUS_FREE).exists():
                logger.warning("    ip %s from the FREE IP pool is not seen for 3 months. Removing..." % ip)
                ip.delete(cascade=True)

    def _handle_auto(self, *args, **options):
        # update via snmp
        for switch in Resource.objects.active(type__in=[GatewaySwitch.__name__, Switch.__name__]):
            logger.info("Found switch: %s" % switch)
            if switch.has_option('snmp_provider_key'):
                snmp_provider_key = switch.get_option_value('snmp_provider_key')
                if snmp_provider_key in self.registered_providers:
                    hostname = switch.get_option_value('snmp_host')
                    community = switch.get_option_value('snmp_community')

                    logger.info("\tdata: ID:%d\t%s\t%s" % (switch.id, hostname, community))
                    provider = self.registered_providers[snmp_provider_key]()
                    provider.from_snmp(hostname, community)

                    self.cmdb_importer.import_switch(switch.id, provider)
                else:
                    logger.warning("Unknown SNMP data provider: %s" % snmp_provider_key)

    def _handle_snmp(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']
        hostname = options['hostname']
        community = options['community']

        source_switch = Resource.objects.get(pk=device_id)

        provider = self.registered_providers[provider_key]()
        provider.from_snmp(hostname, community)
        self.cmdb_importer.import_switch(device_id, provider)

        source_switch.set_option('snmp_host', hostname)
        source_switch.set_option('snmp_community', community)
        source_switch.set_option('snmp_provider_key', provider_key)

    def _handle_file_dumps(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']

        provider = self.registered_providers[provider_key]()

        if options['arpdump']:
            provider.from_arp_dump(options['arpdump'])
        elif options['macdump']:
            provider.from_mac_dump(options['macdump'])
        else:
            raise Exception("Specify one of the dump files.")

        self.cmdb_importer.import_switch(device_id, provider)

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
