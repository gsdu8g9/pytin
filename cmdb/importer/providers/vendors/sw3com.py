from __future__ import unicode_literals
from cmdb.settings import logger
from importer.providers.l3_switch import L3Switch, _snmp_walk, L3SwitchPort


class Switch3Com2250Port(L3SwitchPort):
    @property
    def is_local(self):
        return self._port_name.startswith('ethernet') or \
               self._port_name.startswith('copper') or \
               self._port_name.startswith('fiber')


class Switch3Com2250(L3Switch):
    port_implementor = Switch3Com2250Port

    snmpid__port_num__map = {}  # port numbers are mapped: snmp id - real port number

    def from_snmp(self, host, community):
        assert host
        assert community

        # load port id map
        oid = '.1.3.6.1.2.1.17.1.4.1.2'
        for name, value in _snmp_walk(host, community, oid):
            self.snmpid__port_num__map[value] = name[len(oid):]

        # switch port names and numbers
        oid = '.1.3.6.1.2.1.31.1.1.1.1'
        for name, value in _snmp_walk(host, community, oid):
            snmp_port_id = name[len(oid):]
            if snmp_port_id in self.snmpid__port_num__map:
                real_port_number = self.snmpid__port_num__map[snmp_port_id]
                self._add_switch_port(real_port_number, value)
            else:
                logger.warning("There is no mapping for the SNMP port ID: %s" % snmp_port_id)

        # mac addresses table
        oid = '.1.3.6.1.2.1.17.7.1.2.2.1.2'
        for name, value in _snmp_walk(host, community, oid):
            name_parts = name.split('.')
            mac_address = "".join(
                [("%02x" % int(name_parts[x])).upper() for x in
                 range(len(name_parts) - 6, len(name_parts))]).upper()

            self._add_server_port(self.get_port_name(value), mac_address)

        # arp address table
        oid = '.1.3.6.1.2.1.4.22.1.2'
        for name, value in _snmp_walk(host, community, oid):
            name_parts = name.split('.')
            ip_address = ".".join([name_parts[x] for x in range(len(name_parts) - 4, len(name_parts))])
            self._add_server_port_ip(value[2:].upper(), ip_address)
