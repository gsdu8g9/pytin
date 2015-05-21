import os
import re

from importer.providers.base_providers import ArpTable, ArpTableRecord, MacTableRecord, MacTable


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
