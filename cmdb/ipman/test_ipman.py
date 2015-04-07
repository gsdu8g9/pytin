from django.test import TestCase

from ipman.models import IPNetwork, IPAddress


class IPmanTest(TestCase):
    def test_to_string(self):
        ipnet = IPNetwork.create(network='192.168.1.1/24')
        ip = IPAddress.create(address='172.1.1.5')

        self.assertEqual('192.168.1.0/24', str(ipnet))
        self.assertEqual('172.1.1.5', str(ip))

    def test_is_from_network(self):
        ipnet = IPNetwork.create(network='192.168.1.1/24')

        ip1 = ipnet.next_usable()
        ip2 = IPAddress.create(address='172.1.1.5')

        self.assertTrue(ipnet.owns(ip1))
        self.assertFalse(ipnet.owns(ip2))

        self.assertTrue(ip1 in ipnet)
        self.assertFalse(ip2 in ipnet)


    def test_ipv4_acquire(self):
        """
        Test ip addresses acquisition
        """
        ipnet = IPNetwork.create(network='192.168.1.1/24')

        ip1 = ipnet.next_usable()
        ip2 = ipnet.next_usable()

        self.assertEqual('192.168.1.0/24', ipnet.network)
        self.assertEqual(4, ipnet.version)

        self.assertEqual('192.168.1.1', str(ip1))
        self.assertEqual(4, ip1.version)

        self.assertEqual('192.168.1.1', str(ip2))
        self.assertEqual(4, ip2.version)

        # Acquire IP
        ip1.use()
        ip1.save()

        ip2 = ipnet.next_usable()

        self.assertEqual('192.168.1.2', str(ip2))
        self.assertEqual(4, ip2.version)
