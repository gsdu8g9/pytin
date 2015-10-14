# coding=utf-8
from __future__ import unicode_literals

from argparse import ArgumentParser
import datetime

from django.core.management.base import BaseCommand

from django.utils import timezone

from assets.models import GatewaySwitch, Switch, VirtualServer, PortConnection, SwitchPort
from cmdb.settings import logger
from importer.importlib import GenericCmdbImporter
from importer.providers.l3_switch import L3Switch
from importer.providers.vendors.dlink import DSG3200Switch
from importer.providers.vendors.hp import HP1910Switch
from importer.providers.vendors.qtech import QtechL3Switch, Qtech3400Switch
from importer.providers.vendors.sw3com import Switch3Com2250
from ipman.models import IPAddress, IPAddressPool
from resources.models import Resource


class Command(BaseCommand):
    cmdb_importer = GenericCmdbImporter()

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
        auto_cmd_parser.add_argument('--switch-id', help="ID of the switch to get SNMP data from.")
        self._register_handler('auto', self._handle_auto)

        household_cmd_parser = subparsers.add_parser('household', help='Cleanup unused resources.')
        self._register_handler('household', self._handle_household)

    def _handle_household(self, *args, **options):
        last_seen_31days = timezone.now() - datetime.timedelta(days=31)
        last_seen_15days = timezone.now() - datetime.timedelta(days=15)

        # Clean IP with parent=ip pool (free) with last_seen older that 31 days. It means that IP is not
        # used and can be released.
        logger.info("Clean missing IP addresses: %s" % last_seen_31days)
        for free_ip_pool in Resource.active.filter(status=Resource.STATUS_FREE, type__in=IPAddressPool.ip_pool_types):
            logger.info("    pool %s" % free_ip_pool)

            for ip in IPAddress.active.filter(
                    status=Resource.STATUS_INUSE,
                    last_seen__lt=last_seen_31days,
                    ipman_pool_id=free_ip_pool.id,
                    version=4):
                logger.warning("    used ip %s from the FREE IP pool is not seen for 31 days. Free it." % ip)
                ip.free(cascade=True)

            for ip in IPAddress.active.filter(
                    status=Resource.STATUS_LOCKED,
                    last_seen__lt=last_seen_15days,
                    ipman_pool_id=free_ip_pool.id,
                    version=4):
                logger.warning("    locked ip %s from the FREE IP pool is not seen for 15 days. Free it." % ip)
                ip.free(cascade=True)

        logger.info("Clean missing virtual servers: %s" % last_seen_31days)
        for vm in VirtualServer.active.filter(last_seen__lt=last_seen_31days):
            logger.warning("    server %s not seen for 31 days. Removing..." % vm)
            for vm_child in vm:
                logger.info("        remove %s" % vm_child)
                vm_child.delete()
            vm.delete()

        logger.info("Clean unresolved PortConnections...")
        removed = 0
        for connection in PortConnection.active.all():
            if not connection.linked_port:
                connection.delete()
                removed += 1
        logger.info("  removed: %s" % removed)

    def _handle_auto(self, *args, **options):
        # update via snmp
        query = dict(type__in=[GatewaySwitch.__name__, Switch.__name__])
        if options['switch_id']:
            query['pk'] = options['switch_id']

        for switch in Resource.active.filter(**query):
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

        logger.info("Process hypervisors.")
        for switch in Switch.active.all():
            for switch_port in SwitchPort.active.filter(parent=switch):
                self.cmdb_importer.process_hypervisors(switch_port)

        for switch in GatewaySwitch.active.all():
            for switch_port in SwitchPort.active.filter(parent=switch):
                self.cmdb_importer.process_hypervisors(switch_port)

    def _handle_snmp(self, *args, **options):
        device_id = options['device-id']
        provider_key = options['provider']
        hostname = options['hostname']
        community = options['community']

        source_switch = Resource.active.get(pk=device_id)

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
