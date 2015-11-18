# coding=utf-8
from __future__ import unicode_literals

from django.test import TestCase

from assets.models import Server
from cloud.models import CmdbCloudConfig
from cloud.provisioning.schedulers import RoundRobinScheduler
from resources.models import Resource


class ProxMoxSchedulersTest(TestCase):
    def setUp(self):
        Resource.objects.all().delete()

        self.cloud = CmdbCloudConfig()

    def test_roundrobin(self):
        s1 = Server.objects.create(name='CN1', role='hypervisor', status=Resource.STATUS_INUSE)
        s2 = Server.objects.create(name='CN2', role='hypervisor', status=Resource.STATUS_LOCKED)
        s3 = Server.objects.create(name='CN3', role='hypervisor', status=Resource.STATUS_INUSE)
        s4 = Server.objects.create(name='CN4', role='hypervisor', status=Resource.STATUS_INUSE)
        s5 = Server.objects.create(name='Some server', status=Resource.STATUS_INUSE)

        hvisors = self.cloud.get_hypervisors()
        self.assertEqual(3, len(hvisors))

        scheduler = RoundRobinScheduler(hvisors)
        scheduler.reset()

        node = scheduler.get_node()
        self.assertEqual(s1.id, node.id)

        node = scheduler.get_node()
        self.assertEqual(s3.id, node.id)

        node = scheduler.get_node()
        self.assertEqual(s4.id, node.id)

        node = scheduler.get_node()
        self.assertEqual(s1.id, node.id)
