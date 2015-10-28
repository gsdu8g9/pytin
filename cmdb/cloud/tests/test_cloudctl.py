# from __future__ import unicode_literals
#
# from django.test import TestCase
# from django.utils.six import StringIO
# from django.core.management import call_command
#
# from assets.models import Server
# from cloud.models import CloudNode
#
#
# class CloudNodeTest(TestCase):
#     def test_command_output(self):
#         server, created = Server.objects.get_or_create(name='Hypervisor', role='Hypervisor')
#         node, created = CloudNode.objects.get_or_create(resource=server)
#
#         out = StringIO()
#         call_command('cloudctl', 'node', list=True, stdout=out)
#
#         print out.getvalue()
#
#         node.heartbeat()
#
#         call_command('cloudctl', 'node', list=True, stdout=out)
#         print out.getvalue()
