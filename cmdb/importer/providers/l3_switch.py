import netaddr
from pysnmp.entity.rfc3413.oneliner import cmdgen
from cmdb.settings import logger


def _snmp_walk(host, community, oid):
    assert host, "host must be defined."
    assert community, "community must be defined."
    assert oid, "oid must be defined."

    cmdGen = cmdgen.CommandGenerator()

    errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
        cmdgen.CommunityData(community),
        cmdgen.UdpTransportTarget((host, 161)),
        oid,
        ignoreNonIncreasingOid=True
    )

    if errorIndication:
        logger.error(errorIndication)
    else:
        if errorStatus:
            raise Exception('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBindTable[-1][int(errorIndex) - 1] or '?'))
        else:
            for varBindTableRow in varBindTable:
                for name, val in varBindTableRow:
                    yield name.prettyPrint(), val.prettyPrint()


def _normalize_mac(mac_address):
    assert mac_address
    return str(netaddr.EUI(mac_address, dialect=netaddr.mac_bare)).upper()


def _normalize_port_name(port_name):
    assert port_name
    return port_name.lower()


class ServerInterface(object):
    """
    Server interface, connected to the switch
    """

    def __init__(self, mac):
        assert mac

        self._mac = netaddr.EUI(mac, dialect=netaddr.mac_bare)

    def __str__(self):
        return self.interface

    @property
    def interface(self):
        return _normalize_mac(str(self._mac))

    @property
    def vendor(self):
        try:
            return self._mac.oui.registration().org
        except netaddr.NotRegisteredError:
            return None


class L3SwitchPort(object):
    """
    Level3 switch port
    """

    def __init__(self, switch, port_name, port_num, macs=[]):
        assert port_name
        assert switch

        self._switch = switch
        self._port_name = _normalize_port_name(port_name)
        self._port_num = port_num
        self._macs = [ServerInterface(mac_addr) for mac_addr in macs]

    @property
    def switch(self):
        return self._switch

    @property
    def name(self):
        return self._port_name

    @property
    def number(self):
        return self._port_num

    @property
    def is_local(self):
        return self._port_name.startswith('ethernet')

    @property
    def macs(self):
        return self._macs


class L3Switch(object):
    """
    Layer 3 switch object
    """

    port_implementor = L3SwitchPort

    def __init__(self):
        self.port_name__num__map = {}
        self.port_name__macs__map = {}
        self.mac__port_name__map = {}
        self.server_port__ips__map = {}

    @property
    def ports(self):
        """
        Returns the switch ports
        :return: L3SwitchPort array
        """
        for port_name in self.port_name__num__map:
            port_num = self.port_name__num__map[port_name]

            macs = []
            if port_name in self.port_name__macs__map:
                macs = self.port_name__macs__map[port_name]

            port_object = self.port_implementor(self, port_name, port_num, macs)

            yield port_object

    def get_mac_ips(self, mac_address):
        mac_address = _normalize_mac(mac_address)
        if mac_address in self.server_port__ips__map:
            return self.server_port__ips__map[mac_address]

        return []

    def from_mac_dump(self, file_name):
        raise NotImplementedError()

    def from_arp_dump(self, file_name):
        raise NotImplementedError()

    def from_snmp(self, host, community):
        assert host
        assert community

        # switch port names and numbers
        oid = '.1.3.6.1.2.1.31.1.1.1.1'
        for name, value in _snmp_walk(host, community, oid):
            self._add_switch_port(name[len(oid):], value)

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

    def get_port_name(self, number):
        assert number > 0

        for port_name in self.port_name__num__map:
            if self.port_name__num__map[port_name] == number:
                return port_name

        return number

    def _add_switch_port(self, port_number, port_name):
        assert port_name

        port_name = _normalize_port_name(port_name)
        if port_name not in self.port_name__num__map:
            self.port_name__num__map[port_name] = port_number

    def _add_server_port(self, switch_port_name, server_port_mac):
        assert switch_port_name
        assert server_port_mac

        server_port_mac = _normalize_mac(server_port_mac)
        switch_port_name = _normalize_port_name(switch_port_name)

        self.mac__port_name__map[server_port_mac] = switch_port_name

        if switch_port_name not in self.port_name__macs__map:
            self.port_name__macs__map[switch_port_name] = []

        if server_port_mac not in self.port_name__macs__map[switch_port_name]:
            self.port_name__macs__map[switch_port_name].append(server_port_mac)

    def _add_server_port_ip(self, server_port_mac, ip_address):
        assert server_port_mac
        assert ip_address

        server_port_mac = _normalize_mac(server_port_mac)

        if server_port_mac not in self.server_port__ips__map:
            self.server_port__ips__map[server_port_mac] = []

        if ip_address not in self.server_port__ips__map[server_port_mac]:
            self.server_port__ips__map[server_port_mac].append(ip_address)
