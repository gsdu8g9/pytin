from django.test import TestCase

from assets.models import RegionResource, ServerResource, PortResource, RackResource
from resources.models import Resource


class AssetsTest(TestCase):

    def test_option_type(self):
        country = RegionResource.create(name='Russia')
        city = RegionResource.create(name='Moscow', parent=country)
        dc = RegionResource.create(name='Anders', parent=city)

        self.assertEqual(dc.parent.id, city.id)
        self.assertEqual(city.parent.id, country.id)
        self.assertEqual(country.parent_id, 0)

        rack1 = RackResource.create(name='Rackmount 1/9', parent=dc)
        rack2 = RackResource.create(name='Rackmount 2/4', parent=dc)

        server1 = ServerResource.create(label='server1', parent=rack1)
        server2 = ServerResource.create(label='server2', parent=rack1)
        server3 = ServerResource.create(label='server3', parent=rack2)
        server4 = ServerResource.create(label='server4', parent=rack2)

        port1 = PortResource.create(mac='00:15:17:e5:da:52', number=1, parent=server1)
        port2 = PortResource.create(mac='00:15:17:e5:da:53', number=2, parent=server1)

        port3 = PortResource.create(mac='c2:5a:e9:38:1d:09', number=1, parent=server2)

        port4 = PortResource.create(mac='00:1a:92:19:62:d1', number=1, parent=server3)
        port5 = PortResource.create(mac='00:1a:92:19:62:d2', number=2, parent=server3)

        port6 = PortResource.create(mac='92:31:cc:a1:94:d8', number=1, parent=server4)

        self.assertEqual(15, Resource.objects.active().count())
        self.assertEqual(3, RegionResource.objects.active().count())
        self.assertEqual(2, RackResource.objects.active().count())
        self.assertEqual(4, ServerResource.objects.active().count())
        self.assertEqual(6, PortResource.objects.active().count())

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
                        rack = RackResource.create(label='Rackmount %s-%s' % (dc.id, x4), serial=x4, parent=dc)

                        for x5 in range(1, 10):
                            server = ServerResource.create(label='Server %s-%s' % (rack.id, x5), serial=x5, parent=rack)

                            for x6 in range(1, 2):
                                PortResource.create(number=x6, mac='00:1a:92:19:62:f%s' % x6, parent=server)

