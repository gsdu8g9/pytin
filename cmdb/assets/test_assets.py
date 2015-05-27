from django.test import TestCase

from assets.models import RegionResource, Server, ServerPort, Rack, Switch
from resources.models import Resource, ModelFieldChecker


class AssetsTest(TestCase):

    def test_change_asset_type(self):
        new_res1 = Switch.create(label="test switch")

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
        country = RegionResource.create(name='Russia')
        city = RegionResource.create(name='Moscow', parent=country)
        dc = RegionResource.create(name='Anders', parent=city)

        self.assertEqual(dc.parent.id, city.id)
        self.assertEqual(city.parent.id, country.id)
        self.assertEqual(country.parent_id, None)

        rack1 = Rack.create(name='Rackmount 1/9', parent=dc)
        rack2 = Rack.create(name='Rackmount 2/4', parent=dc)

        server1 = Server.create(label='server1', parent=rack1)
        server2 = Server.create(label='server2', parent=rack1)
        server3 = Server.create(label='server3', parent=rack2)
        server4 = Server.create(label='server4', parent=rack2)

        port1 = ServerPort.create(mac='00:15:17:e5:da:52', number=1, parent=server1)
        port2 = ServerPort.create(mac='00:15:17:e5:da:53', number=2, parent=server1)

        port3 = ServerPort.create(mac='c2:5a:e9:38:1d:09', number=1, parent=server2)

        port4 = ServerPort.create(mac='00:1a:92:19:62:d1', number=1, parent=server3)
        port5 = ServerPort.create(mac='00:1a:92:19:62:d2', number=2, parent=server3)

        port6 = ServerPort.create(mac='92:31:cc:a1:94:d8', number=1, parent=server4)

        self.assertEqual(15, Resource.objects.active().count())
        self.assertEqual(3, RegionResource.objects.active().count())
        self.assertEqual(2, Rack.objects.active().count())
        self.assertEqual(4, Server.objects.active().count())
        self.assertEqual(6, ServerPort.objects.active().count())

    def _create_test_data(self):

        for x1 in range(1, 5):
            country = RegionResource.create(name='Country %s' % x1)

            for x2 in range(1, 3):
                city = RegionResource.create(name='City %s-%s' % (country.id, x2), parent=country)

                RegionResource.create(name='City %s store' % city.id, parent=city)

                for x3 in range(1, 3):
                    dc = RegionResource.create(name='DC %s-%s' % (city.id, x3), parent=city)

                    RegionResource.create(name='DC %s store' % dc.id, parent=dc)

                    for x4 in range(1, 5):
                        rack = Rack.create(label='Rackmount %s-%s' % (dc.id, x4), serial=x4, parent=dc)

                        for x5 in range(1, 10):
                            server = Server.create(label='Server %s-%s' % (rack.id, x5), serial=x5, parent=rack)

                            for x6 in range(1, 2):
                                ServerPort.create(number=x6, mac='00:1a:92:19:62:f%s' % x6, parent=server)

