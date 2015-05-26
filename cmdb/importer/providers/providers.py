import netaddr
from resources.models import Resource


class MacTable(object):
    def __init__(self):
        pass

    def __iter__(self):
        raise NotImplemented()


class ArpTable(MacTable):
    def __iter__(self):
        raise NotImplemented()


class MacTableRecord(object):
    def __init__(self, mac, port, source_device_id):
        self._mac = netaddr.EUI(mac, dialect=netaddr.mac_bare)
        self._port = port
        self._source_device = Resource.objects.get(pk=source_device_id)

    @property
    def source_device_id(self):
        return self._source_device.id

    @property
    def mac(self):
        return str(self._mac).upper()

    @property
    def port(self):
        return self._port

    @property
    def vendor(self):
        try:
            return self._mac.oui.registration().org
        except netaddr.NotRegisteredError:
            return None

    def import_record(self, importer):
        assert importer, "importer must be defined"

        importer.add_arp_record(self._source_device, self)


class ArpTableRecord(MacTableRecord):
    def __init__(self, ip, mac, port, source_device_id):
        super(ArpTableRecord, self).__init__(mac, port, source_device_id)
        self._ip = ip

    @property
    def ip(self):
        return self._ip

    def import_record(self, importer):
        assert importer, "importer must be defined"

        importer.add_mac_record(self._source_device, self)
