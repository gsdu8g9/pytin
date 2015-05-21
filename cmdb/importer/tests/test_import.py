import os

from django.test import TestCase

from assets.models import RegionResource, ServerPort, Server, VirtualServer

from importer.providers.qtech.qsw8300 import QSW8300ArpTableFileDump
from ipman.models import IPNetworkPool, IPAddress
from resources.models import Resource


class QSW8300ImportDataTest(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_import_data(self):
        file_path = os.path.join(self.DATA_DIR, 'arp-table.txt')

        arp_table = QSW8300ArpTableFileDump(file_path)
        arp_table_list = list(arp_table)

        self.assertEqual(1332, len(arp_table_list))

        # create IP pools and basic structure
        dc_anders = RegionResource.create(name="Anders")
        dc_rtcom = RegionResource.create(name="Rostelecom")

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
            added = False
            for ip_pool in pool_list:
                if ip_pool.can_add(arp_record.ip):
                    ips = IPAddress.objects.active(address__exact=arp_record.ip)
                    if len(ips) > 0:
                        ips[0].use()

                        if len(ips) > 1:
                            print "ERROR: Duplicate IP %s!" % arp_record.ip
                    else:
                        # print "Add %s to %s" % (arp_record.ip, ip_pool)
                        IPAddress.create(address=arp_record.ip, status=Resource.STATUS_INUSE, parent=ip_pool)

                    added = True
                    break

            if not added:
                print "!!! IP %s is not added" % arp_record.ip

        # -1 IP: 87.251.133.9, /30 peering network address
        self.assertEqual(1331, len(IPAddress.objects.active()))

        for pool in pool_list:
            print "%s - %d" % (pool, pool.usage)

        # Updating Interface-IP relations
        for arp_record in arp_table_list:
            server_port = None
            ports = ServerPort.objects.active(mac=arp_record.mac)
            if len(ports) <= 0:
                # create server and port
                server = None
                if arp_record.vendor:
                    server = Server.create(label='Server', vendor=arp_record.vendor)
                else:
                    server = VirtualServer.create(label='VPS')

                server_port = ServerPort.create(mac=arp_record.mac, parent=server)
            else:
                server_port = ports[0]

                if len(ports) > 1:
                    print "ERROR: Duplicate ports found with mac: %s!" % arp_record.mac

            # add IP to the port
            ips = IPAddress.objects.active(address__exact=arp_record.ip)
            if len(ips) > 0:
                ips[0].parent = server_port
                ips[0].use()
            else:
                print "Add %s to %s" % (arp_record.ip, server_port)
                IPAddress.create(address=arp_record.ip, status=Resource.STATUS_INUSE, parent=server_port)

        # count servers
        self.assertEqual(72, len(Server.objects.active()))
        self.assertEqual(43, len(VirtualServer.objects.active()))
        self.assertEqual(115, len(ServerPort.objects.active()))
