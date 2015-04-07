from argparse import ArgumentParser

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Management commands",
                                           help="Commands help",
                                           dest='subcommand_name',
                                           parser_class=ArgumentParser)

        ip_cmd = subparsers.add_parser('ip', help='ip command help')
        ip_cmd.add_argument("-a", "--add", dest="address", required=True, help="IPv4 or IPv6 address.")
        self.registered_handlers['ip'] = self.handle_ip

        net_cmd = subparsers.add_parser('net', help='net command help')
        net_cmd.add_argument("-a", "--add", dest="network", required=True, help="IPv4 or IPv6 network in CIDR format.")
        self.registered_handlers['net'] = self.handle_net

    def handle(self, *args, **options):
        assert 'subcommand_name' in options.keys(), "subcommand_name must be defined."

        subcommand = options['subcommand_name']
        assert subcommand in self.registered_handlers.keys(), "Subcommand '%s' must be registered." % subcommand

        # call handler
        self.registered_handlers[subcommand](args, options)

    def handle_ip(self, *args, **options):
        print("!!! IP:", args, options)

    def handle_net(self, *args, **options):
        print ("NET: ", args, options)
