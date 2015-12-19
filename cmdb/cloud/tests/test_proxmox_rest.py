# coding=utf-8
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from assets.models import RegionResource, Datacenter, Rack, Server
from cloud.models import CmdbCloudConfig
from cloud.provisioning.backends.proxmox import VpsControlTask, ProxMoxJBONServiceBackend
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

    def get_result(self):
        return self.REMOTE_WORKER.sent_tasks[0]


class ResourcesAPITests(APITestCase):
    def setUp(self):
        super(ResourcesAPITests, self).setUp()

        user_name = 'admin'
        user, created = User.objects.get_or_create(username=user_name, password=user_name, email='admin@admin.com',
                                                   is_staff=True)
        token, created = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

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

        MockVpsControlTask.REMOTE_WORKER.sent_tasks = []

        self.cloud = CmdbCloudConfig()
        self.backend = ProxMoxJBONServiceBackend(self.cloud)
        ProxMoxJBONServiceBackend.TASK_CREATE = MockVpsControlTask
        ProxMoxJBONServiceBackend.TASK_START = MockVpsControlTask
        ProxMoxJBONServiceBackend.TASK_STOP = MockVpsControlTask

    def test_vps_start(self):
        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        payload = {
            'node': self.srv1.id,
            'vm_id': 11111,
            'user': 'unittest',
            'action': 'start'
        }

        response = self.client.patch('/v1/vps/%s/start/' % payload['vm_id'], payload)

        print response

        self.assertEqual(200, response.status_code)

        # tracker = self.backend.start_vps(
        #     node=node_id,
        #     vmid=vmid,
        #     user=user_name)
        #
        # self.assertEqual(TaskTrackerStatus.STATUS_NEW, tracker.status)
        #
        # check_data = tracker.get_result()
        #
        # check_data_opts = check_data[2]['options'] = check_data[2]['options']
        #
        # self.assertEqual(TaskTrackerStatus.STATUS_SUCCESS, tracker.status)
        #
        # # Задача, которая будет выполнена на агенте.
        # self.assertEqual('tasks.async.mock_vps_control', check_data[0])
        # self.assertEqual(None, check_data[1])
        #
        # # параметры VPS
        # self.assertEqual(11111, check_data_opts['vmid'])
        # self.assertEqual('unittest', check_data_opts['user'])
        #
