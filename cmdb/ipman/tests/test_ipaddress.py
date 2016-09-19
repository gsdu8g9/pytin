from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from assets.models import VirtualServer, RegionResource, Datacenter
from ipman.models import IPAddressGeneric, IPAddressRenter, IPAddressPoolFactory
from ipman.tests import utils
from resources.models import Resource


class IPAddressTest(TestCase):
    def test_rent_ips_from_dc(self):
        moscow = RegionResource.objects.create(name='Moscow')
        dc1 = Datacenter.objects.create(name='Test DC 1', parent=moscow)
        dc2 = Datacenter.objects.create(name='Test DC 2', parent=moscow)

        net_pool1 = IPAddressPoolFactory.from_network(network="46.17.40.0/24", parent=dc1)
        net_pool2 = IPAddressPoolFactory.from_network(network="46.17.41.0/24", parent=dc1)

        net_pool3 = IPAddressPoolFactory.from_network(network="46.17.42.0/24", parent=dc2)

        self.assertEqual(254, net_pool1.get_free_ips().count())
        self.assertEqual(254, net_pool2.get_free_ips().count())
        self.assertEqual(254, net_pool3.get_free_ips().count())

        renter = IPAddressRenter.from_datacenter(dc1, ip_version=4)
        ips = renter.rent(count=25)
        self.assertEqual(25, len(ips))

        self.assertEqual(241, net_pool1.get_free_ips().count())
        self.assertEqual(242, net_pool2.get_free_ips().count())
        self.assertEqual(254, net_pool3.get_free_ips().count())

    def test_rent_ips(self):
        net_pool1 = IPAddressPoolFactory.from_name(name='Generic pool 1')
        utils.fill_ip_pool(net_pool1, c_size=3, d_size=25, prefix='46.17.')

        net_pool2 = IPAddressPoolFactory.from_name(name='Generic pool 2')
        utils.fill_ip_pool(net_pool2, c_size=5, d_size=35, prefix='46.18.')

        self.assertEqual(48, net_pool1.get_free_ips().count())
        self.assertEqual(136, net_pool2.get_free_ips().count())

        renter = IPAddressRenter()
        renter.add_source(net_pool1)
        renter.add_source(net_pool2)

        # 5 and 5 addresses reserved
        ips = renter.rent(count=10)
        self.assertEqual(10, len(ips))

        self.assertEqual(48 - 5, net_pool1.get_free_ips().count())
        self.assertEqual(136 - 5, net_pool2.get_free_ips().count())

        # 3 and 2 addresses reserved
        ips = renter.rent(count=5)
        self.assertEqual(5, len(ips))

        self.assertEqual(48 - 5 - 3, net_pool1.get_free_ips().count())
        self.assertEqual(136 - 5 - 2, net_pool2.get_free_ips().count())

        # 1 addresses reserved
        ips = renter.rent(count=1)
        self.assertEqual(1, len(ips))

        self.assertEqual(48 - 5 - 3 - 1, net_pool1.get_free_ips().count())
        self.assertEqual(136 - 5 - 2, net_pool2.get_free_ips().count())

    def test_mass_manage_ip(self):
        net_pool1 = IPAddressPoolFactory.from_name(name='Generic pool 1')
        net_pool2 = IPAddressPoolFactory.from_name(name='Generic pool 2')

        utils.fill_ip_pool(net_pool1, c_size=25, d_size=105)

        self.assertEqual(2496, net_pool1.total_addresses)
        self.assertEqual(0, net_pool2.total_addresses)

        IPAddressGeneric.objects.filter(address__startswith='46.17.10.').update(pool=net_pool2)
        self.assertEqual(2392, net_pool1.total_addresses)
        self.assertEqual(104, net_pool2.total_addresses)

    def test_pool_usage(self):
        ipv4_net_pool = IPAddressPoolFactory.from_name(name='Generic pool')
        ipv4_net_pool.use()

        utils.fill_ip_pool(ipv4_net_pool, c_size=25, d_size=105)

        all_count = IPAddressGeneric.objects.all().count() / 3
        vm1 = VirtualServer.objects.create(label="VM", status=Resource.STATUS_INUSE)
        for address in IPAddressGeneric.objects.filter():
            if all_count <= 0:
                break

            all_count -= 1
            address.use(parent=vm1)

        self.assertEqual(2496, ipv4_net_pool.total_addresses)
        self.assertEqual(832, ipv4_net_pool.used_addresses)

    def test_add_ip(self):
        ipv4 = '46.17.40.27'
        ipv6 = '2001:0::ab:cd'

        ipv4_net_pool = IPAddressPoolFactory.from_name(name='ipv4_net_pool')
        ipv6_net_pool = IPAddressPoolFactory.from_name(name='ipv6_net_pool')

        addrv4, created = IPAddressGeneric.objects.update_or_create(address=ipv4, pool=ipv4_net_pool)
        self.assertEqual('46.17.40.27', "%s" % addrv4)

        addrv6, created = IPAddressGeneric.objects.update_or_create(address=ipv6, pool=ipv6_net_pool)
        self.assertEqual('2001:0::ab:cd', "%s" % addrv6)
