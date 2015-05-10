from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from ipman.models import IPNetworkPool, IPAddressPool, IPAddressRangePool
from resources.models import Resource


class Command(BaseCommand):
    """
    ipmanctl ippool --addiplist IP [ IP IP ]
    ipmanctl ippool --addcidr CIDRNET
    ipmanctl ippool --addrange START_IP END_IP
    ipmanctl ippool list [-f FILTER -t TYPE]  # search
    ipmanctl ippool --delete ID
    ipmanctl ippool --edit ID (--addip IP | --delip IP )
    """

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
                                           dest='subcommand_name',
                                           parser_class=ArgumentParser)

        # filtered list
        pool_cmd_parser = subparsers.add_parser('pool', help='Manage address pools')
        self._register_handler('pool', self._handle_pool)

        mutual_group = pool_cmd_parser.add_mutually_exclusive_group()
        mutual_group.add_argument("-l", "--list", dest="list_filter", action='store_true',
                                  help="List all or search pools. Filter example: +Django -jazz Python")
        mutual_group.add_argument("--addcidr", dest="pool_addcidr",
                                  help="Add IP address pool by CIDR network: 192.168.1.0/23")
        mutual_group.add_argument("--delete", dest="pool_deleteid",
                                  help="Remove network pool by ID with connected IPs")

    def handle(self, *args, **options):
        assert 'subcommand_name' in options, "subcommand_name must be defined."

        subcommand = options['subcommand_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_pool(self, *args, **options):
        print 'args: ', args, 'options: ', options

        result_list = []

        if options['pool_deleteid']:
            Resource.objects.active(pk=options['pool_deleteid']).delete()
        elif options['pool_addcidr']:
            IPNetworkPool.create(network=options['pool_addcidr'])

        for ip_pool_type in self.ip_pool_types:
            result_list.extend(ip_pool_type.objects.active())

        for address in result_list:
            print str(address)

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
