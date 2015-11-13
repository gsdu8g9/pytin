from __future__ import unicode_literals

import time

from celery import Celery

from cloud.provisioning import HypervisorBackend, CloudTask
from cmdb.settings import logger, PROXMOX_BACKEND

agentd_proxy = Celery('agentd',
                      broker=PROXMOX_BACKEND['MSG_BROKER'],
                      backend=PROXMOX_BACKEND['MSG_BACKEND'])

agentd_proxy.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TIMEZONE='Europe/Moscow',
    CELERY_ENABLE_UTC=True
)


class ShellHookTask(CloudTask):
    def __init__(self, tracker, **context):
        assert tracker

        assert 'node_id' in context
        assert 'hook_name' in context

        self.task_name = 'tasks.async.shell_hook'
        self.tracker = tracker
        self.node_id = context['node_id']
        self.hook_name = context['hook_name']
        self.context = context

    def execute(self):
        self.context['options']['tracker_id'] = self.tracker.id

        logger.info("Executing task %s with tracker id %s" % (self.task_name, self.tracker.id))

        async_task = agentd_proxy.send_task(self.task_name,
                                            countdown=3,
                                            routing_key='cn16.tasks',
                                            kwargs={'hook_name': self.hook_name, 'options': self.context['options']})

        logger.info("    got Celery ID %s" % async_task.id)

        tracker_context = self.tracker.context
        tracker_context['celery_task_id'] = async_task.id
        self.tracker.context = tracker_context
        self.tracker.save()

    def wait_to_end(self):
        ctask_id = self.tracker.context['celery_task_id']

        logger.warning("Waiting for the Celery task: %s" % ctask_id)

        ctask = agentd_proxy.AsyncResult(ctask_id)

        last_line = ''
        while not ctask.ready():
            if ctask.status == 'PROGRESS':
                if 'line' in ctask.info and last_line != ctask.info['line']:
                    logger.info("stdout: %s" % ctask.info['line'])
                    last_line = ctask.info['line']
                    self.tracker.progress()

            time.sleep(1)

        return ctask.get()


class ProxMoxJBONServiceBackend(HypervisorBackend):
    """
    Cloud Service: Just bunch of ProxMox nodes.
    Every node have a pytin-agent running. When task is submitted to this backend it actually submitted
    to run remotely on the specific agent. Node to create VPS is selected by the scheduler.
    """

    # TODO: This config should be loaded from CMDB
    # Each node have CMDB representation. Also we get 'rating' and 'heartbeat' from CMDB.
    # Each node must have pytin-agent-hv installed.
    NODES = {
        332: {
            'types': ['kvm']
        },
        # 130: {
        #     'types': ['openvz']
        # }
    }

    def start_vps(self, vmid, **options):
        assert vmid > 0

        selected_cmdb_node_id = 332

        task_options = {
            'VMID': vmid,
            'SUBCOMMAND': 'start.qm',
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        task_tracker = self.send_task(ShellHookTask,
                                      node_id=selected_cmdb_node_id,
                                      hook_name='vps_cmd_proxy',
                                      options=task_options)

        return task_tracker

    def stop_vps(self, vmid, **options):
        assert vmid > 0

        selected_cmdb_node_id = 332

        task_options = {
            'VMID': vmid,
            'SUBCOMMAND': 'stop.qm',
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        task_tracker = self.send_task(ShellHookTask,
                                      node_id=selected_cmdb_node_id,
                                      hook_name='vps_cmd_proxy',
                                      options=task_options)

        return task_tracker

    def create_vps(self, **options):
        assert 'node_id' in options
        assert 'vmid' in options
        assert 'template' in options
        assert 'cpu' in options
        assert 'ram' in options
        assert 'hdd' in options
        assert 'user' in options

        selected_cmdb_node_id = options['node_id']

        task_options = {
            # Change this parameters
            'USER_NAME': options['user'] if 'user' in options else '',
            'VMID': options['vmid'],
            'VMNAME': "vm%s.%s" % (options['vmid'], options['template']),

            # HDD size in Gb
            'HDDGB': options['hdd'],

            # RAM size in Gb
            'MEMMB': options['ram'],

            # CPU cores
            'VCPU': options['cpu'],

            'IPADDR': '176.32.32.44',
            'GW': '176.32.32.1',
            'NETMASK': '255.255.254.0',

            # CentOS version
            'SUBCOMMAND': options['template']
        }

        task_tracker = self.send_task(ShellHookTask,
                                      node_id=selected_cmdb_node_id,
                                      hook_name='vps_cmd_proxy',
                                      options=task_options)

        return task_tracker
