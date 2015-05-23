import os
import re

from pysnmp.entity.rfc3413.oneliner import cmdgen

from importer.providers.base_providers import ArpTable, ArpTableRecord, MacTableRecord, MacTable


def _snmp_walk(self, oid):
    cmdGen = cmdgen.CommandGenerator()

    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData(self.community),
        cmdgen.UdpTransportTarget((self.host, 161)),
        oid
    )

    if errorIndication:
        print(errorIndication)
    else:
        if errorStatus:
            raise Exception('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBindTable[-1][int(errorIndex) - 1] or '?'))
        else:
            for varBindTableRow in varBindTable:
                for name, val in varBindTableRow:
                    yield name.prettyPrint(), val.prettyPrint()


class QSW8300MacTableSnmp(MacTable):
    def __init__(self, device_id, host, community):
        assert host, "host must be defined."
        assert device_id, "device_id must be defined."
        assert community, "community must be defined."

        self.device_id = device_id
        self.host = host
        self.community = community
        self.mac_port_map = None

    def __iter__(self):
        if not self.mac_port_map:
            port_name_map = {}
            oid = '.1.3.6.1.2.1.31.1.1.1.1'
            for name, value in _snmp_walk(oid):
                port_name_map[name[len(oid):]] = value

            mac_port_map = {}
            oid = '.1.3.6.1.2.1.17.7.1.2.2.1.2'
            for name, value in _snmp_walk(oid):
                name_parts = name.split('.')
                mac_address = "".join(
                    [("%02x" % int(name_parts[x])).upper() for x in
                     range(len(name_parts) - 6, len(name_parts))]).upper()
                mac_port_map[mac_address] = value

        for mac_addr in mac_port_map:
            yield MacTableRecord(source_device_id=self.device_id,
                                 mac=mac_addr,
                                 port=mac_port_map[mac_addr])


class QSW8300ArpTableSnmp(ArpTable):
    arp_table = None

    def __init__(self, device_id, host, community):
        assert host, "host must be defined."
        assert device_id, "device_id must be defined."
        assert community, "community must be defined."

        self.device_id = device_id
        self.host = host
        self.community = community

    def __iter__(self):
        if not self.arp_table:
            port_name_map = {}
            oid = '.1.3.6.1.2.1.31.1.1.1.1'
            for name, value in _snmp_walk(oid):
                port_name_map[name[len(oid):]] = value

            ip_mac_map = {}
            oid = '.1.3.6.1.2.1.4.22.1.2'
            for name, value in _snmp_walk(oid):
                name_parts = name.split('.')
                ip_address = ".".join([name_parts[x] for x in range(len(name_parts) - 4, len(name_parts))])
                ip_mac_map[ip_address] = value[2:].upper()

            mac_port_map = {}
            oid = '.1.3.6.1.2.1.17.7.1.2.2.1.2'
            for name, value in _snmp_walk(oid):
                name_parts = name.split('.')
                mac_address = "".join(
                    [("%02x" % int(name_parts[x])).upper() for x in
                     range(len(name_parts) - 6, len(name_parts))]).upper()
                mac_port_map[mac_address] = value

            self.arp_table = []
            for ip_addr in ip_mac_map:
                mac_addr = ip_mac_map[ip_addr]

                if mac_addr in mac_port_map:
                    port_number = mac_port_map[mac_addr]
                else:
                    print "ERROR: MAC address %s is missing from mac_port_map." % mac_addr
                    continue

                if port_number in port_name_map:
                    port_name = port_name_map[port_number]
                else:
                    print "ERROR: Port number %s is missing from port_name_map." % port_number
                    continue

                self.arp_table.append(dict(ip=ip_addr, mac=mac_addr, port_name=port_name, port_num=port_number))

        for arp_rec in self.arp_table:
            yield ArpTableRecord(source_device_id=self.device_id,
                                 ip=arp_rec['ip'],
                                 mac=arp_rec['mac'],
                                 port=arp_rec['port_num'])


class QSW8300ArpTableFileDump(ArpTable):
    def __init__(self, file_path, device_id):
        assert device_id, "device_id must be defined."
        assert file_path, "file_path must be defined."
        assert os.path.exists(file_path), "file_path must exist."

        self.device_id = device_id
        self.file_path = file_path
        # 46.17.40.36	00-15-17-9e-6f-3c	Vlan1	Ethernet1/0/20	Dynamic	56	1
        self.regexp = re.compile(r'(\d+\.\d+\.\d+\.\d+)\s+([^\s]+)\s+[^\s]+\s+((.+/.+/(\d+))|([^\s]+))', re.IGNORECASE)

    def __iter__(self):
        for arp_line in file(self.file_path):
            arp_record = self._parse_arp_line(arp_line)
            if arp_record:
                yield arp_record

    def _parse_arp_line(self, arp_line):
        assert arp_line, "arp_line must be defined"

        match_obj = self.regexp.match(arp_line)
        if match_obj:
            port_num = match_obj.group(5)

            # group(5) is port number (ex: 20 from Ethernet1/0/20)
            # group(6) is a port channel
            return ArpTableRecord(source_device_id=self.device_id,
                                  ip=match_obj.group(1),
                                  mac=match_obj.group(2),
                                  port=int(port_num) if port_num else match_obj.group(6))

        return None


class QSW8300MacTableFileDump(MacTable):
    def __init__(self, file_path, device_id):
        assert device_id, "device_id must be defined."
        assert file_path, "file_path must be defined."
        assert os.path.exists(file_path), "file_path must exist."

        self.device_id = device_id
        self.file_path = file_path
        # 1	00-30-48-de-3a-b6	DYNAMIC	Hardware	Port-Channel2
        # 1	00-30-48-de-3a-b6	DYNAMIC	Hardware	Ethernet1/0/20
        self.regexp = re.compile(r'\d+\s+([^\s]+)\s+[^\s]+\s+[^\s]+\s+((.+/.+/(\d+))|([^\s]+))')

    def __iter__(self):
        for mac_line in file(self.file_path):
            mac_record = self._parse_mac_line(mac_line)
            if mac_record:
                yield mac_record

    def _parse_mac_line(self, mac_line):
        assert mac_line, "mac_line must be defined"

        match_obj = self.regexp.match(mac_line)
        if match_obj:
            port_num = match_obj.group(4)
            return MacTableRecord(source_device_id=self.device_id,
                                  mac=match_obj.group(1),
                                  port=int(port_num) if port_num else match_obj.group(5))

        return None
