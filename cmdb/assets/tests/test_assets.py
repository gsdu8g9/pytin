from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.test import TestCase

from assets.models import RegionResource, Server, ServerPort, Rack, Switch, VirtualServer, VirtualServerPort, \
    SwitchPort, \
    PortConnection
from ipman.models import IPNetworkPool
from resources.models import Resource, ModelFieldChecker


class AssetsTest(TestCase):
    def test_test_connections(self):
        switch = Switch.objects.create(label="sw-test", status=Resource.STATUS_INUSE)
        switch_port1 = SwitchPort.objects.create(number=1, parent=switch)

        phyz_port1 = ServerPort.objects.create(mac='234567267845')
        vm_port1 = VirtualServerPort.objects.create(mac='244567267845')

        PortConnection.create(switch_port1, phyz_port1)
        PortConnection.create(switch_port1, vm_port1)

        self.assertEqual(2, len(switch_port1.connections))

    def test_delete_virtual_hierarchy_childs_control(self):
        vm1 = VirtualServer.objects.create(label="VM", status=Resource.STATUS_INUSE)
        vmport1 = VirtualServerPort.objects.create(number=15, mac='234567267845', parent=vm1,
                                                   status=Resource.STATUS_INUSE)
        ippool1 = IPNetworkPool.objects.create(network='192.168.1.1/24', status=Resource.STATUS_INUSE)
        address1 = ippool1.available().next()

        self.assertEqual(ippool1.id, address1.parent.id)

        address1.parent = vmport1
        address1.save()

        self.assertEqual(vmport1.id, address1.parent.id)
        self.assertEqual(ippool1.id, address1.get_option_value('ipman_pool_id'))

        # existing childs
        try:
            vm1.delete()
            self.fail("Waiting for the exception.")
        except ValidationError:
            pass

        address1.delete()
        vmport1.delete()
        vm1.delete()

        vm1.refresh_from_db()
        vmport1.refresh_from_db()
        ippool1.refresh_from_db()
        address1.refresh_from_db()

        self.assertEqual(Resource.STATUS_DELETED, vm1.status)
        self.assertEqual(Resource.STATUS_DELETED, vmport1.status)
        self.assertEqual(Resource.STATUS_DELETED, address1.status)
        self.assertNotEquals(ippool1.id, address1.parent.id)

    def test_delete_resources(self):
        switch1 = Switch.objects.create(label="test switch", status=Resource.STATUS_INUSE)
        resource1 = VirtualServer.objects.create(label="test switch", status=Resource.STATUS_INUSE)

        self.assertEqual(Resource.STATUS_INUSE, switch1.status)
        self.assertEqual(Resource.STATUS_INUSE, resource1.status)

        switch1.delete()
        resource1.delete()

        self.assertEqual(Resource.STATUS_DELETED, switch1.status)
        self.assertEqual(Resource.STATUS_DELETED, resource1.status)

    def test_change_asset_type(self):
        new_res1 = Switch.objects.create(label="test switch")

        self.assertTrue(ModelFieldChecker.is_field_or_property(new_res1, 'type'))

        setattr(new_res1, 'type', 'Server')
        new_res1.save()
        new_res1.refresh_from_db()

        self.assertEqual('Switch', new_res1.type)
        self.assertEqual(Switch, new_res1.__class__)

        # real change type
        new_res1 = new_res1.cast_type(Server)

        self.assertEqual('Server', new_res1.type)
        self.assertEqual(Server, new_res1.__class__)

    def test_option_type(self):
        country = RegionResource.objects.create(name='Russia')
        city = RegionResource.objects.create(name='Moscow', parent=country)
        dc = RegionResource.objects.create(name='Anders', parent=city)

        self.assertEqual(dc.parent.id, city.id)
        self.assertEqual(city.parent.id, country.id)
        self.assertEqual(country.parent_id, None)

        rack1 = Rack.objects.create(name='Rackmount 1/9', parent=dc)
        rack2 = Rack.objects.create(name='Rackmount 2/4', parent=dc)

        server1 = Server.objects.create(label='server1', parent=rack1)
        server2 = Server.objects.create(label='server2', parent=rack1)
        server3 = Server.objects.create(label='server3', parent=rack2)
        server4 = Server.objects.create(label='server4', parent=rack2)

        port1 = ServerPort.objects.create(mac='00:15:17:e5:da:52', number=1, parent=server1)
        port2 = ServerPort.objects.create(mac='00:15:17:e5:da:53', number=2, parent=server1)

        port3 = ServerPort.objects.create(mac='c2:5a:e9:38:1d:09', number=1, parent=server2)

        port4 = ServerPort.objects.create(mac='00:1a:92:19:62:d1', number=1, parent=server3)
        port5 = ServerPort.objects.create(mac='00:1a:92:19:62:d2', number=2, parent=server3)

        port6 = ServerPort.objects.create(mac='92:31:cc:a1:94:d8', number=1, parent=server4)

        self.assertEqual(15, Resource.objects.count())
        self.assertEqual(15, Resource.active.count())
        self.assertEqual(3, RegionResource.active.count())
        self.assertEqual(2, Rack.active.count())
        self.assertEqual(4, Server.active.count())
        self.assertEqual(6, ServerPort.active.count())

    def _create_test_data(self):

        for x1 in range(1, 5):
            country = RegionResource.objects.create(name='Country %s' % x1)

            for x2 in range(1, 3):
                city = RegionResource.objects.create(name='City %s-%s' % (country.id, x2), parent=country)

                RegionResource.objects.create(name='City %s store' % city.id, parent=city)

                for x3 in range(1, 3):
                    dc = RegionResource.objects.create(name='DC %s-%s' % (city.id, x3), parent=city)

                    RegionResource.objects.create(name='DC %s store' % dc.id, parent=dc)

                    for x4 in range(1, 5):
                        rack = Rack.objects.create(label='Rackmount %s-%s' % (dc.id, x4), serial=x4, parent=dc)

                        for x5 in range(1, 10):
                            server = Server.objects.create(label='Server %s-%s' % (rack.id, x5), serial=x5, parent=rack)

                            for x6 in range(1, 2):
                                ServerPort.objects.create(number=x6, mac='00:1a:92:19:62:f%s' % x6, parent=server)
