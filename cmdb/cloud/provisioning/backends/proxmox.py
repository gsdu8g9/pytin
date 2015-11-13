# coding=utf-8
from __future__ import unicode_literals

import time

from celery import Celery

from cloud.provisioning import HypervisorBackend, CloudTask
from cmdb.settings import logger, PROXMOX_BACKEND
from ipman.models import IPAddress, IPNetworkPool
from resources.models import Resource

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

    def start_vps(self, **options):
        assert 'tech' in options

        hyper_tech = options['tech']

        if hyper_tech == 'kvm':
            return self.start_vps_kvm(**options)
        elif hyper_tech == 'openvz':
            return self.start_vps_openvz(**options)
        else:
            raise Exception("Tech %s is not supported by the backend.")

    def start_vps_openvz(self, vmid, **options):
        assert vmid > 0

        selected_cmdb_node_id = options['node_id']

        task_options = {
            'VMID': vmid,
            'SUBCOMMAND': 'start.ovz',
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        task_tracker = self.send_task(ShellHookTask,
                                      node_id=selected_cmdb_node_id,
                                      hook_name='vps_cmd_proxy',
                                      options=task_options)

        return task_tracker

    def start_vps_kvm(self, vmid, **options):
        assert vmid > 0

        selected_cmdb_node_id = options['node_id']

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

    def stop_vps(self, **options):
        assert 'tech' in options

        hyper_tech = options['tech']

        if hyper_tech == 'kvm':
            return self.stop_vps_kvm(**options)
        elif hyper_tech == 'openvz':
            return self.stop_vps_openvz(**options)
        else:
            raise Exception("Tech %s is not supported by the backend.")

    def stop_vps_openvz(self, vmid, **options):
        assert vmid > 0

        selected_cmdb_node_id = options['node_id']

        task_options = {
            'VMID': vmid,
            'SUBCOMMAND': 'stop.ovz',
            'USER_NAME': options['user'] if 'user' in options else ''
        }

        task_tracker = self.send_task(ShellHookTask,
                                      node_id=selected_cmdb_node_id,
                                      hook_name='vps_cmd_proxy',
                                      options=task_options)

        return task_tracker

    def stop_vps_kvm(self, vmid, **options):
        assert vmid > 0

        selected_cmdb_node_id = options['node_id']

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
        assert 'tech' in options

        hyper_tech = options['tech']

        if hyper_tech == 'kvm':
            return self.create_vps_kvm(**options)
        elif hyper_tech == 'openvz':
            return self.create_vps_openvz(**options)
        else:
            raise Exception("Tech %s is not supported by the backend.")

    def create_vps_openvz(self, **options):
        assert 'node_id' in options
        assert 'vmid' in options
        assert 'template' in options
        assert 'cpu' in options
        assert 'ram' in options
        assert 'hdd' in options
        assert 'user' in options
        assert 'ip' in options

        selected_cmdb_node_id = options['node_id']

        ip, gateway, netmask = self._find_ip_info(options['ip'])

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

            'IP_ADDRS': [ip],
            'GW': gateway,
            'NETMASK': netmask,

            # CentOS version
            'SUBCOMMAND': 'create.ovz',
            'TEMPLATE': options['template']
        }

        task_tracker = self.send_task(ShellHookTask,
                                      node_id=selected_cmdb_node_id,
                                      hook_name='vps_cmd_proxy',
                                      options=task_options)

        return task_tracker

    def create_vps_kvm(self, **options):
        assert 'node_id' in options
        assert 'vmid' in options
        assert 'template' in options
        assert 'cpu' in options
        assert 'ram' in options
        assert 'hdd' in options
        assert 'user' in options
        assert 'ip' in options

        selected_cmdb_node_id = options['node_id']

        ip, gateway, netmask = self._find_ip_info(options['ip'])

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

            'IPADDR': ip,
            'GW': gateway,
            'NETMASK': netmask,

            # CentOS version
            'SUBCOMMAND': options['template']
        }

        task_tracker = self.send_task(ShellHookTask,
                                      node_id=selected_cmdb_node_id,
                                      hook_name='vps_cmd_proxy',
                                      options=task_options)

        return task_tracker

    def _find_ip_info(self, ip_address):
        """
        Search and return info about IP address: gateway and netmask.
        Check only in IPNetworkPools that is free.
        :param ip_address:
        :return: tuple (ip, gw, netmask)
        """
        assert ip_address

        target_net_pool = None
        found_ips = IPAddress.active.filter(address=ip_address)
        if len(found_ips) > 0:
            found_ip = found_ips[0]
            target_net_pool = found_ip.get_origin()
        else:
            for ip_net_pool in IPNetworkPool.active.find(status=Resource.STATUS_FREE):
                if ip_net_pool.can_add(ip_address):
                    target_net_pool = ip_net_pool
                    break

        if not target_net_pool:
            raise Exception("IP %s have no origin" % ip_address)

        # checking IP pool
        netmask = target_net_pool.get_option_value('netmask', default=None)
        gateway = target_net_pool.get_option_value('gateway', default=None)

        if not netmask or not gateway:
            raise Exception("IP pool %s have no network settings." % target_net_pool)

        return ip_address, gateway, netmask
