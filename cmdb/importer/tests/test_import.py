import os

from django.test import TestCase

from assets.models import RegionResource, ServerPort, Server, VirtualServer, GatewaySwitch, PortConnection
from importer.importlib import CmdbImporter

from importer.providers.qtech.qsw8300 import QSW8300ArpTableFileDump
from ipman.models import IPNetworkPool, IPAddress


class QSW8300ImportDataTest(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_import_data(self):
        file_path = os.path.join(self.DATA_DIR, 'arp-table.txt')

        cmdb_importer = CmdbImporter()

        # create IP pools and basic structure
        dc_anders = RegionResource.create(name="Anders")
        dc_rtcom = RegionResource.create(name="Rostelecom")

        # create source switch
        anders_gw = GatewaySwitch.create(name="baxet-gw-q", parent=dc_anders)

        # arp table provider
        arp_table = QSW8300ArpTableFileDump(file_path, anders_gw.id)
        arp_table_list = list(arp_table)

        self.assertEqual(1332, len(arp_table_list))

        # Add our IP pools
        pool_list = [IPNetworkPool.create(network='46.17.40.0/23', parent=dc_anders),
                     IPNetworkPool.create(network='46.17.44.0/23', parent=dc_anders),
                     IPNetworkPool.create(network='176.32.34.0/23', parent=dc_anders),
                     IPNetworkPool.create(network='176.32.36.0/24', parent=dc_anders),
                     IPNetworkPool.create(network='176.32.37.0/24', parent=dc_anders),
                     IPNetworkPool.create(network='176.32.38.0/24', parent=dc_anders),
                     IPNetworkPool.create(network='176.32.39.0/24', parent=dc_anders),
                     IPNetworkPool.create(network='2a00:b700::/48', parent=dc_anders),
                     IPNetworkPool.create(network='46.17.46.0/23', parent=dc_rtcom),
                     IPNetworkPool.create(network='46.29.160.0/23', parent=dc_rtcom),
                     IPNetworkPool.create(network='176.32.32.0/23', parent=dc_rtcom),
                     IPNetworkPool.create(network='46.29.162.0/23', parent=dc_rtcom),
                     IPNetworkPool.create(network='46.29.164.0/22', parent=dc_rtcom),
                     IPNetworkPool.create(network='185.22.152.0/22', parent=dc_rtcom),
                     IPNetworkPool.create(network='2a00:b700:1::/48', parent=dc_rtcom)]

        # Double the IP, to test update process
        arp_table_list.extend(arp_table)

        for arp_record in arp_table_list:
            cmdb_importer.add_arp_record(anders_gw, arp_record)

        # -1 IP: 87.251.133.9, /30 peering network address
        self.assertEqual(1331, len(IPAddress.objects.active()))

        for pool in pool_list:
            print "%s - %d" % (pool, pool.usage)

        # count servers
        self.assertEqual(72, len(Server.objects.active()))
        self.assertEqual(43, len(VirtualServer.objects.active()))
        self.assertEqual(115, len(ServerPort.objects.active()))
        self.assertEqual(10, len(PortConnection.objects.active()))
