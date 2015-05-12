from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from ipman.models import IPNetworkPool, IPAddressPool, IPAddressRangePool, IPAddress
from resources.models import Resource


class Command(BaseCommand):
    ip_pool_types = [
        IPAddressPool,
        IPAddressRangePool,
        IPNetworkPool
    ]

    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """

        subparsers = parser.add_subparsers(title="Management commands",
                                           help="Commands help",
                                           parser_class=ArgumentParser)

        # POOL commands
        pool_cmd_parser = subparsers.add_parser('pool', help='Manage address pools')

        pool_subparsers = pool_cmd_parser.add_subparsers(title="Pool management commands",
                                                         help="Commands help",
                                                         dest='subcommand_name',
                                                         parser_class=ArgumentParser)

        add_cidr_cmd = pool_subparsers.add_parser('addcidr', help="Add pool by network")
        add_cidr_cmd.add_argument('net', help="CIDR network")
        self._register_handler('addcidr', self._handle_addcidr)

        add_cidr_cmd = pool_subparsers.add_parser('addrange', help="Add pool by range")
        add_cidr_cmd.add_argument('ip-start', help="IP range start")
        add_cidr_cmd.add_argument('ip-end', help="IP range end")
        self._register_handler('addrange', self._handle_addrange)

        add_cidr_cmd = pool_subparsers.add_parser('addnamed', help="Add named pool")
        add_cidr_cmd.add_argument('pool-name', help="Name of the pool. It holds arbitrary IPs.")
        self._register_handler('addnamed', self._handle_addnamed)

        add_cidr_cmd = pool_subparsers.add_parser('addip', help="Add pool by IP")
        add_cidr_cmd.add_argument('pool-id', help="ID or the pool")
        add_cidr_cmd.add_argument('ip', nargs='+', help="IP address to add to pool")
        self._register_handler('addip', self._handle_addip)

        add_cidr_cmd = pool_subparsers.add_parser('delete', help="Delete pool")
        add_cidr_cmd.add_argument('pool-id', help="ID of the pool")
        self._register_handler('delete', self._handle_delete_pool)

        add_cidr_cmd = pool_subparsers.add_parser('list', help="List pools")
        self._register_handler('list', self._handle_list_pools)

        add_cidr_cmd = pool_subparsers.add_parser('get', help="Get resource options")
        add_cidr_cmd.add_argument('pool-id', help="ID of the pool")
        self._register_handler('get', self._handle_get_options)

        add_cidr_cmd = pool_subparsers.add_parser('set', help="Set resource options")
        add_cidr_cmd.add_argument('pool-id', help="ID of the pool")
        add_cidr_cmd.add_argument('option-name', help="Name of the option")
        add_cidr_cmd.add_argument('option-value', help="Value of the option")
        self._register_handler('set', self._handle_set_options)

    def handle(self, *args, **options):
        assert 'subcommand_name' in options, "subcommand_name must be defined."

        subcommand = options['subcommand_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_get_options(self, *args, **options):
        ip_pool = Resource.objects.get(pk=options['pool-id'])

        for option in ip_pool.get_options():
            print option

    def _handle_set_options(self, *args, **options):
        ip_pool = Resource.objects.get(pk=options['pool-id'])

        ip_pool.set_option(options['option-name'], options['option-value'])

    def _handle_addip(self, *args, **options):
        ip_set = IPAddressPool.objects.get(pk=options['pool-id'])

        for ip_address in options['ip']:
            ip_set += IPAddress.create(address=ip_address)

        self._list_pools()

    def _handle_addnamed(self, *args, **options):
        IPAddressPool.create(name=options['pool-name'])

        self._list_pools()

    def _handle_list_pools(self, *args, **options):
        self._list_pools()

    def _handle_delete_pool(self, *args, **options):
        Resource.objects.active(pk=options['pool-id']).delete()

        self._list_pools()

    def _handle_addcidr(self, *args, **options):
        IPNetworkPool.create(network=options['net'])

        self._list_pools()

    def _handle_addrange(self, *args, **options):
        print args, options

        IPAddressRangePool.create(range_from=options['ip-start'], range_to=options['ip-end'])

        self._list_pools()

    def _list_pools(self):
        result_list = []
        for ip_pool_type in self.ip_pool_types:
            result_list.extend(ip_pool_type.objects.active())

        for address_pool in result_list:
            print "%d\t%s\t%s" % (address_pool.id, address_pool, address_pool.type)

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
