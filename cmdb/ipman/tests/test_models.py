from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from assets.models import RegionResource, Datacenter, Rack, Server
from ipman.models import GlobalIPManager, IPAddressPoolFactory, IPAddressGeneric
from resources.models import Resource


class IPModelsTest(TestCase):
    def test_add_ip_duplicate(self):
        pool1 = IPAddressPoolFactory.from_name('Test pool 1')
        pool2 = IPAddressPoolFactory.from_name('Test pool 1')

        ip1 = pool1.add_ip("46.17.40.111")
        ip2 = pool2.add_ip("46.17.40.111")

        ip1.refresh_from_db()
        ip2.refresh_from_db()

        self.assertEqual(ip1.id, ip2.id)
        self.assertEqual(ip1.address, ip2.address)
        self.assertEqual(ip1.pool.id, pool2.id)

    def test_add_ip_to_the_pool(self):
        pool1 = IPAddressPoolFactory.from_name('Test pool')

        pool1.add_ip("46.17.40.111")
        pool1.add_ip(IPAddressGeneric.objects.create(address="46.17.40.112", pool=pool1))

        self.assertEqual(2, pool1.get_ips().count())

    def test_delete_ip(self):
        """
        IP is completely removed from DB on delete()
        """
        srv1 = Server.objects.create(name='Test server 1')
        pool1 = IPAddressPoolFactory.from_network('192.168.0.0/24')

        self.assertEqual(254, pool1.get_ips().count())

        ip = pool1.get_ips()[10]
        ip.delete()

        self.assertEqual(253, pool1.get_ips().count())

    def test_free_ip(self):
        """
        IP.parent set to None on free()
        """
        srv1 = Server.objects.create(name='Test server 1')
        pool1 = IPAddressPoolFactory.from_network('192.168.0.0/24')

        ip = pool1.get_ips()[10]
        self.assertEqual(None, ip.parent)
        self.assertEqual(Resource.STATUS_FREE, ip.status)
        self.assertEqual(pool1.id, ip.pool.id)

        ip.use(srv1)
        ip.refresh_from_db()

        self.assertEqual(srv1.id, ip.parent.id)
        self.assertEqual(Resource.STATUS_INUSE, ip.status)
        self.assertEqual(pool1.id, ip.pool.id)

        ip.free()

        self.assertEqual(srv1.id, ip.parent.id)  # keep .parent field
        self.assertEqual(Resource.STATUS_FREE, ip.status)
        self.assertEqual(pool1.id, ip.pool.id)

    def test_datacenter_pool_manager(self):
        russia = RegionResource.objects.create(name='Russia')

        moscow = RegionResource.objects.create(name='Moscow', parent=russia)
        dc1 = Datacenter.objects.create(name='Test DC 1', parent=moscow)
        dc2 = Datacenter.objects.create(name='Test DC 2', parent=moscow)
        rack1 = Rack.objects.create(name='Test Rack 1', parent=dc1)
        srv1 = Server.objects.create(name='Test server 1', parent=rack1)

        pool1 = IPAddressPoolFactory.from_network('192.168.0.0/23')
        dc1 += pool1

        pool2 = IPAddressPoolFactory.from_network('192.169.0.0/23')
        pool2.use()
        dc2 += pool2

        # testing manager

        pools1 = GlobalIPManager.find_pools()
        self.assertEqual(2, len(pools1))

        pools2 = GlobalIPManager.find_pools(datacenter=dc1)
        self.assertEqual(1, len(pools2))

        ip_address = GlobalIPManager.get_ip('192.169.0.100')
        self.assertEqual('192.169.0.100', ip_address.address)
        self.assertEqual(pool2.id, ip_address.pool.id)
