from argparse import ArgumentParser
import argparse

from django.core.management.base import BaseCommand

from django.utils import timezone

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
        res_list_cmd = subparsers.add_parser('list', help="Get events list.")
        res_list_cmd.add_argument('--limit', type=int, default=0, help="Limit output.")
        res_list_cmd.add_argument('--page', type=int, default=1, help="Page number to paginate resource list (from 1).")
        res_list_cmd.add_argument('filter', nargs=argparse.REMAINDER, help="Key=Value pairs.")
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

        events_set = HistoryEvent.objects.filter(**query).order_by('-created_at')

        if limit > 0:
            events_set = events_set[offset:limit]

        row_format = '%15s %5s %11s %15s %15s %25s %25s'
        logger.info(row_format % ('DATE', 'TYPE', 'RES_ID', 'RES_TYPE', 'FIELD', 'OLD', 'NEW'))
        for event in events_set:
            logger.info(row_format % (
                timezone.localtime(event.created_at).strftime('%d.%m.%Y %H:%M'), event.type, event.resource.id,
                event.resource.type, event.field_name, event.field_old_value,
                event.field_new_value))

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
