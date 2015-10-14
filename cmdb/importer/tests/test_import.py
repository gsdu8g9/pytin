from __future__ import unicode_literals
import os

from django.test import TestCase

from assets.models import Server, Switch, VirtualServer, ServerPort, PortConnection, VirtualServerPort, SwitchPort
from importer.importlib import GenericCmdbImporter
from importer.providers.l3_switch import L3Switch
from resources.models import Resource


class QSW8300ImportDataTest(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_hypervisor_no_detect_hypervisor(self):
        switch = L3Switch()

        switch._add_switch_port(24, 'ethernet/1/24')
        switch._add_server_port('ethernet/1/24', '0025904EB5A4')
        switch._add_server_port('ethernet/1/24', '0025904EB5A5')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2080C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2081C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2082C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2083C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2084C')

        # manually identify hypervisor
        hv_server = Server.objects.create(label="hvisor", server_role='hypervisor')
        ServerPort.objects.create(mac='0025904EB5A4', parent=hv_server)

        cmdb_importer = GenericCmdbImporter()

        sw = Switch.objects.create(label="switch")
        cmdb_importer.import_switch(sw.id, switch)

        self.assertEqual(2, len(Server.active.filter()))
        self.assertEqual(5, len(VirtualServer.active.filter()))
        self.assertEqual(5, len(VirtualServer.active.filter(parent=None)))
        self.assertEqual(2, len(ServerPort.active.filter()))
        self.assertEqual(0, len(ServerPort.active.filter(parent=None)))
        self.assertEqual(5, len(VirtualServerPort.active.filter()))
        self.assertEqual(0, len(VirtualServerPort.active.filter(parent=None)))
        self.assertEqual(7, len(PortConnection.active.filter()))

    def test_hypervisor_no_detect(self):
        switch = L3Switch()

        switch._add_switch_port(24, 'ethernet/1/24')
        switch._add_server_port('ethernet/1/24', '0025904EB5A4')
        switch._add_server_port('ethernet/1/24', '0025904EB5A5')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2080C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2081C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2082C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2083C')
        switch._add_server_port('ethernet/1/24', 'CEA9ACD2084C')

        cmdb_importer = GenericCmdbImporter()

        sw = Switch.objects.create(label="switch")
        cmdb_importer.import_switch(sw.id, switch)

        self.assertEqual(1, len(SwitchPort.active.filter()))
        self.assertEqual(1, len(SwitchPort.active.filter(status=Resource.STATUS_INUSE)))

        self.assertEqual(2, len(Server.active.filter()))
        self.assertEqual(5, len(VirtualServer.active.filter()))
        self.assertEqual(5, len(VirtualServer.active.filter(parent=None)))
        self.assertEqual(2, len(ServerPort.active.filter()))
        self.assertEqual(2, len(ServerPort.active.filter(status=Resource.STATUS_INUSE)))
        self.assertEqual(0, len(ServerPort.active.filter(parent=None)))
        self.assertEqual(5, len(VirtualServerPort.active.filter()))
        self.assertEqual(5, len(VirtualServerPort.active.filter(status=Resource.STATUS_INUSE)))
        self.assertEqual(0, len(VirtualServerPort.active.filter(parent=None)))
        self.assertEqual(7, len(PortConnection.active.filter()))

    def test_create_with_id(self):
        new_server = Server.objects.create(label="test server", id=103)
        new_server.refresh_from_db()

        self.assertEqual(103, new_server.id)
