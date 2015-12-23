# coding=utf-8
from __future__ import unicode_literals

import json

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

    def poll(self):
        return True, self.REMOTE_WORKER.sent_tasks[0]

    def wait(self):
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

    def test_vps_create(self):
        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)
        self.srv1.use()

        ram = 1024
        hdd = 50
        cpu = 2
        template = 'kvm.centos6'

        payload = {
            'vmid': 11111,
            'ram': ram,
            'hdd': hdd,
            'cpu': cpu,
            'user': 'unittest',
            'template': template,
        }

        response = self.client.post('/v1/vps/', payload)
        self.assertEqual(200, response.status_code)

        # cloud_tasks
        task_info = self.client.get('/v1/cloud_tasks/%s/' % response.data['id'])
        self.assertEqual(200, response.status_code)
        self.assertEqual('success', task_info.data['status'])

        context = json.loads(task_info.data['context_json'])
        self.assertEqual(self.srv1.id, context['cmdb_node_id'])
        self.assertEqual('192.168.0.2', context['options']['ip'])
        self.assertEqual('192.168.0.1', context['options']['gateway'])

    def test_vps_start(self):
        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        payload = {
            'node': self.srv1.id,
            'vmid': 11111,
            'user': 'unittest'
        }

        response = self.client.patch('/v1/vps/%s/start/' % payload['vmid'], payload)
        self.assertEqual(200, response.status_code)

        # cloud_tasks
        task_info = self.client.get('/v1/cloud_tasks/%s/' % response.data['id'])
        self.assertEqual(200, response.status_code)
        self.assertEqual('success', task_info.data['status'])

    def test_vps_stop(self):
        self.srv1.set_option('hypervisor_driver', CmdbCloudConfig.TECH_HV_KVM)

        payload = {
            'node': self.srv1.id,
            'vmid': 11111,
            'user': 'unittest'
        }

        response = self.client.patch('/v1/vps/%s/stop/' % payload['vmid'], payload)
        self.assertEqual(200, response.status_code)

        # cloud_tasks
        task_info = self.client.get('/v1/cloud_tasks/%s/' % response.data['id'])
        self.assertEqual(200, response.status_code)
        self.assertEqual('success', task_info.data['status'])
