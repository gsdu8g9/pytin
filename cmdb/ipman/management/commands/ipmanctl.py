from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from ipman.models import IPNetworkPool, IPAddressPool, IPAddressRangePool, IPAddress
from resources.models import Resource, ResourceOption


class Command(BaseCommand):
    ip_pool_types = [
        IPAddressPool.__name__,
        IPAddressRangePool.__name__,
        IPNetworkPool.__name__
    ]

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
        addr_add_cmd.add_argument('pool-id', help="ID of the pool")
        addr_add_cmd.add_argument('ip', nargs='+', help="IP address to add to pool")
        self._register_handler('address.add', self._handle_address_add)

        addr_list_cmd = address_subparsers.add_parser('list', help="List addresses")
        addr_list_cmd.add_argument('--pool-id', help="ID of the pool")
        addr_list_cmd.add_argument('--status', help="Status of the IP")
        addr_list_cmd.add_argument('--address', help="Search in address")
        self._register_handler('address.list', self._handle_address_list)

        addr_del_cmd = address_subparsers.add_parser('delete', help="Delete address")
        addr_del_cmd.add_argument('address-id', help="ID of the address")
        self._register_handler('address.delete', self._handle_delete_address)


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

        add_cidr_cmd = pool_subparsers.add_parser('delete', help="Delete pool")
        add_cidr_cmd.add_argument('pool-id', help="ID of the pool")
        self._register_handler('pool.delete', self._handle_delete_pool)

        pool_subparsers.add_parser('list', help="List pools")
        self._register_handler('pool.list', self._handle_list_pools)

        # Common operatoins (move to resources?)
        res_get_cmd = subparsers.add_parser('get', help="Get resource options")
        res_get_cmd.add_argument('resource-id', help="ID of the resource")
        self._register_handler('get', self._handle_res_get_options)

        res_set_cmd = subparsers.add_parser('set', help="Set resource options")
        res_set_cmd.add_argument('resource-id', help="ID of the resource")
        res_set_cmd.add_argument('option-name', help="Name of the option")
        res_set_cmd.add_argument('option-value', help="Value of the option")
        res_set_cmd.add_argument('--format', '--option-format', help="Type of the value",
                                 default=ResourceOption.FORMAT_STRING,
                                 choices=[ResourceOption.FORMAT_STRING, ResourceOption.FORMAT_INT,
                                          ResourceOption.FORMAT_FLOAT, ResourceOption.FORMAT_DICT])
        self._register_handler('set', self._handle_res_set_options)

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_delete_address(self, *args, **options):
        address = Resource.objects.get(pk=options['address-id'])

        address.delete()

        if address.parent_id > 0:
            self._list_addresses(address.parent_id)

    def _handle_address_list(self, *args, **options):
        supported_fields = ['status', 'address']

        query_fields = []
        for option_name in options:
            for supported_field in supported_fields:
                if option_name.startswith(supported_field):
                    query_fields.append(option_name)

        query = {}
        for field in query_fields:
            if options[field] is not None:
                query[field] = options[field]

        self._list_addresses(options['pool_id'], **query)

    def _handle_address_add(self, *args, **options):
        ip_set = Resource.objects.get(pk=options['pool-id'])

        for ip_address in options['ip']:
            ip_set += IPAddress.create(address=ip_address)

        self._list_addresses(ip_set.id)

    def _handle_res_get_options(self, *args, **options):
        ip_pool = Resource.objects.get(pk=options['resource-id'])

        for option in ip_pool.get_options():
            print option

    def _handle_res_set_options(self, *args, **options):
        ip_pool = Resource.objects.get(pk=options['resource-id'])

        ip_pool.set_option(options['option-name'], options['option-value'])

        for option in ip_pool.get_options():
            print option

    def _handle_pool_addnamed(self, *args, **options):
        IPAddressPool.create(name=options['pool-name'])

        self._list_pools()

    def _handle_list_pools(self, *args, **options):
        self._list_pools()

    def _handle_delete_pool(self, *args, **options):
        Resource.objects.active(pk=options['pool-id']).delete()

        self._list_pools()

    def _handle_pool_addcidr(self, *args, **options):
        IPNetworkPool.create(network=options['net'])

        self._list_pools()

    def _handle_pool_addrange(self, *args, **options):
        print args, options

        IPAddressRangePool.create(range_from=options['ip-start'], range_to=options['ip-end'])

        self._list_pools()

    def _list_addresses(self, pool_id, **kwargs):
        assert pool_id > 0, "pool_id must be defined."

        query = {'parent': pool_id}

        query.update(kwargs)

        for ip_address in IPAddress.objects.active(**query):
            print "%d\t%d\t%s\t%s" % (ip_address.id, ip_address.parent_id, ip_address, ip_address.status)

    def _list_pools(self):
        for address_pool in Resource.objects.active(type__in=self.ip_pool_types):
            print "%d\t%s\t%s\t%s" % (address_pool.id, address_pool, address_pool.usage, address_pool.type)

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
