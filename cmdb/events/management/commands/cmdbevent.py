from __future__ import unicode_literals
from argparse import ArgumentParser
import argparse

from django.core.exceptions import ObjectDoesNotExist

from django.core.management.base import BaseCommand
from django.utils import timezone
from prettytable import PrettyTable

from cmdb.settings import logger

from events.models import HistoryEvent


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Events management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # Common operatoins
        event_list_cmd = subparsers.add_parser('list', help="Get events list.")
        event_list_cmd.add_argument('--limit', type=int, default=0, help="Limit output.")
        event_list_cmd.add_argument('--page', type=int, default=1,
                                    help="Page number to paginate resource list (from 1).")
        event_list_cmd.add_argument('--order', default='-id', help="Field name to order by.")
        event_list_cmd.add_argument('--from-date', default='',
                                    help="Get events from the specified date and time (format: d.m.Y H:M).")
        event_list_cmd.add_argument('filter', nargs=argparse.ZERO_OR_MORE, help="Key=Value pairs.")
        self._register_handler('list', self._handle_res_list)

    def handle(self, *args, **options):
        if 'subcommand_name' in options:
            subcommand = "%s.%s" % (options['manager_name'], options['subcommand_name'])
        else:
            subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_res_list(self, *args, **options):
        query = self._parse_reminder_arg(options['filter'])

        limit = options['limit']
        offset = (options['page'] - 1) * limit

        events_set = HistoryEvent.objects.filter(**query)

        if options['from_date']:
            events_begin_date = timezone.datetime.strptime(options['from_date'], '%d.%m.%Y %H:%M')
            events_set = events_set.filter(created_at__gte=events_begin_date)

        if options['order']:
            fields = options['order'].split(',')
            events_set = events_set.order_by(*fields)

        if limit > 0:
            events_set = events_set[offset:limit]

        table = PrettyTable(
            ['id', 'created_at', 'type', 'resource_id', 'resource__type', 'field_name', 'field_old_value',
             'field_new_value'])
        table.padding_width = 1
        table.align['id'] = 'r'
        table.align['resource_id'] = 'r'
        table.align['resource_type'] = 'l'
        table.align['field_name'] = 'l'
        table.align['field_old_value'] = 'l'
        table.align['field_new_value'] = 'l'

        for event in events_set:
            try:
                table.add_row([event.id,
                               timezone.localtime(event.created_at).strftime('%d.%m.%Y %H:%M'),
                               event.type,
                               event.resource.id, event.resource.type,
                               event.field_name, event.field_old_value, event.field_new_value])
            except ObjectDoesNotExist:
                logger.debug("Removing event %s with missing resource %s" % (event.id, event.resource_id))
                event.delete()

        logger.info(unicode(table))

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
