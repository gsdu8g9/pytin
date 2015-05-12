from django.test import TestCase

from ipman.models import IPAddress, IPNetworkPool, IPAddressPool, IPAddressRangePool


class IPmanTest(TestCase):
    def test_pool_add_sub(self):
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')

        self.assertEqual(24, ipnet.prefixlen)
        self.assertEqual('255.255.255.0', ipnet.netmask)
        self.assertEqual('192.168.1.1', ipnet.gateway)
        self.assertEqual('', ipnet.nameservers)

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
