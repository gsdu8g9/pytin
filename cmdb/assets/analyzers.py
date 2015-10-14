from __future__ import unicode_literals
from assets.models import SwitchPort, ServerPort, VirtualServerPort


class CmdbAnalyzer(object):
    @staticmethod
    def guess_hypervisor(switch_port):
        """
        Check if there is one physical and many VPS servers on the switch port.
        :param switch_port: Port of the Switch to analyze connections.
        :param dry_run: If True, then role is set for guessed hypervisor (when 1 physical + many VMs).
        :return: (result, physical servers, virtual servers)
                result: True - if hypervisor is found
                if True:
                    physical server - found hypervisor
                    virtual servers - found virtual servers
                if False:
                    physical servers - found physical servers, or []
                    virtual servers - found virtual servers, or []
        """
        assert switch_port
        assert isinstance(switch_port, SwitchPort)

        pysical_srv = []
        virtual_srv = []

        for connection in switch_port.connections:
            if isinstance(connection.linked_port, ServerPort):
                pysical_srv.append(connection.linked_port.device)
            elif isinstance(connection.linked_port, VirtualServerPort):
                virtual_srv.append(connection.linked_port.device)

        if len(pysical_srv) > 0:
            if len(pysical_srv) == 1 and len(virtual_srv) > 0:
                return True, pysical_srv[0], virtual_srv
            elif len(pysical_srv) > 1 and len(virtual_srv) > 0:
                hvisors = [server for server in pysical_srv if server.get_option_value('role') == 'hypervisor']
                if len(hvisors) == 1:
                    return True, hvisors[0], virtual_srv
                else:
                    return False, pysical_srv, virtual_srv

        return False, [], []
