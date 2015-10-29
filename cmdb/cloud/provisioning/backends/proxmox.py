from __future__ import unicode_literals

from cloud.provisioning import Hypervisor


class ProxMoxJBONServiceBackend(Hypervisor):
    """
    Cloud Service: Just bunch of ProxMox nodes.
    """

    # TODO: This config should be loaded from config file (not from DB).
    # Each node have CMDB representation. Also we get 'rating' and 'heartbeat' from CMDB.
    # Each node must have pytin-agent-hv installed.
    NODES = {
        62: {
            'hostname': 'cn11.justhost.ru',
            'types': ['kvm']
        },
        130: {
            'hostname': 'cn12.justhost.ru',
            'types': ['openvz']
        }
    }

    def request(self, vps_request_options):
        # we can create KVM, OpenVZ and other virtuals - it's the mater of selected script hook on the node.
        pass
