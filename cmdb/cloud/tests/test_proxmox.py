# coding=utf-8
from __future__ import unicode_literals

from django.test import TestCase

from assets.models import RegionResource, Datacenter, Rack, Server
from cloud.models import CmdbCloudConfig, TaskTrackerStatus
from cloud.provisioning.backends.proxmox import ProxMoxJBONServiceBackend, VpsControlTask
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


class MockVpsControlTask(VpsControlTask):
    task_name = 'tasks.async.mock_vps_control'

    REMOTE_WORKER = CeleryEmulator()

    def poll(self):
        return True, self.REMOTE_WORKER.sent_tasks[0]

    def wait(self):
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
                                                  status=Resource.STATUS_FREE,
                                                  dns1='46.17.46.200', dns2='46.17.40.200')
        self.pool11 = IPNetworkPool.objects.create(network='192.169.0.0/23', parent=self.pools_group1,
                                                   status=Resource.STATUS_INUSE,
                                                   dns1='46.17.46.200', dns2='46.17.40.200')

        self.srv1.set_option('agentd_taskqueue', 'test_task_queue')

        MockVpsControlTask.REMOTE_WORKER.sent_tasks = []

        self.cloud = CmdbCloudConfig()
        self.backend = ProxMoxJBONServiceBackend(self.cloud)
        ProxMoxJBONServiceBackend.TASK_CREATE = MockVpsControlTask
        ProxMoxJBONServiceBackend.TASK_START = MockVpsControlTask
        ProxMoxJBONServiceBackend.TASK_STOP = MockVpsControlTask

    def test_start_vps_kvm(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        tracker = self.backend.start_vps(
                node=node_id,
                vmid=vmid,
                user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('unittest', check_data_opts['user'])

    def test_stop_vps_kvm(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        tracker = self.backend.stop_vps(
                node=node_id,
                vmid=vmid,
                user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('unittest', check_data_opts['user'])

    def test_start_vps_openvz(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_OPENVZ)

        tracker = self.backend.start_vps(
                node=node_id,
                vmid=vmid,
                user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('unittest', check_data_opts['user'])

    def test_stop_vps_openvz(self):
        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_OPENVZ)

        tracker = self.backend.stop_vps(
                node=node_id,
                vmid=vmid,
                user=user_name)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('unittest', check_data_opts['user'])

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

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_OPENVZ)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        tracker = self.backend.create_vps(
                node=node_id,
                vmid=vmid,
                template=template,
                user=user_name,
                ram=ram,
                hdd=hdd,
                cpu=cpu,
                ip=ip_addr)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()

        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(self.srv1.id, tracker.context['cmdb_node_id'])
        self.assertEqual('test_task_queue', tracker.context['queue'])

        self.assertEqual(CmdbCloudConfig.TECH_HV_OPENVZ, check_data_opts['driver'])
        self.assertEqual('centos6', check_data_opts['template'])
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('v11111.openvz.unittest', check_data_opts['hostname'])
        self.assertEqual('unittest', check_data_opts['user'])
        self.assertEqual('192.168.0.25', check_data_opts['ip'])
        self.assertEqual('192.168.0.1', check_data_opts['gateway'])
        self.assertEqual('255.255.254.0', check_data_opts['netmask'])
        self.assertEqual(50, check_data_opts['hdd'])
        self.assertEqual(1024, check_data_opts['ram'])
        self.assertEqual(2, check_data_opts['cpu'])
        self.assertEqual('46.17.46.200', check_data_opts['dns1'])
        self.assertEqual('46.17.40.200', check_data_opts['dns2'])
        self.assertEqual(15, len(check_data_opts['rootpass']))

    def test_create_vps_kvm(self):
        """
        Test creating VPS KVM
        :return:
        """
        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'
        ip_addr = '192.169.0.15'

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        # ip parameter is ignored
        tracker = self.backend.create_vps(
                node=node_id,
                vmid=vmid,
                template=template,
                user=user_name,
                ram=ram,
                hdd=hdd,
                cpu=cpu,
                ip=ip_addr)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(self.srv1.id, tracker.context['cmdb_node_id'])
        self.assertEqual('test_task_queue', tracker.context['queue'])

        self.assertEqual(CmdbCloudConfig.TECH_HV_KVM, check_data_opts['driver'])
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('v11111.kvm.unittest', check_data_opts['hostname'])
        self.assertEqual('unittest', check_data_opts['user'])
        self.assertEqual('192.169.0.15', check_data_opts['ip'])
        self.assertEqual('192.169.0.1', check_data_opts['gateway'])
        self.assertEqual('255.255.254.0', check_data_opts['netmask'])
        self.assertEqual(50, check_data_opts['hdd'])
        self.assertEqual(1024, check_data_opts['ram'])
        self.assertEqual(2, check_data_opts['cpu'])
        self.assertEqual('46.17.46.200', check_data_opts['dns1'])
        self.assertEqual('46.17.40.200', check_data_opts['dns2'])
        self.assertEqual(15, len(check_data_opts['rootpass']))

    def test_create_vps_kvm_rent_ip(self):
        """
        Создание VPS без указания IP. IP будет выделен автоматически из свободного пула.
        """
        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        tracker = self.backend.create_vps(
                node=node_id,
                vmid=vmid,
                template=template,
                user=user_name,
                ram=ram,
                hdd=hdd,
                cpu=cpu,
                # ip=, we need to lease IP
        )

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(self.srv1.id, tracker.context['cmdb_node_id'])
        self.assertEqual('test_task_queue', tracker.context['queue'])

        self.assertEqual(CmdbCloudConfig.TECH_HV_KVM, check_data_opts['driver'])
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('v11111.kvm.unittest', check_data_opts['hostname'])
        self.assertEqual('unittest', check_data_opts['user'])
        self.assertEqual('192.168.0.2', check_data_opts['ip'])
        self.assertEqual('192.168.0.1', check_data_opts['gateway'])
        self.assertEqual('255.255.254.0', check_data_opts['netmask'])
        self.assertEqual(50, check_data_opts['hdd'])
        self.assertEqual(1024, check_data_opts['ram'])
        self.assertEqual(2, check_data_opts['cpu'])
        self.assertEqual('46.17.46.200', check_data_opts['dns1'])
        self.assertEqual('46.17.40.200', check_data_opts['dns2'])

    def test_create_vps_kvm_rent_ip__ip_is_empty(self):
        """
        Создание VPS с указанным пустым IP. IP будет выделен автоматически из свободного пула.
        """
        ram = 1024
        hdd = 50
        cpu = 2
        template = 'centos6'

        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        node_id = self.srv1.id
        vmid = 11111
        user_name = 'unittest'

        tracker = self.backend.create_vps(
                node=node_id,
                vmid=vmid,
                template=template,
                user=user_name,
                ram=ram,
                hdd=hdd,
                cpu=cpu,
                ip=None)

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(self.srv1.id, tracker.context['cmdb_node_id'])
        self.assertEqual('test_task_queue', tracker.context['queue'])

        self.assertEqual(CmdbCloudConfig.TECH_HV_KVM, check_data_opts['driver'])
        self.assertEqual(11111, check_data_opts['vmid'])
        self.assertEqual('v11111.kvm.unittest', check_data_opts['hostname'])
        self.assertEqual('unittest', check_data_opts['user'])
        self.assertEqual('192.168.0.2', check_data_opts['ip'])
        self.assertEqual('192.168.0.1', check_data_opts['gateway'])
        self.assertEqual('255.255.254.0', check_data_opts['netmask'])
        self.assertEqual(50, check_data_opts['hdd'])
        self.assertEqual(1024, check_data_opts['ram'])
        self.assertEqual(2, check_data_opts['cpu'])
        self.assertEqual('46.17.46.200', check_data_opts['dns1'])
        self.assertEqual('46.17.40.200', check_data_opts['dns2'])

    def test_create_vps_kvm_schedule_node_rent_ip(self):
        """
        Создание VPS без указания ноды (автовыбор) и без указания IP (выделить)
        """
        s1 = Server.objects.create(name='CN1', rating=10, role='hypervisor', parent=self.rack1, agentd_taskqueue='s1',
                                   hypervisor_driver=CmdbCloudConfig.TECH_HV_KVM, status=Resource.STATUS_INUSE)

        s2 = Server.objects.create(name='CN2', role='hypervisor', parent=self.rack1, agentd_taskqueue='s2',
                                   hypervisor_driver=CmdbCloudConfig.TECH_HV_KVM,
                                   status=Resource.STATUS_LOCKED)

        s3 = Server.objects.create(name='CN3', role='hypervisor', parent=self.rack1, agentd_taskqueue='s3',
                                   hypervisor_driver=CmdbCloudConfig.TECH_HV_KVM,
                                   status=Resource.STATUS_INUSE)

        s4 = Server.objects.create(name='CN4', rating=15, role='hypervisor', parent=self.rack1, agentd_taskqueue='s4',
                                   hypervisor_driver=CmdbCloudConfig.TECH_HV_KVM, status=Resource.STATUS_INUSE)

        s5 = Server.objects.create(name='Some server', status=Resource.STATUS_INUSE, parent=self.rack1)

        s6 = Server.objects.create(name='CN6', role='hypervisor', parent=self.rack1, agentd_taskqueue='s6',
                                   hypervisor_driver=CmdbCloudConfig.TECH_HV_OPENVZ,
                                   status=Resource.STATUS_INUSE)

        ram = 1024
        hdd = 50
        cpu = 2
        template = 'kvm.centos6'

        hv_tech = CmdbCloudConfig.TECH_HV_KVM

        vmid = 11111
        user_name = 'unittest'

        tracker = self.backend.create_vps(
                vmid=vmid,
                template=template,
                user=user_name,
                ram=ram,
                hdd=hdd,
                cpu=cpu,
                driver=hv_tech)

        self.assertEqual(s4.id, tracker.context['cmdb_node_id'])
        self.assertEqual('s4', tracker.context['queue'])

        self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)

        check_data = tracker.wait()
        check_data_opts = check_data[2]['options'] = check_data[2]['options']

        self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)

        # Задача, которая будет выполнена на агенте.
        self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        self.assertEqual(None, check_data[1])

        # параметры VPS
        self.assertEqual(11111, check_data_opts['vmid'])

        # selected best node for the VPS
        self.assertEqual(s4.id, tracker.context['cmdb_node_id'])

        self.assertEqual(CmdbCloudConfig.TECH_HV_KVM, check_data_opts['driver'])
        self.assertEqual('v11111.kvm.unittest', check_data_opts['hostname'])
        self.assertEqual('unittest', check_data_opts['user'])
        self.assertEqual('192.168.0.2', check_data_opts['ip'])
        self.assertEqual('192.168.0.1', check_data_opts['gateway'])
        self.assertEqual('255.255.254.0', check_data_opts['netmask'])
        self.assertEqual(50, check_data_opts['hdd'])
        self.assertEqual(1024, check_data_opts['ram'])
        self.assertEqual(2, check_data_opts['cpu'])
        self.assertEqual('46.17.46.200', check_data_opts['dns1'])
        self.assertEqual('46.17.40.200', check_data_opts['dns2'])
