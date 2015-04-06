from django.test import TestCase

from ipman.models import IPNetwork


class IPmanTest(TestCase):
    def test_ipv4_acquire(self):
        """
        Test ip addresses acquisition
        """
        ipnet = IPNetwork.create(network=u'192.168.1.1/24')

        ip1 = ipnet.next_usable()
        ip2 = ipnet.next_usable()

        self.assertEqual(u'192.168.1.0/24', ipnet.network)
        self.assertEqual(4, ipnet.version)

        self.assertEqual(u'192.168.1.1', unicode(ip1))
        self.assertEqual(4, ip1.version)

        self.assertEqual(u'192.168.1.1', unicode(ip2))
        self.assertEqual(4, ip2.version)

        # Acquire IP
        ip1.use()
        ip1.save()

        ip2 = ipnet.next_usable()

        self.assertEqual(u'192.168.1.2', unicode(ip2))
        self.assertEqual(4, ip2.version)
