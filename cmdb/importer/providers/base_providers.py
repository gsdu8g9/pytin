import netaddr


class MacTable(object):
    def __init__(self):
        pass

    def __iter__(self):
        raise NotImplemented()


class ArpTable(object):
    def __init__(self):
        pass

    def __iter__(self):
        raise NotImplemented()

class MacTableRecord(object):
    def __init__(self, mac, port):
        self._mac = netaddr.EUI(mac, dialect=netaddr.mac_bare)
        self._port = port

    @property
    def mac(self):
        return str(self._mac)

    @property
    def port(self):
        return self._port

    @property
    def vendor(self):
        try:
            return self._mac.oui.registration().org
        except netaddr.NotRegisteredError:
            return None

class ArpTableRecord(MacTableRecord):
    def __init__(self, ip, mac, port):
        self._ip = ip
        self._mac = netaddr.EUI(mac, dialect=netaddr.mac_bare)
        self._port = port

    @property
    def ip(self):
        return self._ip
