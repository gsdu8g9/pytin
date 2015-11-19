from __future__ import unicode_literals

from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.utils import timezone
from prettytable import PrettyTable

from cloud.models import CmdbCloudConfig, TaskTrackerStatus
from cloud.provisioning.backends.proxmox import ProxMoxJBONServiceBackend
from cmdb.settings import logger


class Command(BaseCommand):
    registered_handlers = {}

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout, stderr, no_color)

        self.cloud = CmdbCloudConfig()
        self.task_tracker = self.cloud.task_tracker
        self.backend = ProxMoxJBONServiceBackend(self.cloud)

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="Cloud management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # Tasks
        tracker_cmd_parser = subparsers.add_parser('tracker', help='Manage task trackers.')
        tracker_cmd_parser.add_argument('--new', action="store_true", help="Show submitted tasks.")
        tracker_cmd_parser.add_argument('--failed', action="store_true", help="Show failed tasks.")
        tracker_cmd_parser.add_argument('--success', action="store_true", help="Show success tasks.")
        tracker_cmd_parser.add_argument('--progress', action="store_true", help="Show running tasks.")
        tracker_cmd_parser.add_argument('--limit', type=int, default=10, help="Limit the output.")
        tracker_cmd_parser.add_argument('--attach', type=int, metavar='TRACKER-ID', help="Attach to the task console.")
        tracker_cmd_parser.add_argument('--cancel', type=int, metavar='TRACKER-ID', help="Cancel task.")
        self.register_handler('tracker', self._handle_trackers)

        # Cloud Services
        vps_cmd_parser = subparsers.add_parser('vps', help='Manage VPS services.')
        vps_cmd_parser.add_argument('--create', action="store_true", help="Create VPS server.")
        vps_cmd_parser.add_argument('--start', action="store_true", help="Start VPS server.")
        vps_cmd_parser.add_argument('--stop', action="store_true", help="Stop VPS server.")
        vps_cmd_parser.add_argument('--tech', default='kvm',
                                    help="Hypervisor technology (must be supported by backend).")
        vps_cmd_parser.add_argument('--template', help="VPS template.", default='centos.6.64bit')
        vps_cmd_parser.add_argument('--node', type=int, default=0,
                                    help="CMDB node ID. Scheduling is used if not specified.")
        vps_cmd_parser.add_argument('--vmid', type=int, help="Set ID of the VM..", required=True)
        vps_cmd_parser.add_argument('--user', help="Specify user name for the VM.")
        vps_cmd_parser.add_argument('--ip', help="Specify IP address for the VM.")
        vps_cmd_parser.add_argument('--ram', type=int, help="Set RAM amount (Mb).", default=512)
        vps_cmd_parser.add_argument('--hdd', type=int, help="Set HDD amount (Gb).", default=5)
        vps_cmd_parser.add_argument('--cpu', type=int, help="Number of vCPU cores.", default=1)

        self.register_handler('vps', self._handle_vps)

    def _handle_vps(self, *args, **options):
        tracker = None

        vmid = int(options['vmid'])
        user_name = options['user']
        hyper_tech = options['tech']
        node_id = int(options['node'])

        if options['create']:
            ram = int(options['ram'])
            hdd = int(options['hdd'])
            cpu = int(options['cpu'])
            template = options['template']
            ip_addr = options['ip']

            tracker = self.backend.create_vps(
                node_id=node_id,
                vmid=vmid,
                template=template,
                user=user_name,
                ram=ram,
                hdd=hdd,
                cpu=cpu,
                ip=ip_addr,
                tech=hyper_tech)

        elif options['stop']:
            tracker = self.backend.stop_vps(
                node_id=node_id,
                vmid=vmid,
                user=user_name,
                tech=hyper_tech)

        elif options['start']:
            tracker = self.backend.start_vps(
                node_id=node_id,
                vmid=vmid,
                user=user_name,
                tech=hyper_tech)

        if tracker:
            logger.info("Attached to the task tracker %s. Ctrl-C to exit." % tracker.id)

            try:
                result_data = tracker.get_result()
                logger.info(result_data)
            except Exception, ex:
                logger.error(ex.message)

    def _handle_trackers(self, *args, **options):
        if options['cancel']:
            tracker_id = int(options['cancel'])
            tracker = self.task_tracker.get(tracker_id)
            tracker.failed('Cancelled')
        elif options['attach']:
            tracker_id = int(options['attach'])
            tracker = self.task_tracker.get(tracker_id)

            logger.info("Attached to task tracker %s. Ctrl-C to detach." % tracker_id)
            print tracker.get_result()
        else:
            limit = int(options['limit'])

            view_status = TaskTrackerStatus.STATUS_NEW
            if options['failed']:
                view_status = TaskTrackerStatus.STATUS_FAILED
            elif options['success']:
                view_status = TaskTrackerStatus.STATUS_SUCCESS
            elif options['progress']:
                view_status = TaskTrackerStatus.STATUS_PROGRESS

            self._dump_trackers(view_status, limit)

    def _dump_trackers(self, status, limit):
        trackers = self.task_tracker.find(status=status).order_by('-id')[:limit]

        table = PrettyTable(
            ['id', 'task_class', 'status', 'created', 'updated', 'time-delta'])
        table.padding_width = 1

        for tracker in trackers:
            table.add_row([tracker.id,
                           tracker.task_class,
                           tracker.status,
                           timezone.localtime(tracker.created_at).strftime('%d.%m.%Y %H:%M'),
                           timezone.localtime(tracker.updated_at).strftime('%d.%m.%Y %H:%M'),
                           (tracker.updated_at - tracker.created_at) if tracker.updated_at else '0'
                           ])

        logger.info(unicode(table))

    def handle(self, *args, **options):
        subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
