from __future__ import unicode_literals
import os
import re

from importer.providers.l3_switch import L3Switch, L3SwitchPort


class QtechL3SwitchPort(L3SwitchPort):
    @property
    def is_local(self):
        return self._port_name.startswith('ethernet')


class QtechL3Switch(L3Switch):
    port_implementor = QtechL3SwitchPort
    mac_regexp = r'\d+\s+([^\s]+)\s+[^\s]+\s+[^\s]+\s+((.+/.+/(\d+))|([^\s]+))'
    arp_regexp = r'(\d+\.\d+\.\d+\.\d+)\s+([^\s]+)\s+[^\s]+\s+((.+/.+/(\d+))|([^\s]+))'

    def from_mac_dump(self, file_name):
        assert file_name, "file_path must be defined."
        assert os.path.exists(file_name), "file_path must exist."

        # 1	00-30-48-de-3a-b6	DYNAMIC	Hardware	Port-Channel2
        # 1	00-30-48-de-3a-b6	DYNAMIC	Hardware	Ethernet1/0/20
        regexp = re.compile(self.mac_regexp, re.IGNORECASE)

        for mac_line in file(file_name):
            match_obj = regexp.match(mac_line)
            if match_obj:
                port_num = match_obj.group(4)

                switch_port_number = int(port_num) if port_num else None
                switch_port_name = match_obj.group(2)

                self._add_switch_port(switch_port_number, switch_port_name)
                self._add_server_port(switch_port_name, server_port_mac=match_obj.group(1))

    def from_arp_dump(self, file_name):
        assert file_name, "file_path must be defined."
        assert os.path.exists(file_name), "file_path must exist."

        # 46.17.40.36	00-15-17-9e-6f-3c	Vlan1	Ethernet1/0/20	Dynamic	56	1
        regexp = re.compile(self.arp_regexp, re.IGNORECASE)

        for arp_line in file(file_name):
            match_obj = regexp.match(arp_line)

            if match_obj:
                port_num = match_obj.group(5)

                switch_port_number = int(port_num) if port_num else None
                switch_port_name = match_obj.group(3)

                self._add_switch_port(switch_port_number, switch_port_name)
                self._add_server_port(switch_port_name, server_port_mac=match_obj.group(2))
                self._add_server_port_ip(server_port_mac=match_obj.group(2), ip_address=match_obj.group(1))


class Qtech3400Switch(QtechL3Switch):
    mac_regexp = r'\d+\s+([^\s]+)\s+[^\s]+\s+[^\s]+\s+((.+/(\d+))|([^\s]+))'
