from django.test import TestCase

from ipman.models import IPAddress, IPNetworkPool, IPAddressPool, IPAddressRangePool
from resources.models import Resource


class IPmanTest(TestCase):

    def test_ip_beauty(self):
        self.assertEqual(4, IPAddress.create(address='46.17.40.29').beauty)
        self.assertEqual(8, IPAddress.create(address='172.27.27.27').beauty)
        self.assertEqual(7, IPAddress.create(address='46.17.46.17').beauty)
        self.assertEqual(7, IPAddress.create(address='46.17.46.64').beauty)
        self.assertEqual(1, IPAddress.create(address='237.45.160.89').beauty)
        self.assertEqual(2, IPAddress.create(address='237.45.169.89').beauty)
        self.assertEqual(10, IPAddress.create(address='111.11.11.11').beauty)

    def test_polymorfic_pool_list(self):
        ip_pool_types = [
            IPAddressPool.__name__,
            IPAddressRangePool.__name__,
            IPNetworkPool.__name__
        ]

        IPAddressPool.create(name='Test ip set')
        IPAddressRangePool.create(name='IP range', range_from='172.1.1.1', range_to='172.1.2.1')
        IPNetworkPool.create(network='192.168.1.1/24')

        pools = Resource.objects.active(type__in=ip_pool_types)

        self.assertEqual(3, len(pools))
        self.assertEqual('IPAddressPool', pools[0].type)
        self.assertEqual(IPAddressPool, pools[0].__class__)
        self.assertEqual('IPAddressRangePool', pools[1].type)
        self.assertEqual(IPAddressRangePool, pools[1].__class__)
        self.assertEqual('IPNetworkPool', pools[2].type)
        self.assertEqual(IPNetworkPool, pools[2].__class__)

    def test_network_pool_usage(self):
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')

        self.assertEqual(256, ipnet.total_addresses)
        self.assertEqual(0, ipnet.used_addresses)
        self.assertEqual(0, ipnet.usage)

        for x in range(1, 50):
            ipaddr = ipnet.available().next()
            ipaddr.use()
            ipaddr.save()

        self.assertEqual(256, ipnet.total_addresses)
        self.assertEqual(49, ipnet.used_addresses)
        self.assertEqual(19, ipnet.usage)

    def test_ip_range_usage(self):
        iprange = IPAddressRangePool.create(name='IP range', range_from='172.1.1.1', range_to='172.1.2.1')

        self.assertEqual(257, iprange.total_addresses)
        self.assertEqual(0, iprange.used_addresses)
        self.assertEqual(0, iprange.usage)

        for x in range(1, 50):
            ipaddr = iprange.available().next()
            ipaddr.use()
            ipaddr.save()

        self.assertEqual(257, iprange.total_addresses)
        self.assertEqual(49, iprange.used_addresses)
        self.assertEqual(19, iprange.usage)

    def test_ip_list_usage(self):
        ipset = IPAddressPool.create(name='Test ip set')

        for x in range(1, 100):
            ipset += IPAddress.create(address='172.27.27.%s' % x)

        self.assertEqual(99, ipset.total_addresses)
        self.assertEqual(0, ipset.used_addresses)
        self.assertEqual(0, ipset.usage)

        for x in range(1, 50):
            ipaddr = ipset.available().next()
            ipaddr.use()
            ipaddr.save()

        self.assertEqual(99, ipset.total_addresses)
        self.assertEqual(49, ipset.used_addresses)
        self.assertEqual(49, ipset.usage)

    def test_pool_add_sub(self):
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')

        self.assertEqual(24, ipnet.get_option_value('prefixlen'))
        self.assertEqual('255.255.255.0', ipnet.get_option_value('netmask'))
        self.assertEqual('192.168.1.1', ipnet.get_option_value('gateway'))
        self.assertEqual('', ipnet.get_option_value('nameservers'))

        ip1 = ipnet.available().next()
        ip2 = IPAddress.create(address='192.168.1.2')

        self.assertEqual(ipnet.id, ip1.parent_id)
        self.assertEqual(None, ip2.parent_id)

        ipnet += ip2
        ipnet -= ip1

        self.assertEqual(None, ip1.parent_id)
        self.assertEqual(ipnet.id, ip2.parent_id)

    def test_pool_range_owns_acquire(self):
        iprange = IPAddressRangePool.create(name='IP range', range_from='172.1.1.1', range_to='172.1.2.1')

        self.assertTrue(iprange.can_add('172.1.1.155'))
        self.assertFalse(iprange.can_add('172.1.2.10'))

        usable_ip = iprange.available().next()
        self.assertEqual('172.1.1.1', usable_ip.address)

        usable_ip.use()
        usable_ip.save()

        usable_ip = iprange.available().next()
        self.assertEqual('172.1.1.2', usable_ip.address)

    def test_pool_set_owns_acquire(self):
        ipset = IPAddressPool.create(name='Set of IPs, used by JustHost.ru, Kazan')

        self.assertTrue(ipset.can_add('192.168.1.10'))
        self.assertRaises(StopIteration, ipset.available().next)

        # add resource to the pool
        ipset += IPAddress.create(address='172.27.27.10')

        usable_ip = ipset.available().next()
        self.assertEqual('172.27.27.10', usable_ip.address)

        usable_ip.use()
        usable_ip.save()

        self.assertRaises(StopIteration, ipset.available().next)

    def test_pool_network_ipv4_to_string(self):
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')
        ip = IPAddress.create(address='172.1.1.5')

        self.assertEqual('192.168.1.0/24', str(ipnet))
        self.assertEqual('172.1.1.5', str(ip))

    def test_pool_network_ipv4_owns(self):
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')

        ip1 = ipnet.available().next()
        ip2 = IPAddress.create(address='172.1.1.5')

        self.assertTrue(ipnet.can_add(ip1))
        self.assertFalse(ipnet.can_add(ip2))

        self.assertTrue(ip1 in ipnet)
        self.assertFalse(ip2 in ipnet)

    def test_cross_pool_ip_usage(self):
        """
        Test ip addresses acquisition
        """
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')
        ipset = IPAddressPool.create(name='Set of IPs elsewhere')

        ip1 = ipnet.available().next()
        ip2 = ipnet.available().next()

        self.assertEqual('192.168.1.1', str(ip1))
        self.assertEqual(4, ip1.version)

        self.assertEqual('192.168.1.1', str(ip2))
        self.assertEqual(4, ip2.version)

        # use IP elsewhere
        ip2.parent = ipset
        ip2.save()

        ip3 = ipnet.available().next()

        self.assertEqual('192.168.1.2', str(ip3))
        self.assertEqual(4, ip3.version)

    def test_pool_network_ipv4_acquire(self):
        """
        Test ip addresses acquisition
        """
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')

        ip1 = ipnet.available().next()
        ip2 = ipnet.available().next()

        self.assertEqual('192.168.1.0/24', ipnet.network)
        self.assertEqual(4, ipnet.version)

        self.assertEqual('192.168.1.1', str(ip1))
        self.assertEqual(4, ip1.version)

        self.assertEqual('192.168.1.1', str(ip2))
        self.assertEqual(4, ip2.version)

        # Acquire IP
        ip1.use()
        ip1.save()

        ip2 = ipnet.available().next()

        self.assertEqual('192.168.1.2', str(ip2))
        self.assertEqual(4, ip2.version)

    def test_pool_network_polymorphic(self):
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')

        ip1 = ipnet.available().next()
        ip2 = IPAddress.create(address='172.1.1.5')

        self.assertTrue(ipnet.can_add(ip1))
        self.assertFalse(ipnet.can_add(ip2))

        # polymorphic
        polipnet = Resource.objects.get(pk=ipnet.id)
        self.assertTrue(polipnet.can_add(ip1))
        self.assertFalse(polipnet.can_add(ip2))

        polipnets = Resource.objects.filter(network='192.168.1.0/24')
        self.assertEqual(1, len(polipnets))
        self.assertTrue(polipnets[0].can_add(ip1))
        self.assertFalse(polipnets[0].can_add(ip2))
