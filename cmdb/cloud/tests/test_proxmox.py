# coding=utf-8
from __future__ import unicode_literals

from django.test import TestCase

from assets.models import RegionResource, Datacenter, Rack, Server
from cloud.models import CmdbCloudConfig, TaskTrackerStatus
from cloud.provisioning.backends.proxmox import ShellHookTask, ProxMoxJBONServiceBackend
from ipman.models import IPNetworkPool
from resources.models import Resource


class CeleryEmulator(object):
    sent_tasks = None

    class MockAsyncTask(object):
        id = 5

    def __init__(self):
        self.sent_tasks = []

    def send_task(self, name, args=None, kwargs=None, countdown=None,
                  eta=None, task_id=None, producer=None, connection=None,
                  router=None, result_cls=None, expires=None,
                  publisher=None, link=None, link_error=None,
                  add_to_parent=True, reply_to=None, **options):
        self.sent_tasks.append((name, args, kwargs))

        return self.MockAsyncTask()


class MockShellHookTask(ShellHookTask):
    REMOTE_WORKER = CeleryEmulator()

    def get_result(self):
        return self.REMOTE_WORKER.sent_tasks[0]


class ProxMoxJBONServiceBackendTest(TestCase):
    def setUp(self):
        Resource.objects.all().delete()

        self.moscow = RegionResource.objects.create(name='Moscow')
        self.dc1 = Datacenter.objects.create(name='Test DC 1', parent=self.moscow)
        self.rack1 = Rack.objects.create(name='Test Rack 1', parent=self.dc1)
        self.srv1 = Server.objects.create(name='Test hypervisor 1', role='hypervisor', parent=self.rack1)
        self.pools_group1 = RegionResource.objects.create(name='Test DC 1 IP Pools', parent=self.dc1)
        self.pool1 = IPNetworkPool.objects.create(network='192.168.0.0/23', parent=self.pools_group1,
                                                  status=Resource.STATUS_FREE)
        self.pool11 = IPNetworkPool.objects.create(network='192.169.0.0/23', parent=self.pools_group1,
                                                   status=Resource.STATUS_INUSE)

        self.srv1.set_option('agentd_taskqueue', 'test_task_queue')

        MockShellHookTask.REMOTE_WORKER.sent_tasks = []

        self.cloud = CmdbCloudConfig()
        self.backend = ProxMoxJBONServiceBackend(self.cloud)
        self.backend.SHELL_HOOK_TASK_CLASS = MockShellHookTask

    def test_start_vps_kvm(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_KVM)

        tracker = self.backend.start_vps(
            node_id=node_id,
            vmid=vmid,
            user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('start.qm', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])

    def test_stop_vps_kvm(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_KVM)

        tracker = self.backend.stop_vps(
            node_id=node_id,
            vmid=vmid,
            user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('stop.qm', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])

    def test_start_vps_openvz(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_OPENVZ)

        tracker = self.backend.start_vps(
            node_id=node_id,
            vmid=vmid,
            user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('start.ovz', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])

    def test_stop_vps_openvz(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_OPENVZ)

        tracker = self.backend.stop_vps(
            node_id=node_id,
            vmid=vmid,
            user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('stop.ovz', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])

    def test_create_vps_openvz(self):
        """
        Test creating VPS KVM
        :return:
        """
        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'
        ip_addr = '192.168.0.25'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_OPENVZ)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        tracker = self.backend.create_vps(
            node_id=node_id,
            vmid=vmid,
            template=template,
            user=user_name,
            ram=ram,
            hdd=hdd,
            cpu=cpu,
            ip=ip_addr)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('create.ovz', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual('centos6', check_data_opts['TEMPLATE'])
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('vm11111.centos6.openvz', check_data_opts['VMNAME'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])
        self.assertEqual('192.168.0.25', check_data_opts['IPADDR'])
        self.assertEqual('192.168.0.1', check_data_opts['GW'])
        self.assertEqual('255.255.254.0', check_data_opts['NETMASK'])
        self.assertEqual(50, check_data_opts['HDDGB'])
        self.assertEqual(1024, check_data_opts['MEMMB'])
        self.assertEqual(2, check_data_opts['VCPU'])
        self.assertEqual('46.17.46.200', check_data_opts['DNS1'])
        self.assertEqual('46.17.40.200', check_data_opts['DNS2'])

    def test_create_vps_kvm(self):
        """
        Test creating VPS KVM
        :return:
        """
        cloud = CmdbCloudConfig()
        backend = ProxMoxJBONServiceBackend(cloud)
        backend.SHELL_HOOK_TASK_CLASS = MockShellHookTask

        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'
        ip_addr = '192.169.0.15'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_KVM)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        tracker = backend.create_vps(
            node_id=node_id,
            vmid=vmid,
            template=template,
            user=user_name,
            ram=ram,
            hdd=hdd,
            cpu=cpu,
            ip=ip_addr)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('centos6', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('vm11111.centos6.kvm', check_data_opts['VMNAME'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])
        self.assertEqual('192.169.0.15', check_data_opts['IPADDR'])
        self.assertEqual('192.169.0.1', check_data_opts['GW'])
        self.assertEqual('255.255.254.0', check_data_opts['NETMASK'])
        self.assertEqual(50, check_data_opts['HDDGB'])
        self.assertEqual(1024, check_data_opts['MEMMB'])
        self.assertEqual(2, check_data_opts['VCPU'])
        self.assertEqual('46.17.46.200', check_data_opts['DNS1'])
        self.assertEqual('46.17.40.200', check_data_opts['DNS2'])

    def test_create_vps_kvm_rent_ip(self):
        """
        Создание VPS без указания IP. IP будет выделен автоматически из свободного пула.
        """
        cloud = CmdbCloudConfig()
        backend = ProxMoxJBONServiceBackend(cloud)
        backend.SHELL_HOOK_TASK_CLASS = MockShellHookTask

        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_KVM)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        tracker = backend.create_vps(
            node_id=node_id,
            vmid=vmid,
            template=template,
            user=user_name,
            ram=ram,
            hdd=hdd,
            cpu=cpu,
            # ip=, IP must be leased
        )

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('centos6', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('vm11111.centos6.kvm', check_data_opts['VMNAME'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])
        self.assertEqual('192.168.0.2', check_data_opts['IPADDR'])
        self.assertEqual('192.168.0.1', check_data_opts['GW'])
        self.assertEqual('255.255.254.0', check_data_opts['NETMASK'])
        self.assertEqual(50, check_data_opts['HDDGB'])
        self.assertEqual(1024, check_data_opts['MEMMB'])
        self.assertEqual(2, check_data_opts['VCPU'])
        self.assertEqual('46.17.46.200', check_data_opts['DNS1'])
        self.assertEqual('46.17.40.200', check_data_opts['DNS2'])

    def test_create_vps_kvm_rent_ip__ip_is_empty(self):
        """
        Создание VPS с указанным пустым IP. IP будет выделен автоматически из свободного пула.
        """
        cloud = CmdbCloudConfig()
        backend = ProxMoxJBONServiceBackend(cloud)
        backend.SHELL_HOOK_TASK_CLASS = MockShellHookTask

        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'

        self.srv1.set_option('hypervisor_tech', CmdbCloudConfig.TECH_HV_KVM)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        tracker = backend.create_vps(
            node_id=node_id,
            vmid=vmid,
            template=template,
            user=user_name,
            ram=ram,
            hdd=hdd,
            cpu=cpu,
            ip=None)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('centos6', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])
        self.assertEqual('vm11111.centos6.kvm', check_data_opts['VMNAME'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])
        self.assertEqual('192.168.0.2', check_data_opts['IPADDR'])
        self.assertEqual('192.168.0.1', check_data_opts['GW'])
        self.assertEqual('255.255.254.0', check_data_opts['NETMASK'])
        self.assertEqual(50, check_data_opts['HDDGB'])
        self.assertEqual(1024, check_data_opts['MEMMB'])
        self.assertEqual(2, check_data_opts['VCPU'])
        self.assertEqual('46.17.46.200', check_data_opts['DNS1'])
        self.assertEqual('46.17.40.200', check_data_opts['DNS2'])

    def test_create_vps_kvm_schedule_node_rent_ip(self):
        """
        Создание VPS без указания ноды (автовыбор) и без указания IP (выделить)
        """
        cloud = CmdbCloudConfig()
        backend = ProxMoxJBONServiceBackend(cloud)
        backend.SHELL_HOOK_TASK_CLASS = MockShellHookTask

        # Server.objects.all().delete()

        s1 = Server.objects.create(name='CN1', rating=10, role='hypervisor', parent=self.rack1, agentd_taskqueue='s1',
                                   hypervisor_tech=CmdbCloudConfig.TECH_HV_KVM, status=Resource.STATUS_INUSE)

        s2 = Server.objects.create(name='CN2', role='hypervisor', parent=self.rack1, agentd_taskqueue='s2',
                                   hypervisor_tech=CmdbCloudConfig.TECH_HV_KVM,
                                   status=Resource.STATUS_LOCKED)

        s3 = Server.objects.create(name='CN3', role='hypervisor', parent=self.rack1, agentd_taskqueue='s3',
                                   hypervisor_tech=CmdbCloudConfig.TECH_HV_KVM,
                                   status=Resource.STATUS_INUSE)

        s4 = Server.objects.create(name='CN4', rating=15, role='hypervisor', parent=self.rack1, agentd_taskqueue='s4',
                                   hypervisor_tech=CmdbCloudConfig.TECH_HV_KVM, status=Resource.STATUS_INUSE)

        s5 = Server.objects.create(name='Some server', status=Resource.STATUS_INUSE, parent=self.rack1)

        s6 = Server.objects.create(name='CN6', role='hypervisor', parent=self.rack1, agentd_taskqueue='s6',
                                   hypervisor_tech=CmdbCloudConfig.TECH_HV_OPENVZ,
                                   status=Resource.STATUS_INUSE)

        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'

        hv_tech = CmdbCloudConfig.TECH_HV_KVM

        vmid = 11111
        user_name = 'unittest'

        tracker = backend.create_vps(
            vmid=vmid,
            template=template,
            user=user_name,
            ram=ram,
            hdd=hdd,
            cpu=cpu,
            tech=hv_tech)

        self.assertEqual(s4.id, tracker.context['cmdb_node_id'])
        self.assertEqual('s4', tracker.context['queue'])

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.get_result()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.shell_hook', check_data[0])
        self.assertEqual(None, check_data[1])

        # Скрипт, для передачи управления специальным скриптам, которые создают VPS (SUBCOMMAND).
        self.assertEqual('vps_cmd_proxy', check_data[2]['hook_name'])

        # SUBCOMMAND - название спец скрипта, поднимает CentOS, Debian и тд.
        self.assertEqual('centos6', check_data_opts['SUBCOMMAND'])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['VMID'])

        # selected best node for the VPS
        self.assertEqual(s4.id, check_data_opts['HV_NODE_ID'])
        self.assertEqual('vm11111.centos6.kvm', check_data_opts['VMNAME'])
        self.assertEqual('unittest', check_data_opts['USER_NAME'])
        self.assertEqual('192.168.0.2', check_data_opts['IPADDR'])
        self.assertEqual('192.168.0.1', check_data_opts['GW'])
        self.assertEqual('255.255.254.0', check_data_opts['NETMASK'])
        self.assertEqual(50, check_data_opts['HDDGB'])
        self.assertEqual(1024, check_data_opts['MEMMB'])
        self.assertEqual(2, check_data_opts['VCPU'])
        self.assertEqual('46.17.46.200', check_data_opts['DNS1'])
        self.assertEqual('46.17.40.200', check_data_opts['DNS2'])