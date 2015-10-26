from __future__ import unicode_literals
import time

from django.test import TestCase

from assets.models import Server
from cloud.models import CloudNode, CloudService
import cloud.models


class CloudNodeTest(TestCase):
    def test_add_node_no_role(self):
        server, created = Server.objects.get_or_create(name='Server')

        try:
            node, created = CloudNode.objects.get_or_create(resource=server)
            self.fail('Waiting for the AssertionError.')
        except:
            pass

    def test_add_node(self):
        server, created = Server.objects.get_or_create(name='Server')
        node, created = CloudNode.objects.get_or_create(resource=server)

        self.assertTrue(created)
        self.assertEqual(node.resource.name, 'Server')
        self.assertEqual(node.fail_count, 0)
        self.assertEqual(node.heartbeat_last, None)

        cloud.models.HEARTBEAT_PERIOD_SEC = 4

        node.heartbeat()
        time.sleep(5)
        node.heartbeat()

        self.assertEqual(1, len(list(CloudNode.objects.filter(fail_count=1))))

        node.refresh_from_db()
        self.assertEqual(node.fail_count, 1)

        # add node to service
        service, created = CloudService.objects.get_or_create(name='VPS', implementor='app.cloud.VPS')
        added_node = service.add_node(node)

        self.assertEqual(1, len(service.nodes))
