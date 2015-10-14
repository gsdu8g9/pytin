from __future__ import unicode_literals
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from cmdb.settings import logger
from ipman.models import IPNetworkPool, IPAddressPool, IPAddressRangePool, IPAddress
from resources.lib.console import ConsoleResourceWriter
from resources.models import Resource


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="IP management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # IP address commands
        address_cmd_parser = subparsers.add_parser('address', help='Manage IP addresses')
        address_subparsers = address_cmd_parser.add_subparsers(title="IP address management commands",
                                                               help="Commands help",
                                                               dest='subcommand_name',
                                                               parser_class=ArgumentParser)

        addr_add_cmd = address_subparsers.add_parser('add', help="Add IP to the pool.")
        addr_add_cmd.add_argument('pool-id', type=int, help="ID of the pool")
        addr_add_cmd.add_argument('ip', nargs='+', help="IP address to add to the pool-id")
        self._register_handler('address.add', self._handle_address_add)

        pool_rent_cmd = address_subparsers.add_parser('rent', help="Find and lock 'count' IPs from specified pools.")
        pool_rent_cmd.add_argument('pool-id', nargs='+', help="IDs of the pools to rent IPs.")
        pool_rent_cmd.add_argument('-c', '--count', type=int, default=1, help="Number of addresses to rent.")
        self._register_handler('address.rent', self._handle_pool_rent)

        # POOL commands
        pool_cmd_parser = subparsers.add_parser('pool', help='Manage address pools')

        pool_subparsers = pool_cmd_parser.add_subparsers(title="Pool management commands",
                                                         help="Commands help",
                                                         dest='subcommand_name',
                                                         parser_class=ArgumentParser)

        add_cidr_cmd = pool_subparsers.add_parser('addcidr', help="Add IP pool defined by network.")
        add_cidr_cmd.add_argument('net', help="CIDR network")
        self._register_handler('pool.addcidr', self._handle_pool_addcidr)

        add_cidr_cmd = pool_subparsers.add_parser('addrange', help="Add IP pool defined by address range.")
        add_cidr_cmd.add_argument('ip-start', help="IP range start.")
        add_cidr_cmd.add_argument('ip-end', help="IP range end.")
        self._register_handler('pool.addrange', self._handle_pool_addrange)

        add_cidr_cmd = pool_subparsers.add_parser('addnamed', help="Add named pool. It holds arbitrary IPs.")
        add_cidr_cmd.add_argument('pool-name', help="Name of the pool.")
        self._register_handler('pool.addnamed', self._handle_pool_addnamed)

        pool_subparsers.add_parser('list', help="List all pools")
        self._register_handler('pool.list', self._handle_list_pools)

        pool_get_next_cmd = pool_subparsers.add_parser('get', help="Get next available addresses from the pool.")
        pool_get_next_cmd.add_argument('pool-id', nargs='+', help="ID of the pools.")
        pool_get_next_cmd.add_argument('-c', '--count', type=int, default=1, help="Number of addresses to retrieve.")
        pool_get_next_cmd.add_argument('-b', '--beauty', type=int, default=5,
                                       help="Return IPs with beauty greater or equal.")
        self._register_handler('pool.get', self._handle_pool_get_next)

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_pool_rent(self, *args, **options):
        ip_pool_ids = options['pool-id']
        ip_count = options['count']

        rent_ips = IPAddressPool.globally_available(ip_pool_ids, ip_count)
        self._print_addresses(rent_ips)

    def _handle_pool_get_next(self, *args, **options):
        for pool_id in options['pool-id']:
            ip_set = Resource.active.get(pk=pool_id)
            ip_count = options['count']
            beauty_idx = options['beauty']

            for ip_address in ip_set.available():
                if not ip_count:
                    break

                if ip_address.beauty >= beauty_idx:
                    self._print_address(ip_address)
                    ip_count -= 1

            if ip_count > 0:
                logger.warning("Pool '%s' have no such many IPs (%d IPs unavailable)" % (ip_set, ip_count + 1))

    def _handle_address_add(self, *args, **options):
        ip_set = Resource.active.get(pk=options['pool-id'])

        for ip_address in options['ip']:
            if not IPAddress.is_valid_address(ip_address):
                raise ValueError("Invalid ip address: %s" % ip_address)

            ips = IPAddress.active.filter(address=ip_address)
            ip_object = ips[0] if len(ips) > 0 else IPAddress.objects.create(address=ip_address)

            ip_set += ip_object

            self._print_address(ip_object)

    def _handle_pool_addnamed(self, *args, **options):
        IPAddressPool.objects.create(name=options['pool-name'])

        self._list_pools()

    def _handle_pool_addcidr(self, *args, **options):
        if not IPAddressPool.is_valid_network(options['net']):
            raise ValueError("Invalid network")

        IPNetworkPool.objects.create(network=options['net'])

        self._list_pools()

    def _handle_pool_addrange(self, *args, **options):
        if not IPAddress.is_valid_address(options['ip-start']):
            raise ValueError("Invalid ip-start")

        if not IPAddress.is_valid_address(options['ip-end']):
            raise ValueError("Invalid ip-end")

        IPAddressRangePool.objects.create(range_from=options['ip-start'], range_to=options['ip-end'])

        self._list_pools()

    def _handle_list_pools(self, *args, **options):
        self._list_pools()

    def _handle_delete_pool(self, *args, **options):
        Resource.active.filter(pk=options['pool-id']).delete()

        self._list_pools()

    def _print_addresses(self, ip_address_list):
        assert ip_address_list

        for ip_address in ip_address_list:
            self._print_address(ip_address)

    def _print_address(self, ip_address):
        assert ip_address

        logger.info(unicode(ip_address))

    def _list_pools(self):
        resource_writer = ConsoleResourceWriter(IPAddressPool.get_all_pools())
        resource_writer.print_table(fields=['id', 'parent', 'self', 'type', 'status', 'usage'], sort_by='parent')

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
