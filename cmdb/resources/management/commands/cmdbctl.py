from __future__ import unicode_literals

import argparse
from argparse import ArgumentParser

from django.apps import apps
from django.core.management.base import BaseCommand

from cmdb.settings import logger
from resources.iterators import PathIterator, TreeIterator
from resources.lib.console import ConsoleResourceWriter
from resources.models import Resource, ResourceOption, ModelFieldChecker


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Resource low level management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # GET
        res_get_cmd = subparsers.add_parser('get', help="Get resource details.")
        res_get_cmd.add_argument('resource-id', type=int, nargs='+', help="ID of the resource.")
        res_get_cmd.add_argument('-p', '--path', action='store_true',
                                 help="Display path from the root node to resource-id.")
        res_get_cmd.add_argument('-t', '--tree', action='store_true', help="Display the tree of childs.")
        res_get_cmd.add_argument('-f', '--show-fields', default='id,name,status', help="Comma separated field list:\
                                                    supported fields are from the resource.")
        self._register_handler('get', self._handle_command_get)

        # SET
        res_set_cmd = subparsers.add_parser('set', help="Edit resource options.")
        res_set_cmd.add_argument('resource-id', type=int, help="ID of the resource.")
        res_set_cmd.add_argument('-c', '--cascade', action='store_true',
                                 help="Use cascade  updates, where appropriate.")
        res_set_cmd.add_argument('-f', '--format', '--option-format', help="Type of the values.",
                                 default=ResourceOption.FORMAT_STRING,
                                 choices=[choice[0] for choice in ResourceOption.FORMAT_CHOICES])

        stat_group = res_set_cmd.add_mutually_exclusive_group()
        stat_group.add_argument('--use', action='store_true', help="Mark resource and its childs as used.")
        stat_group.add_argument('--free', action='store_true', help="Mark resource and its childs as free.")
        stat_group.add_argument('--lock', action='store_true', help="Mark resource and its childs as locked.")

        res_set_cmd.add_argument('fields', nargs=argparse.ZERO_OR_MORE, help="Key=Value pairs.")
        self._register_handler('set', self._handle_command_set)

        # SEARCH
        res_list_cmd = subparsers.add_parser('search', help="Search for resources.")
        res_list_cmd.add_argument('-l', '--limit', type=int, default=0, help="Limit the resources output.")
        res_list_cmd.add_argument('-p', '--page', type=int, default=1,
                                  help="Page number to paginate resource list (from 1).")
        res_list_cmd.add_argument('-o', '--order', default='id', help="Field name to order by.")
        res_list_cmd.add_argument('-f', '--show-fields', default='id,self,status', help="Comma separated field list:\
                                                    supported fields are from the resource.")
        res_list_cmd.add_argument('-s', '--status',
                                  help="Comma separated statuses of the resource. If status is used, "
                                       "you can search in deleted resources.",
                                  choices=[choice[0] for choice in Resource.STATUS_CHOICES])
        res_list_cmd.add_argument('--index', action="store_true",
                                  help="Update name fields of the resources.")
        res_list_cmd.add_argument('filter', nargs=argparse.ZERO_OR_MORE, help="Key=Value pairs.")
        self._register_handler('search', self._handle_command_search)

        # ADD
        res_add_cmd = subparsers.add_parser('add', help="Add the new resource.")
        res_add_cmd.add_argument('-t', '--type', default='resources.Resource',
                                 help="Type of the resource in format 'app.model'.")
        res_add_cmd.add_argument('fields', nargs=argparse.ONE_OR_MORE, help="Key=Value pairs.")
        self._register_handler('add', self._handle_command_add)

        # DELETE
        res_delete_cmd = subparsers.add_parser('delete', help="Delete resource objects.")
        res_delete_cmd.add_argument('resource-id', type=int, nargs='+', help="IDs of the resources to delete.")
        self._register_handler('delete', self._handle_command_delete)

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_command_delete(self, *args, **options):
        for res_id in options['resource-id']:
            resource = Resource.active.get(pk=res_id)
            resource.delete()

    def _handle_command_add(self, *args, **options):
        parsed_data = self._parse_reminder_arguments(options['fields'])

        requested_model = Resource
        if options['type']:
            requested_model = apps.get_model(options['type'])

        if 'parent' in parsed_data:
            field_name, field_value = self._normalize_parent_field(parsed_data['parent'])
            if 'parent' in parsed_data:
                del parsed_data['parent']
            if 'parent_id' in parsed_data:
                del parsed_data['parent_id']
            parsed_data[field_name] = field_value

        if 'id' in parsed_data and Resource.active.filter(pk=parsed_data['id']).exists():
            raise Exception("Item with ID %s is already exists." % parsed_data['id'])

        resource = requested_model.objects.create(**parsed_data)
        resource.refresh_from_db()

        ConsoleResourceWriter.dump_item(resource)

    def _handle_command_search(self, *args, **options):
        query = self._parse_reminder_arguments(options['filter'])

        if options['index']:
            updated = 0
            for resource in Resource.active.all():
                resource.name = unicode(resource)
                resource.save()

            logger.debug("Updated resources: %s" % updated)
            return

        # apply status
        if not options['status']:
            resource_set = Resource.active.filter(**query)
        else:
            query['status__in'] = options['status'].split(',')
            resource_set = Resource.objects.filter(**query)

        # order by
        table_sort_by_field = None
        if options['order']:
            fields = options['order'].split(',')
            for field_name in fields:
                if not ModelFieldChecker.is_model_field(Resource, field_name):
                    table_sort_by_field = field_name
                    break

            if not table_sort_by_field:
                resource_set = resource_set.order_by(*fields)

        # apply limits
        limit = options['limit']
        offset = (options['page'] - 1) * limit
        if limit > 0:
            resource_set = resource_set[offset:limit]

        # tabular output with column align
        show_fields = options['show_fields'].split(',')

        console_writer = ConsoleResourceWriter(resource_set)
        console_writer.print_table(show_fields, sort_by=table_sort_by_field)

    def _handle_command_get(self, *args, **options):
        show_fields = options['show_fields'].split(',')

        for res_id in options['resource-id']:
            resource = Resource.objects.get(pk=res_id)

            if options['path']:
                console_printer = ConsoleResourceWriter(PathIterator(resource))
                console_printer.print_path(show_fields)
            elif options['tree']:
                console_printer = ConsoleResourceWriter(TreeIterator(resource))
                console_printer.print_tree(show_fields)
            else:
                ConsoleResourceWriter.dump_item(resource)

    def _handle_command_set(self, *args, **options):
        res_id = options['resource-id']
        resource = Resource.objects.get(pk=res_id)

        update_query = self._parse_reminder_arguments(options['fields'])
        for field_name in update_query:
            field_value = update_query[field_name]

            if field_name in ['parent', 'parent_id']:
                field_name, field_value = self._normalize_parent_field(field_value)

            if field_name == 'type':
                requested_model = apps.get_model(field_value)
                resource = resource.cast_type(requested_model)
            elif ModelFieldChecker.is_field_or_property(resource, field_name):
                setattr(resource, field_name, field_value)
                resource.save()
            else:
                if field_value:
                    resource.set_option(name=field_name,
                                        value=field_value,
                                        format=options['format'] if options['format'] else ResourceOption.FORMAT_STRING)
                elif resource.get_option_value(field_name, default=None):
                    resource.get_option(field_name).delete()  # delete option

        cascade = options['cascade']
        if options['use']:
            resource.use(cascade=cascade)
        elif options['free']:
            resource.free(cascade=cascade)
        elif options['lock']:
            resource.lock(cascade=cascade)

        ConsoleResourceWriter.dump_item(resource)

    def _normalize_parent_field(self, parent_value):
        """
        Process field 'parent' and convert in to parent_id if necessary. Also translate value to None when appropriate.
        :param parent_value: Value of the field 'parent'
        :return: touple  (field_name, field_value)
        """
        field_value = parent_value

        try:
            field_value = int(field_value)
            if not field_value:
                raise ValueError()
            field_name = 'parent_id'
        except ValueError:
            field_name = 'parent'
            field_value = None

        return field_name, field_value

    def _parse_reminder_arguments(self, reminder_args):
        """
        Parses name=value arguments, such as filters and set attributes.
            cmd --arg1=val1 --arg2=vl2 reminder_arg1=val1 ... reminder_argN=valN
        :param reminder_args: array of reminder command line arguments
        :return: name=value dict from arguments
        """
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
