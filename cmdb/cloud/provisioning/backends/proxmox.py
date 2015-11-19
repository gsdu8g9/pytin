# coding=utf-8
from __future__ import unicode_literals

import time

from celery import Celery

from assets.models import Server
from cloud.models import CmdbCloudConfig
from cloud.provisioning import HypervisorBackend, CloudTask
from cloud.provisioning.schedulers import RatingBasedScheduler
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

        assert 'queue' in context

        self.task_name = 'tasks.async.shell_hook'
        self.tracker = tracker
        self.queue = context['queue']
        self.context = context

    def execute(self):
        self.context['options']['tracker_id'] = self.tracker.id

        logger.info("Executing task %s with tracker id %s" % (self.task_name, self.tracker.id))

        async_task = self.REMOTE_WORKER.send_task(self.task_name,
                                                  queue=self.queue,
                                                  routing_key=self.queue,
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
    """
    Just bunch of ProxMox nodes.
    Every node have a pytin-agentd-hv running. When task is submitted to this backend it is actually submitted
    to run remotely on the specific agent. Node to create VPS is selected by the scheduler.

    Every hypervisor node in CMDB must have options: role = hypervisor and hypervisor_tech (kvm, openvz, etc).
    """

    SHELL_HOOK_TASK_CLASS = ShellHookTask

    def __init__(self, cloud):
        super(ProxMoxJBONServiceBackend, self).__init__(cloud)

        self.scheduler = RatingBasedScheduler()

    def start_vps(self, **options):
        assert 'vmid' in options
        assert 'node_id' in options and options['node_id'] > 0

        target_node = Server.active.get(pk=options['node_id'])
        hyper_tech = target_node.get_option_value('hypervisor_tech', default='unknown')

        if hyper_tech == CmdbCloudConfig.TECH_HV_KVM:
            start_subcommand = 'start.qm'
        elif hyper_tech == CmdbCloudConfig.TECH_HV_OPENVZ:
            start_subcommand = 'start.ovz'
        else:
            raise Exception("Tech %s is not supported by the backend." % hyper_tech)

        task_options = {
            'VMID': options['vmid'],
            'SUBCOMMAND': start_subcommand,
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        target_node = Server.active.get(pk=options['node_id'])

        return self.internal_shell_hook_command(target_node, **task_options)

    def stop_vps(self, **options):
        assert 'vmid' in options
        assert 'node_id' in options and options['node_id'] > 0

        target_node = Server.active.get(pk=options['node_id'])
        hyper_tech = target_node.get_option_value('hypervisor_tech', default='unknown')

        if hyper_tech == CmdbCloudConfig.TECH_HV_KVM:
            stop_subcommand = 'stop.qm'
        elif hyper_tech == CmdbCloudConfig.TECH_HV_OPENVZ:
            stop_subcommand = 'stop.ovz'
        else:
            raise Exception("Tech %s is not supported by the backend." % hyper_tech)

        task_options = {
            'VMID': options['vmid'],
            'SUBCOMMAND': stop_subcommand,
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        target_node = Server.active.get(pk=options['node_id'])

        return self.internal_shell_hook_command(target_node, **task_options)

    def create_vps(self, **options):
        assert 'vmid' in options
        assert 'template' in options
        assert 'cpu' in options
        assert 'ram' in options
        assert 'hdd' in options
        assert 'user' in options

        logger.debug(options)

        if 'node_id' in options and options['node_id'] > 0:
            target_node = Server.active.get(pk=options['node_id'])
            hyper_tech = target_node.get_option_value('hypervisor_tech', default='unknown')
        else:
            assert 'tech' in options and options['tech']

            hyper_tech = options['tech']
            target_node = self.scheduler.get_best_node(self.cloud.get_hypervisors(tech=hyper_tech))

        if 'ip' in options and options['ip']:
            ip, gateway, netmask = self.find_ip_info(options['ip'])
        else:
            ip, gateway, netmask = self.lease_ip(target_node.id)

        # Common options
        task_options = {
            # Change this parameters
            'USER_NAME': options['user'] if 'user' in options else '',
            'VMID': options['vmid'],
            'VMNAME': "vm%s.%s.%s" % (options['vmid'], options['template'], hyper_tech),

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

        if hyper_tech == CmdbCloudConfig.TECH_HV_KVM:
            # SUBCOMMAND is the specific script name used to deploy specific OS version
            task_options['SUBCOMMAND'] = options['template']
        elif hyper_tech == CmdbCloudConfig.TECH_HV_OPENVZ:
            # TEMPLATE is the OS version to deploy on OpenVZ
            task_options['SUBCOMMAND'] = 'create.ovz'
            task_options['TEMPLATE'] = options['template']
        else:
            raise Exception("Tech '%s' is not supported by the backend." % hyper_tech)

        return self.internal_shell_hook_command(target_node, **task_options)

    def internal_shell_hook_command(self, target_node, **task_options):
        """Run ShellHook remotely. All commands are proxied via vps_cmd_proxy.sh script to the specific
                scripts that are used to deploy specific VPS templates: CentOS, Debian, etc.
        :param task_options: Параметры запуска скрипта.
        :return: TaskTracker
        """
        assert target_node

        node_queue = target_node.get_option_value('agentd_taskqueue', default=None)
        if not node_queue:
            raise ValueError("Missing agentd_taskqueue in node %s" % target_node.id)

        logger.info("Send task to queue %s for node %s" % (node_queue, target_node.id))

        task_options['HV_NODE_ID'] = target_node.id

        return self.send_task(self.SHELL_HOOK_TASK_CLASS,
                              cmdb_node_id=target_node.id,
                              queue=node_queue,
                              options=task_options)
