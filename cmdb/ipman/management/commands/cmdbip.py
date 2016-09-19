from __future__ import unicode_literals

from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from cmdb.settings import logger
from ipman.models import IPAddressRenter, GlobalIPManager, IPAddressPoolFactory
from resources.lib.console import ConsoleResourceWriter
from resources.models import Resource, ResourceOption


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
        addr_add_cmd.add_argument('target-pool-id', type=int, help="ID of the target pool.")
        addr_add_cmd.add_argument('ip-address', help="IP address to add.")
        self._register_handler('address.add', self._handle_address_add)

        addr_add_cmd = address_subparsers.add_parser('delete', help="Delete IP address.")
        addr_add_cmd.add_argument('ip-address', help="IP address to delete.")
        self._register_handler('address.delete', self._handle_address_delete)

        addr_move_cmd = address_subparsers.add_parser('move', help="Move IPs between pools.")
        addr_move_cmd.add_argument('target-pool-id', type=int, help="ID of the target pool.")
        addr_move_cmd.add_argument('--file', help="File with IP addresses list.", default='')
        addr_move_cmd.add_argument('--ip-start', help="IP address to start from.", default='')
        addr_move_cmd.add_argument('--ip-end', help="Last IP in the sequence.", default='')
        addr_move_cmd.add_argument('--count', type=int, help="Number of IPs to move.", default=0)
        self._register_handler('address.move', self._handle_address_move)

        pool_rent_cmd = address_subparsers.add_parser('rent', help="Find and lock 'count' IPs from specified sources.")
        pool_rent_cmd.add_argument('--dc', type=int, help="ID of the datacenter.")
        pool_rent_cmd.add_argument('--version', type=int, help="IP address version (4 or 6).", default=4)
        pool_rent_cmd.add_argument('--pools', type=int, nargs='+', help="IDs of the specific pools.")
        pool_rent_cmd.add_argument('-c', '--count', type=int, default=1, help="Number of addresses to rent.")
        self._register_handler('address.rent', self._handle_pool_rent)

        # POOL commands
        pool_cmd_parser = subparsers.add_parser('pool', help='Manage address pools')

        pool_subparsers = pool_cmd_parser.add_subparsers(title="Pool management commands",
                                                         help="Commands help",
                                                         dest='subcommand_name',
                                                         parser_class=ArgumentParser)

        config_cmd = pool_subparsers.add_parser('config', help="Configure IP pool.")
        config_cmd.add_argument('pool-id', type=int, help="ID of the pool to be configured.")
        config_cmd.add_argument('--version', type=int, help="Version of IP addresses in pool.", default=None)
        config_cmd.add_argument('--gateway', help="IP addresses gateway.", default=None)
        config_cmd.add_argument('--netmask', help="Netmask for the IPs in the pool.", default=None)
        config_cmd.add_argument('--dns1', help="DNS1 for the pool.", default=None)
        config_cmd.add_argument('--dns2', help="DNS2 for the pool.", default=None)
        self._register_handler('pool.config', self._handle_pool_config)

        add_cidr_cmd = pool_subparsers.add_parser('addcidr', help="Add IP pool defined by network/prefix.")
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

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_pool_config(self, *args, **options):
        target_pool = Resource.active.get(pk=options['pool-id'])

        if options['version']:
            target_pool.set_option('version', options['version'], ResourceOption.FORMAT_INT)

        if options['gateway']:
            target_pool.set_option('gateway', options['gateway'].decode('utf-8'))

        if options['netmask']:
            target_pool.set_option('netmask', options['netmask'].decode('utf-8'))

        if options['dns1']:
            target_pool.set_option('dns1', options['dns1'].decode('utf-8'))

        if options['dns2']:
            target_pool.set_option('dns2', options['dns2'].decode('utf-8'))

    def _handle_pool_rent(self, *args, **options):
        ip_count = options['count']

        if options['dc']:
            renter = IPAddressRenter.from_datacenter(Resource.objects.get(
                pk=options['dc']),
                ip_version=options['version'])
        else:
            renter = IPAddressRenter.from_pools(GlobalIPManager.find_pools(pk__in=options['pools']))

        rent_ips = renter.rent(ip_count)

        self._print_addresses(rent_ips)

    def _handle_address_add(self, *args, **options):
        target_pool = Resource.active.get(pk=options['target-pool-id'])

        ip_address = options['ip-address'].decode('utf-8')
        ip = target_pool.add_ip(ip_address)

        self._print_address(ip)

    def _handle_address_delete(self, *args, **options):
        ip_address = options['ip-address'].decode('utf-8')
        ip = GlobalIPManager.get_ip(ip_address)

        ip.delete()

        logger.info("%s deleted" % ip_address)

    def _handle_address_move(self, *args, **options):
        target_pool = Resource.active.get(pk=options['target-pool-id'])

        moved_ips = []
        if options['file']:
            with open(options['file']) as ip_list_file:
                for ip_line in ip_list_file:
                    ip_line = ip_line.decode('utf-8').strip()
                    if not ip_line:
                        continue

                    ip_obj = GlobalIPManager.get_ip(ip_line)
                    if ip_obj.move_to_pool(target_pool):
                        moved_ips.append(ip_obj)
        elif options['ip_start']:
            start_ip = options['ip_start'].decode('utf-8')
            end_ip = options['ip_end'].decode('utf-8')
            count = options['count']

            moved_ips = GlobalIPManager.move_ips(target_pool=target_pool,
                                                 start_ip=start_ip, end_ip=end_ip, count=count)

        logger.info("IPs are moved to %s" % target_pool)
        self._print_addresses(moved_ips)

    def _handle_pool_addnamed(self, *args, **options):
        pool_name = options['pool-name'].decode('utf-8')
        IPAddressPoolFactory.from_name(pool_name)

        self._list_pools()

    def _handle_pool_addcidr(self, *args, **options):
        net = options['net'].decode('utf-8')
        IPAddressPoolFactory.from_network(net)

        self._list_pools()

    def _handle_pool_addrange(self, *args, **options):
        range_from = options['ip_start'].decode('utf-8')
        range_to = options['ip_end'].decode('utf-8')

        IPAddressPoolFactory.from_range(range_from=range_from, range_to=range_to)

        self._list_pools()

    def _handle_list_pools(self, *args, **options):
        self._list_pools()

    def _handle_delete_pool(self, *args, **options):
        Resource.active.filter(pk=options['pool-id']).delete()

        self._list_pools()

    def _print_addresses(self, ip_address_list):
        for ip_address in ip_address_list:
            self._print_address(ip_address)

    def _print_address(self, ip_address):
        assert ip_address

        logger.info("%s" % ip_address)

    def _list_pools(self):
        resource_writer = ConsoleResourceWriter(GlobalIPManager.find_pools())
        resource_writer.print_table(fields=['id',
                                            'parent',
                                            'self',
                                            'status',
                                            'used_addresses',
                                            'total_addresses',
                                            'usage'],
                                    sort_by='parent')

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
