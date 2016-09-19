from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ipman.models import IPAddressPoolFactory, GlobalIPManager


class IPPoolTest(TestCase):
    def test_move_ips(self):
        pool1 = IPAddressPoolFactory.from_network('192.168.1.0/24')
        pool2 = IPAddressPoolFactory.from_network('192.168.2.0/23')
        pool3 = IPAddressPoolFactory.from_name('Target pool')

        self.assertEqual(254, pool1.get_ips().count())
        self.assertEqual(510, pool2.get_ips().count())
        self.assertEqual(0, pool3.get_ips().count())

        GlobalIPManager.move_ips(pool3, '192.168.1.100', 50)
        GlobalIPManager.move_ips(pool3, '192.168.2.100', 1)

        self.assertEqual(204, pool1.get_ips().count())
        self.assertEqual(509, pool2.get_ips().count())
        self.assertEqual(51, pool3.get_ips().count())

    def test_peer_network(self):
        pool = IPAddressPoolFactory.from_network(network='87.251.133.9/31')
        self.assertEqual(2, pool.get_ips().count())

    def test_create_from_network(self):
        pool1 = IPAddressPoolFactory.from_network('192.168.1.0/24')
        pool2 = IPAddressPoolFactory.from_network('192.168.2.0/23')

        self.assertEqual(254, pool1.get_ips().count())
        self.assertEqual(254, pool1.get_free_ips().count())
        self.assertEqual('192.168.1.0/24', pool1.name)
        self.assertEqual('192.168.1.1', pool1.get_option_value('gateway'))
        self.assertEqual('255.255.255.0', pool1.get_option_value('netmask'))

        self.assertEqual(510, pool2.get_ips().count())
        self.assertEqual(510, pool2.get_free_ips().count())
        self.assertEqual('192.168.2.0/23', pool2.name)
        self.assertEqual('192.168.2.1', pool2.get_option_value('gateway'))
        self.assertEqual('255.255.254.0', pool2.get_option_value('netmask'))

    def test_create_from_range(self):
        pool1 = IPAddressPoolFactory.from_range('46.17.40.50', '46.17.40.192')

        self.assertEqual(143, pool1.get_ips().count())
        self.assertEqual(143, pool1.get_free_ips().count())
        self.assertEqual('46.17.40.50-46.17.40.192', pool1.name)
