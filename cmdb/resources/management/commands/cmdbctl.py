from argparse import ArgumentParser
import argparse

from django.core.management.base import BaseCommand

from resources.models import Resource, ResourceOption


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """

        subparsers = parser.add_subparsers(title="Resources management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # Common operatoins
        res_get_cmd = subparsers.add_parser('get', help="Get resource options")
        res_get_cmd.add_argument('resource-id', nargs='+', help="ID of the resource")
        self._register_handler('get', self._handle_res_get_options)

        res_set_cmd = subparsers.add_parser('set', help="Set resource options")
        res_set_cmd.add_argument('resource-id', nargs='+', help="ID of the resource")
        res_set_cmd.add_argument('-n', '--option-name', help="Name of the option")
        res_set_cmd.add_argument('-v', '--option-value', help="Value of the option")
        res_set_cmd.add_argument('--format', '--option-format', help="Type of the value",
                                 default=ResourceOption.FORMAT_STRING,
                                 choices=[choice[0] for choice in ResourceOption.FORMAT_CHOICES])
        stat_group = res_set_cmd.add_mutually_exclusive_group()
        stat_group.add_argument('--use', action='store_true', help="Mark resource and its childs as used")
        stat_group.add_argument('--free', action='store_true', help="Mark resource and its childs as free")
        stat_group.add_argument('--lock', action='store_true', help="Mark resource and its childs as locked")
        self._register_handler('set', self._handle_res_set_options)

        res_list_cmd = subparsers.add_parser('list', help="Get resource list")
        res_list_cmd.add_argument('filter', nargs=argparse.REMAINDER)
        self._register_handler('list', self._handle_res_list)

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_res_list(self, *args, **options):
        query = {}
        for filter_item in options['filter']:
            field_name, field_value = filter_item.split('=')
            field_name = field_name.strip()
            field_value = field_value.strip()

            if field_name.endswith('__in'):
                if field_name not in query:
                    query[field_name] = [field_value]
                else:
                    query[field_name].append(field_value)
            else:
                query[field_name] = field_value

        for resource in Resource.objects.filter(**query):
            print "%d\t%s\t%s\t%s\t%s" % (
                resource.id, resource.parent_id, resource.name, resource.type, resource.status)

    def _handle_res_get_options(self, *args, **options):
        for res_id in options['resource-id']:
            ip_pool = Resource.objects.get(pk=res_id)

            for option in ip_pool.get_options():
                print option

    def _handle_res_set_options(self, *args, **options):
        for res_id in options['resource-id']:
            ip_resource = Resource.objects.get(pk=res_id)

            if options['option_name'] and options['option_value']:
                ip_resource.set_option(name=options['option_name'],
                                       value=options['option_value'],
                                       format=options['option_format'] if options[
                                           'option_format'] else ResourceOption.FORMAT_STRING)
            elif options['use']:
                ip_resource.use()
            elif options['free']:
                ip_resource.free()
            elif options['lock']:
                ip_resource.lock()

            for option in ip_resource.get_options():
                print option

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
