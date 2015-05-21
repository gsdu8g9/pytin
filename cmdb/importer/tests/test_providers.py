import os

from django.test import TestCase

from importer.providers.qtech.qsw8300 import QSW8300ArpTableFileDump, QSW8300MacTableFileDump


class QSW8300ProvidersTest(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_load_arp_table(self):
        file_path = os.path.join(self.DATA_DIR, 'arp-table.txt')

        arp_table = QSW8300ArpTableFileDump(file_path, 11)
        arp_table_list = list(arp_table)

        self.assertEqual(1332, len(arp_table_list))

        self.assertEqual('46.17.40.2', arp_table_list[0].ip)
        self.assertEqual('827D7CE0B36E', arp_table_list[0].mac)
        self.assertEqual('Port-Channel1', arp_table_list[0].port)
        self.assertEqual(11, arp_table_list[0].source_device_id)

        self.assertEqual('176.32.36.226', arp_table_list[735].ip)
        self.assertEqual('002590892FC6', arp_table_list[735].mac)
        self.assertEqual(16, arp_table_list[735].port)
        self.assertEqual(11, arp_table_list[735].source_device_id)

        self.assertEqual('176.32.37.164', arp_table_list[900].ip)
        self.assertEqual('001E6766BA7E', arp_table_list[900].mac)
        self.assertEqual(13, arp_table_list[900].port)

    def test_load_mac_table(self):
        file_path = os.path.join(self.DATA_DIR, 'mac-table.txt')

        mac_table = QSW8300MacTableFileDump(file_path, 11)

        mac_table_list = list(mac_table)

        self.assertEqual(125, len(mac_table_list))

        self.assertEqual('003048DE46F9', mac_table_list[70].mac)
        self.assertEqual('Port-Channel2', mac_table_list[70].port)
        self.assertEqual('Supermicro Computer, Inc.', mac_table_list[70].vendor)
        self.assertEqual(11, mac_table_list[70].source_device_id)

        self.assertEqual('90E6BA93EE9D', mac_table_list[100].mac)
        self.assertEqual(17, mac_table_list[100].port)
        self.assertEqual('ASUSTek COMPUTER INC.', mac_table_list[100].vendor)
