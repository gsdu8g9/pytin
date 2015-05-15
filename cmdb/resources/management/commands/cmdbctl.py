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
            print "%d\t%s\t%s\t%s\t%s" % (resource.id, resource.parent_id, resource.name, resource.type, resource.status)

    def _handle_res_get_options(self, *args, **options):
        ip_pool = Resource.objects.get(pk=options['resource-id'])

        for option in ip_pool.get_options():
            print option

    def _handle_res_set_options(self, *args, **options):
        ip_pool = Resource.objects.get(pk=options['resource-id'])

        ip_pool.set_option(options['option-name'], options['option-value'])

        for option in ip_pool.get_options():
            print option

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
