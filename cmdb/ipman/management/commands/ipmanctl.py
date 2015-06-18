from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from cmdb.settings import logger

from ipman.models import IPNetworkPool, IPAddressPool, IPAddressRangePool, IPAddress
from resources.models import Resource


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # IP address commands
        address_cmd_parser = subparsers.add_parser('address', help='Manage addresses')
        address_subparsers = address_cmd_parser.add_subparsers(title="IP address management commands",
                                                               help="Commands help",
                                                               dest='subcommand_name',
                                                               parser_class=ArgumentParser)

        addr_add_cmd = address_subparsers.add_parser('add', help="Add IP in")
        addr_add_cmd.add_argument('pool-id', type=int, help="ID of the pool")
        addr_add_cmd.add_argument('ip', nargs='+', help="IP address to add to pool")
        self._register_handler('address.add', self._handle_address_add)

        # POOL commands
        pool_cmd_parser = subparsers.add_parser('pool', help='Manage address pools')

        pool_subparsers = pool_cmd_parser.add_subparsers(title="Pool management commands",
                                                         help="Commands help",
                                                         dest='subcommand_name',
                                                         parser_class=ArgumentParser)

        add_cidr_cmd = pool_subparsers.add_parser('addcidr', help="Add pool by network")
        add_cidr_cmd.add_argument('net', help="CIDR network")
        self._register_handler('pool.addcidr', self._handle_pool_addcidr)

        add_cidr_cmd = pool_subparsers.add_parser('addrange', help="Add pool by range")
        add_cidr_cmd.add_argument('ip-start', help="IP range start")
        add_cidr_cmd.add_argument('ip-end', help="IP range end")
        self._register_handler('pool.addrange', self._handle_pool_addrange)

        add_cidr_cmd = pool_subparsers.add_parser('addnamed', help="Add named pool")
        add_cidr_cmd.add_argument('pool-name', help="Name of the pool. It holds arbitrary IPs.")
        self._register_handler('pool.addnamed', self._handle_pool_addnamed)

        pool_subparsers.add_parser('list', help="List pools")
        self._register_handler('pool.list', self._handle_list_pools)

        pool_get_next_cmd = pool_subparsers.add_parser('get', help="Get next available addresses from the pool")
        pool_get_next_cmd.add_argument('pool-id', nargs='+', help="ID of the pool")
        pool_get_next_cmd.add_argument('-c', '--count', type=int, default=1, help="Number of addresses to acquire")
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

    def _handle_pool_get_next(self, *args, **options):
        for pool_id in options['pool-id']:
            ip_set = Resource.objects.get(pk=pool_id)
            ip_count = options['count']
            beauty_idx = options['beauty']

            for ip_address in ip_set.available():
                if not ip_count:
                    break

                if ip_address.beauty >= beauty_idx:
                    logger.info("%d\t%s\t%s\t%s" % (ip_address.id, ip_address.parent_id, ip_address, ip_address.status))
                    ip_count -= 1

            if ip_count > 0:
                logger.warning("Pool '%s' have no such many IPs (%d IPs unavailable)" % (ip_set, ip_count + 1))

    def _handle_address_add(self, *args, **options):
        if not IPAddress.is_valid_address(options['ip']):
            raise ValueError("Invalid ip address")

        ip_set = Resource.objects.get(pk=options['pool-id'])

        ips = IPAddress.objects.active(address=options['ip'])
        for ip_address in options['ip']:
            ip_set += ips[0] if len(ips) > 0 else IPAddress.objects.create(address=ip_address)

        self._list_addresses(parent=ip_set.id)

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
        Resource.objects.active(pk=options['pool-id']).delete()

        self._list_pools()

    def _list_addresses(self, **kwargs):
        for ip_address in IPAddress.objects.active(**kwargs):
            logger.info("%d\t%s\t%s\t%s\t%d" % (
                ip_address.id, ip_address.parent_id, ip_address, ip_address.status, ip_address.beauty))

    def _list_pools(self):
        for address_pool in IPAddressPool.get_all_pools():
            logger.info("%d\t%s\t%s\t%s\t%s\t%s" % (
                address_pool.id, address_pool.parent_id, address_pool, address_pool.usage, address_pool.type,
                address_pool.status))

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
