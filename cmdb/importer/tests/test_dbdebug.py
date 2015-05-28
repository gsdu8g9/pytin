import os
from unittest import TestCase

from assets.models import SwitchPort, PortConnection


class CMDBDebug(TestCase):
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    def test_detect_uplinks(self):
        for switch in SwitchPort.objects.active():
            connections = PortConnection.objects.active(parent=switch)

