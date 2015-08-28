from django.core.exceptions import ValidationError

from django.test import TestCase

from assets.models import VirtualServer
from ipman.models import IPAddress, IPNetworkPool, IPAddressPool, IPAddressRangePool
from resources.models import Resource


class IPmanTest(TestCase):
    def setUp(self):
        print self._testMethodName

    def test_free_ip(self):
        vm1 = VirtualServer.objects.create(label="VM", status=Resource.STATUS_INUSE)

        ip_net_pool = IPNetworkPool.objects.create(network='192.168.1.1/24', status=Resource.STATUS_INUSE)
        ip1 = ip_net_pool.available().next()
        ip1.use()
        ip1.refresh_from_db()

        ip2 = ip_net_pool.available().next()
        ip2.parent = ip1
        ip2.use()
        ip2.refresh_from_db()

        self.assertEqual(ip_net_pool.id, ip1.parent_id)
        self.assertEqual(Resource.STATUS_INUSE, ip1.status)

        # assign IP
        ip1.parent = vm1
        ip1.save()
        ip1.refresh_from_db()

        self.assertEqual(vm1.id, ip1.parent_id)
        self.assertEqual(ip_net_pool.id, ip1.get_origin())
        self.assertEqual(Resource.STATUS_INUSE, ip1.status)

        ip1.free()
        ip1.refresh_from_db()

        self.assertEqual(ip_net_pool.id, ip1.parent_id)
        self.assertEqual(ip_net_pool.id, ip1.get_origin())
        self.assertEqual(Resource.STATUS_FREE, ip1.status)
        self.assertEqual(Resource.STATUS_INUSE, ip2.status)

        ip1.free(cascade=True)
        ip1.refresh_from_db()
        ip2.refresh_from_db()
        self.assertEqual(Resource.STATUS_FREE, ip1.status)
        self.assertEqual(Resource.STATUS_FREE, ip2.status)

    def test_delete_ips_and_pool(self):
        ip_net_pool = IPNetworkPool.objects.create(network='192.168.1.1/24', status=Resource.STATUS_INUSE)
        ip1 = ip_net_pool.available().next()
        ip1.use()
        ip2 = IPAddress.objects.create(address='46.17.40.29', status=Resource.STATUS_INUSE)

        self.assertEqual(Resource.STATUS_INUSE, ip_net_pool.status)
        self.assertEqual(Resource.STATUS_INUSE, ip1.status)
        self.assertEqual(Resource.STATUS_INUSE, ip2.status)

        # IP pool is not deleted until there is some IPs
        try:
            ip_net_pool.delete()
            self.fail("Waiting for the exception.")
        except ValidationError:
            pass

        # IP addresses are normally deleted
        ip1.delete()
        ip2.delete()

        ip_net_pool.delete()

        ip1.refresh_from_db()
        ip2.refresh_from_db()
        ip_net_pool.refresh_from_db()

        self.assertTrue(IPAddress.objects.filter(pk=ip1.id).exists())
        self.assertEqual(Resource.STATUS_DELETED, ip_net_pool.status)
        self.assertEqual(Resource.STATUS_DELETED, ip2.status)
        self.assertEqual(Resource.STATUS_DELETED, ip1.status)

    def test_add_wrong_network(self):
        self.assertRaises(Exception, IPNetworkPool.active.create, network='192.168.1/24')

        pools = Resource.active.filter(type=IPNetworkPool.__name__)
        self.assertEqual(1, len(pools))
        self.assertEqual('0.0.0.0/0', str(pools[0]))

    def test_ip_beauty(self):
        self.assertEqual(4, IPAddress.objects.create(address='46.17.40.29').beauty)
        self.assertEqual(8, IPAddress.objects.create(address='172.27.27.27').beauty)
        self.assertEqual(7, IPAddress.objects.create(address='46.17.46.17').beauty)
        self.assertEqual(7, IPAddress.objects.create(address='46.17.46.64').beauty)
        self.assertEqual(1, IPAddress.objects.create(address='237.45.160.89').beauty)
        self.assertEqual(2, IPAddress.objects.create(address='237.45.169.89').beauty)
        self.assertEqual(10, IPAddress.objects.create(address='111.11.11.11').beauty)

    def test_polymorfic_pool_list(self):
        ip_pool_types = [
            IPAddressPool.__name__,
            IPAddressRangePool.__name__,
            IPNetworkPool.__name__
        ]

        IPAddressPool.objects.create(name='Test ip set')
        IPAddressRangePool.objects.create(name='IP range', range_from='172.1.1.1', range_to='172.1.2.1')
        IPNetworkPool.objects.create(network='192.168.1.1/24')

        pools = Resource.active.filter(type__in=ip_pool_types)

        self.assertEqual(3, len(pools))
        self.assertEqual('IPAddressPool', pools[0].type)
        self.assertEqual(IPAddressPool, pools[0].__class__)
        self.assertEqual('IPAddressRangePool', pools[1].type)
        self.assertEqual(IPAddressRangePool, pools[1].__class__)
        self.assertEqual('IPNetworkPool', pools[2].type)
        self.assertEqual(IPNetworkPool, pools[2].__class__)

    def test_network_pool_usage(self):
        ipnet = IPNetworkPool.objects.create(network='192.168.1.1/24')

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
        iprange = IPAddressRangePool.objects.create(name='IP range', range_from='172.1.1.1', range_to='172.1.2.1')

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
        ipset = IPAddressPool.objects.create(name='Test ip set')

        # Test empty IP set usage
        self.assertEqual(0, ipset.usage)

        for x in range(1, 100):
            ipset += IPAddress.objects.create(address='172.27.27.%s' % x)

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
        ipnet = IPNetworkPool.objects.create(network='192.168.1.1/24')

        self.assertEqual(24, ipnet.get_option_value('prefixlen'))
        self.assertEqual('255.255.255.0', ipnet.get_option_value('netmask'))
        self.assertEqual('192.168.1.1', ipnet.get_option_value('gateway'))
        self.assertEqual('', ipnet.get_option_value('nameservers'))

        ip1 = ipnet.available().next()
        ip2 = IPAddress.objects.create(address='192.168.1.2')

        self.assertEqual(ipnet.id, ip1.parent_id)
        self.assertEqual(None, ip2.parent_id)

        ipnet += ip2
        ipnet -= ip1

        self.assertEqual(None, ip1.parent_id)
        self.assertEqual(ipnet.id, ip2.parent_id)

    def test_pool_range_owns_acquire(self):
        iprange = IPAddressRangePool.objects.create(name='IP range', range_from='172.1.1.1', range_to='172.1.2.1')

        self.assertTrue(iprange.can_add('172.1.1.155'))
        self.assertFalse(iprange.can_add('172.1.2.10'))

        usable_ip = iprange.available().next()
        self.assertEqual('172.1.1.2', usable_ip.address)

        usable_ip.use()
        usable_ip.save()

        usable_ip = iprange.available().next()
        self.assertEqual('172.1.1.3', usable_ip.address)

    def test_pool_set_owns_acquire(self):
        ipset = IPAddressPool.objects.create(name='Set of IPs, used by JustHost.ru, Kazan')

        self.assertTrue(ipset.can_add('192.168.1.10'))
        self.assertRaises(StopIteration, ipset.available().next)

        # add resource to the pool
        ipset += IPAddress.objects.create(address='172.27.27.10')

        usable_ip = ipset.available().next()
        self.assertEqual('172.27.27.10', usable_ip.address)

        usable_ip.use()
        usable_ip.save()

        self.assertRaises(StopIteration, ipset.available().next)

    def test_pool_network_ipv4_to_string(self):
        ipnet = IPNetworkPool.objects.create(network='192.168.1.1/24')
        ip = IPAddress.objects.create(address='172.1.1.5')

        self.assertEqual('192.168.1.0/24', str(ipnet))
        self.assertEqual('172.1.1.5', str(ip))

    def test_pool_network_ipv4_owns(self):
        ipnet = IPNetworkPool.objects.create(network='192.168.1.1/24')

        ip1 = ipnet.available().next()
        ip2 = IPAddress.objects.create(address='172.1.1.5')

        self.assertTrue(ipnet.can_add(ip1))
        self.assertFalse(ipnet.can_add(ip2))

        self.assertTrue(ip1 in ipnet)
        self.assertFalse(ip2 in ipnet)

    def test_cross_pool_ip_usage(self):
        """
        Test ip addresses acquisition
        """
        ipnet = IPNetworkPool.objects.create(network='192.168.1.1/24')
        ipset = IPAddressPool.objects.create(name='Set of IPs elsewhere')

        ip1 = ipnet.available().next()
        ip2 = ipnet.available().next()

        self.assertEqual('192.168.1.2', str(ip1))
        self.assertEqual(4, ip1.version)

        self.assertEqual('192.168.1.2', str(ip2))
        self.assertEqual(4, ip2.version)

        # use IP elsewhere
        ip2.parent = ipset
        ip2.save()

        ip3 = ipnet.available().next()

        self.assertEqual('192.168.1.3', str(ip3))
        self.assertEqual(4, ip3.version)

    def test_pool_network_ipv4_acquire(self):
        """
        Test ip addresses acquisition
        """
        ipnet = IPNetworkPool.objects.create(network='192.168.1.1/24')

        ip1 = ipnet.available().next()
        ip2 = ipnet.available().next()

        self.assertEqual('192.168.1.0/24', ipnet.network)
        self.assertEqual(4, ipnet.version)

        self.assertEqual('192.168.1.2', str(ip1))
        self.assertEqual(4, ip1.version)

        self.assertEqual('192.168.1.2', str(ip2))
        self.assertEqual(4, ip2.version)

        # Acquire IP
        ip1.use()
        ip1.save()

        ip2 = ipnet.available().next()

        self.assertEqual('192.168.1.3', str(ip2))
        self.assertEqual(4, ip2.version)

    def test_pool_network_polymorphic(self):
        ipnet = IPNetworkPool.objects.create(network='192.168.1.1/24')

        ip1 = ipnet.available().next()
        ip2 = IPAddress.objects.create(address='172.1.1.5')

        self.assertTrue(ipnet.can_add(ip1))
        self.assertFalse(ipnet.can_add(ip2))

        # polymorphic
        polipnet = Resource.active.get(pk=ipnet.id)
        self.assertTrue(polipnet.can_add(ip1))
        self.assertFalse(polipnet.can_add(ip2))

        polipnets = Resource.active.filter(network='192.168.1.0/24')
        self.assertEqual(1, len(polipnets))
        self.assertTrue(polipnets[0].can_add(ip1))
        self.assertFalse(polipnets[0].can_add(ip2))
