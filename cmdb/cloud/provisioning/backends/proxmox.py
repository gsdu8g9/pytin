# coding=utf-8
from __future__ import unicode_literals

import time

from celery import Celery

from assets.models import Server
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
    # Remote interface used to execute tasks
    REMOTE_WORKER = agentd_proxy

    # Script used as the entry point for all shell commands. See pytin-agentd-hv project.
    HOOK_SCRIPT_NAME = 'vps_cmd_proxy'

    def __init__(self, tracker, **context):
        assert tracker

        assert 'routing_key' in context

        self.task_name = 'tasks.async.shell_hook'
        self.tracker = tracker
        self.routing_key = context['routing_key']
        self.context = context

    def execute(self):
        self.context['options']['tracker_id'] = self.tracker.id

        logger.info("Executing task %s with tracker id %s" % (self.task_name, self.tracker.id))

        async_task = self.REMOTE_WORKER.send_task(self.task_name,
                                                  queue=self.routing_key,
                                                  routing_key=self.routing_key,
                                                  kwargs={'hook_name': self.HOOK_SCRIPT_NAME,
                                                          'options': self.context['options']})

        logger.info("    got Celery ID %s" % async_task.id)

        tracker_context = self.tracker.context
        tracker_context['celery_task_id'] = async_task.id
        self.tracker.context = tracker_context
        self.tracker.save()

    def get_result(self):
        ctask_id = self.tracker.context['celery_task_id']

        logger.warning("Waiting for the Celery task: %s" % ctask_id)

        ctask = self.REMOTE_WORKER.AsyncResult(ctask_id)

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
    SHELL_HOOK_TASK_CLASS = ShellHookTask

    TECH_HV_KVM = 'kvm'
    TECH_HV_OPENVZ = 'openvz'

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
        #     'types': [self.TECH_HV_OPENVZ]
        # }
    }

    def start_vps(self, **options):
        assert 'vmid' in options
        assert 'node_id' in options
        assert 'tech' in options

        hyper_tech = options['tech']

        if hyper_tech == self.TECH_HV_KVM:
            start_subcommand = 'start.qm'
        elif hyper_tech == self.TECH_HV_OPENVZ:
            start_subcommand = 'start.ovz'
        else:
            raise Exception("Tech %s is not supported by the backend.")

        task_options = {
            'VMID': options['vmid'],
            'SUBCOMMAND': start_subcommand,
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        return self.internal_shell_hook_command(options['node_id'], **task_options)

    def stop_vps(self, **options):
        assert 'vmid' in options
        assert 'node_id' in options
        assert 'tech' in options

        hyper_tech = options['tech']

        if hyper_tech == self.TECH_HV_KVM:
            stop_subcommand = 'stop.qm'
        elif hyper_tech == self.TECH_HV_OPENVZ:
            stop_subcommand = 'stop.ovz'
        else:
            raise Exception("Tech %s is not supported by the backend.")

        task_options = {
            'VMID': options['vmid'],
            'SUBCOMMAND': stop_subcommand,
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        return self.internal_shell_hook_command(options['node_id'], **task_options)

    def create_vps(self, **options):
        assert 'tech' in options
        assert 'node_id' in options
        assert 'vmid' in options
        assert 'template' in options
        assert 'cpu' in options
        assert 'ram' in options
        assert 'hdd' in options
        assert 'user' in options

        logger.debug(options)

        hv_node_id = options['node_id']
        hyper_tech = options['tech']

        if 'ip' in options and options['ip']:
            ip, gateway, netmask = self.find_ip_info(options['ip'])
        else:
            ip, gateway, netmask = self.lease_ip(hv_node_id)

        # Common options
        task_options = {
            # Change this parameters
            'USER_NAME': options['user'] if 'user' in options else '',
            'VMID': options['vmid'],
            'VMNAME': "vm%s.%s.%s" % (options['vmid'], options['template'], options['tech']),

            # HDD size in Gb
            'HDDGB': options['hdd'],

            # RAM size in Gb
            'MEMMB': options['ram'],

            # CPU cores
            'VCPU': options['cpu'],

            'DNS1': '46.17.46.200',
            'DNS2': '46.17.40.200',

            'IPADDR': ip,
            'GW': gateway,
            'NETMASK': netmask,
        }

        if hyper_tech == self.TECH_HV_KVM:
            # SUBCOMMAND is the specific script name used to deploy specific OS version
            task_options['SUBCOMMAND'] = options['template']
        elif hyper_tech == self.TECH_HV_OPENVZ:
            # TEMPLATE is the OS version to deploy on OpenVZ
            task_options['SUBCOMMAND'] = 'create.ovz'
            task_options['TEMPLATE'] = options['template']
        else:
            raise Exception("Tech %s is not supported by the backend.")

        return self.internal_shell_hook_command(hv_node_id, **task_options)

    def internal_shell_hook_command(self, target_node_id, **task_options):
        """Run ShellHook remotely. All commands are proxied via vps_cmd_proxy.sh script to the specific
                scripts that are used to deploy specific VPS templates: CentOS, Debian, etc.
        :param task_options: Параметры запуска скрипта.
        :return: TaskTracker
        """
        assert target_node_id > 0

        target_node = Server.active.get(pk=target_node_id)
        routing_key = target_node.get_option_value('agentd_taskqueue', default=None)
        if not routing_key:
            raise ValueError("Missing agentd_taskqueue in node %s" % target_node_id)

        logger.info("Send task to queue %s for node %s" % (routing_key, target_node_id))

        return self.send_task(self.SHELL_HOOK_TASK_CLASS,
                              routing_key=routing_key,
                              options=task_options)
