import os

from django.test import TestCase

from importer.providers.vendors.hp import HP1910Switch
from importer.providers.vendors.qtech import QtechL3Switch, Qtech3400Switch


class QSW8300ProvidersTest(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_l3_hp_switch(self):
        switch = HP1910Switch()
        switch._add_switch_port(None, 'sdfjskdfhsdkfh')
        switch._add_switch_port(5, 'GigabitEthernet1/0/5')

        swports = list(switch.ports)
        self.assertEqual(5, swports[0].number)
        self.assertEqual(True, swports[0].is_local)

        self.assertEqual(None, swports[1].number)
        self.assertEqual(False, swports[1].is_local)

    def test_l3_qtech_switch(self):
        switch = Qtech3400Switch()

        file_path = os.path.join(self.DATA_DIR, 'mac-table.txt')
        switch.from_mac_dump(file_path)

        test_data = {}

        for switch_port in switch.ports:
            test_data[switch_port.name] = {
                'num': switch_port.number,
                'islocal': switch_port.is_local,
                'macs': switch_port.macs
            }

        self.assertEqual(34, len(test_data))

        self.assertEqual(15, test_data['ethernet1/15']['num'])
        self.assertEqual(True, test_data['ethernet1/15']['islocal'])
        self.assertEqual(1, len(test_data['ethernet1/15']['macs']))

        self.assertEqual(None, test_data['port-channel1']['num'])
        self.assertEqual(False, test_data['port-channel1']['islocal'])
        self.assertEqual(37, len(test_data['port-channel1']['macs']))
        self.assertEqual('Intel Corporate', test_data['port-channel1']['macs'][0].vendor)
