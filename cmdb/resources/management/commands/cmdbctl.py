from argparse import ArgumentParser
import argparse

from django.core.management.base import BaseCommand

from django.apps import apps
from django.utils import timezone
from cmdb.settings import logger

from resources.iterators import PathIterator, TreeIterator
from resources.models import Resource, ResourceOption, ModelFieldChecker


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
        res_get_cmd = subparsers.add_parser('get', help="Get resource options.")
        res_get_cmd.add_argument('resource-id', type=int, nargs='+', help="ID of the resource.")
        res_get_cmd.add_argument('-p', '--path', action='store_true',
                                 help="Display path from root node to resource-id.")
        res_get_cmd.add_argument('-t', '--tree', action='store_true', help="Display the tree of childs.")
        self._register_handler('get', self._handle_res_get_options)

        res_set_cmd = subparsers.add_parser('set', help="Set resource options.")
        res_set_cmd.add_argument('resource-id', type=int, nargs='+', help="ID of the resource.")
        res_set_cmd.add_argument('-n', '--option-name', help="Name of the option.")
        res_set_cmd.add_argument('-v', '--option-value', type=str, help="Value of the option.")
        res_set_cmd.add_argument('--format', '--option-format', help="Type of the value.",
                                 default=ResourceOption.FORMAT_STRING,
                                 choices=[choice[0] for choice in ResourceOption.FORMAT_CHOICES])
        res_set_cmd.add_argument('--cascade', action='store_true', help="Update resource and its childs.")
        stat_group = res_set_cmd.add_mutually_exclusive_group()
        stat_group.add_argument('--use', action='store_true', help="Mark resource and its childs as used.")
        stat_group.add_argument('--free', action='store_true', help="Mark resource and its childs as free.")
        stat_group.add_argument('--lock', action='store_true', help="Mark resource and its childs as locked.")
        self._register_handler('set', self._handle_res_set_options)

        res_list_cmd = subparsers.add_parser('list', help="Get resource list.")
        res_list_cmd.add_argument('--limit', type=int, default=0, help="Limit the resources output.")
        res_list_cmd.add_argument('--page', type=int, default=1, help="Page number to paginate resource list (from 1).")
        res_list_cmd.add_argument('--status', help="Status of the IP",
                                  choices=[choice[0] for choice in Resource.STATUS_CHOICES])
        res_list_cmd.add_argument('filter', nargs=argparse.REMAINDER, help="Key=Value pairs.")
        self._register_handler('list', self._handle_res_list)

        res_add_cmd = subparsers.add_parser('add', help="Add the new resource.")
        res_add_cmd.add_argument('--type', default='resources.Resource',
                                 help="Type of the resource in format 'app.model'.")
        res_add_cmd.add_argument('--outid', action='store_true', help="Print only new resource ID.")
        res_add_cmd.add_argument('fields', nargs=argparse.REMAINDER, help="Key=Value pairs.")
        self._register_handler('add', self._handle_res_add)

        res_delete_cmd = subparsers.add_parser('delete', help="Delete resource objects.")
        res_delete_cmd.add_argument('resource-id', type=int, nargs='+', help="IDs of the resources to delete.")
        res_delete_cmd.add_argument('--purge', action='store_true', help="Remove object from DB.")
        res_delete_cmd.add_argument('--cascade', action='store_true',
                                    help="Mark the resource as deleted and all its childs.")
        self._register_handler('delete', self._handle_res_delete)

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_res_delete(self, *args, **options):
        for res_id in options['resource-id']:
            resource = Resource.objects.get(pk=res_id)
            resource.delete(purge=options['purge'], cascade=options['cascade'])

    def _handle_res_add(self, *args, **options):
        parsed_data = self._parse_reminder_arg(options['fields'])

        requested_model = Resource
        if options['type']:
            requested_model = apps.get_model(options['type'])

        if 'parent' in parsed_data:
            parsed_data['parent_id'] = parsed_data['parent']
            del parsed_data['parent']

        if 'id' in parsed_data and Resource.objects.active(pk=parsed_data['id']).exists():
            raise Exception("Item with ID %s is already exists." % parsed_data['id'])

        resource = requested_model.create(**parsed_data)
        resource.refresh_from_db()

        if options['outid']:
            logger.info(resource.id)
        else:
            self._print_resource_data(resource)

    def _handle_res_list(self, *args, **options):
        query = self._parse_reminder_arg(options['filter'])

        limit = options['limit']
        offset = (options['page'] - 1) * limit

        if not options['status']:
            resource_set = Resource.objects.active(**query)
        else:
            query['status'] = options['status']
            resource_set = Resource.objects.filter(**query)

        if limit > 0:
            resource_set = resource_set[offset:limit]

        row_format = '%5s%11s%35s%20s%10s'
        logger.info(row_format % ('ID', 'parent_id', 'name', 'type', 'status'))
        for resource in resource_set:
            logger.info(row_format % (
                resource.id, resource.parent_id, resource, resource.type, resource.status))

    def _handle_res_get_options(self, *args, **options):
        for res_id in options['resource-id']:
            resource = Resource.objects.get(pk=res_id)

            if options['path']:
                indent = 0
                for inner_resource in PathIterator(resource):
                    self._print_resource_data(inner_resource, indent)
                    indent += 8
            elif options['tree']:
                for inner_resource, level in TreeIterator(resource):
                    indent = (8 * (level - 1))
                    self._print_resource_data(inner_resource, indent)
            else:
                self._print_resource_data(resource)

    def _handle_res_set_options(self, *args, **options):
        for res_id in options['resource-id']:
            resource = Resource.objects.get(pk=res_id)

            if options['option_name'] and options['option_value']:
                if options['option_name'] == 'parent':
                    options['option_name'] = 'parent_id'

                if options['option_name'] == 'type':
                    requested_model = apps.get_model(options['option_value'])
                    resource = resource.cast_type(requested_model)
                elif ModelFieldChecker.is_field_or_property(resource, options['option_name']):
                    setattr(resource, options['option_name'], options['option_value'])
                    resource.save()
                else:
                    resource.set_option(name=options['option_name'],
                                        value=options['option_value'],
                                        format=options['format'] if options['format'] else ResourceOption.FORMAT_STRING)
            elif options['use']:
                resource.use(cascade=options['cascade'])
            elif options['free']:
                resource.free(cascade=options['cascade'])
            elif options['lock']:
                resource.lock(cascade=options['cascade'])

            self._print_resource_data(resource)

    def _print_resource_data(self, resource, indent=0):
        padding = "".ljust(indent, ' ')

        logger.info("%s|-------------------" % padding)
        logger.info("%s|%d\t%s\t%s\t%s\t%s]" % (
            padding, resource.id, resource.parent_id, resource.type, resource, resource.status))
        logger.info("%s|:created_at = %s" % (padding, timezone.localtime(resource.created_at)))
        logger.info("%s|:updated_at = %s" % (padding, timezone.localtime(resource.updated_at)))
        logger.info("%s|:last_seen = %s" % (padding, timezone.localtime(resource.last_seen)))

        for option in resource.get_options():
            logger.info("%s|%s" % (padding, option))

    def _parse_reminder_arg(self, reminder_args):
        query = {}
        for filter_item in reminder_args:
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

        return query

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
