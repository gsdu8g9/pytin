from __future__ import unicode_literals

from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from pyzabbix import ZabbixAPI

from cmdb.settings import logger, ZABBIX_APP
from resources.models import Resource, ResourceOption
from zabbix.models import ZabbixMetric


class Command(BaseCommand):
    registered_handlers = {}

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout, stderr, no_color)

        self.zapi = ZabbixAPI(ZABBIX_APP['SERVER_URL'])
        self.zapi.login(ZABBIX_APP['USER'], ZABBIX_APP['PASSWORD'])

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Zabbix integration management commands.",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # Tasks
        tracker_cmd_parser = subparsers.add_parser('metric', help='Manage host metrics.')
        tracker_cmd_parser.add_argument('--cmdb-node', type=int, help="CMDB node ID.")
        tracker_cmd_parser.add_argument('--zbx-item', type=int, help="Zabbix item ID (metric).")
        tracker_cmd_parser.add_argument('--populate', metavar='cmdb-attr',
                                        help="Create or update CMDB node attribute from the Zabbix metric.")
        tracker_cmd_parser.add_argument('--delete', action="store_true", help="Delete linked Zabbix item.")
        tracker_cmd_parser.add_argument('--list', action="store_true", help="List linked Zabbix items.")
        tracker_cmd_parser.add_argument('--auto-poll', action="store_true", help="Poll all linked metrics.")
        self.register_handler('metric', self._handle_metrics)

    def _handle_metrics(self, *args, **options):

        if options['auto_poll']:
            for linked_metric in ZabbixMetric.objects.filter(cmdb_node_option__resource__status=Resource.STATUS_INUSE):
                cmdb_node = linked_metric.cmdb_node_option.resource
                cmdb_attr = linked_metric.cmdb_node_option.name
                metric_id = linked_metric.zbx_metric_id

                logger.info("Auto populate %s.%s from Zabbix item %s." % (cmdb_node.id, cmdb_attr, metric_id))

                linked_metric = self._populate_attribute(cmdb_node, cmdb_attr, metric_id)
                logger.info(linked_metric)

        elif options['list']:
            logger.info("Linked metrics:")
            for linked_metric in ZabbixMetric.objects.filter():
                logger.info(linked_metric)

        elif options['delete']:
            assert options['zbx_item']
            metric_id = int(options['zbx_item'])

            ZabbixMetric.objects.filter(zbx_metric_id=metric_id).delete()

        elif options['populate']:
            assert options['cmdb_node']
            assert options['zbx_item']

            metric_id = int(options['zbx_item'])
            cmdb_node_id = int(options['cmdb_node'])
            cmdb_attr = options['populate']

            cmdb_node = Resource.active.get(pk=cmdb_node_id)

            logger.info("Populate %s.%s from zabbix item %s" % (cmdb_node.id, cmdb_attr, metric_id))

            linked_metric = self._populate_attribute(cmdb_node, cmdb_attr, metric_id)

            logger.info(linked_metric)

    def _populate_attribute(self, cmdb_node, cmdb_node_attr, zbx_metric_id):
        assert cmdb_node
        assert cmdb_node_attr
        assert zbx_metric_id > 0

        zbx_metrics = self.zapi.item.get(itemids=[zbx_metric_id])
        if len(zbx_metrics) <= 0:
            raise Exception("Zabbix metric %s is not found." % zbx_metric_id)

        zbx_metric = zbx_metrics[0]

        val_format = ResourceOption.FORMAT_STRING
        if zbx_metric['value_type'] == '3':
            val_format = ResourceOption.FORMAT_INT
        elif zbx_metric['value_type'] == '0':
            val_format = ResourceOption.FORMAT_FLOAT

        zbx_last_value = zbx_metric['lastvalue']

        cmdb_node.set_option(cmdb_node_attr, zbx_last_value, format=val_format)

        linked_metric, created = ZabbixMetric.objects.update_or_create(
            cmdb_node_option=cmdb_node.get_option(cmdb_node_attr),
            zbx_metric_id=zbx_metric_id
        )

        return linked_metric

    def handle(self, *args, **options):
        subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
