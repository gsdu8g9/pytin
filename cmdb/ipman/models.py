import ipaddress

from resources.models import Resource


VERSION_IPV4 = 4
VERSION_IPV6 = 6


class IPAddress(Resource):
    """
    IP address
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.address

    @property
    def address(self):
        return unicode(self.get_option_value('address'))

    @address.setter
    def address(self, address):
        assert address is not None, "Parameter 'address' must be defined."

        parsed_addr = ipaddress.ip_address(unicode(address))
        self.set_option('address', parsed_addr)
        self.set_option('version', parsed_addr.version)

    @property
    def version(self):
        return self.get_option_value('version')


class IPNetwork(Resource):
    """
    IP addresses network.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.network

    def __contains__(self, item):
        assert isinstance(item, IPAddress), "Item must be the instance of IPAddress"

        parsed_net = self._get_network_object()
        parsed_addr = ipaddress.ip_address(unicode(item.address))

        return parsed_addr in parsed_net

    def _get_network_object(self):
        return ipaddress.ip_network(unicode(self.network), strict=False)

    @property
    def network(self):
        return self.get_option_value('network', default=None)

    @network.setter
    def network(self, network):
        assert network is not None, "Parameter 'network' must be defined."

        parsed_net = ipaddress.ip_network(unicode(network), strict=False)
        self.set_option('network', parsed_net)
        self.set_option('version', parsed_net.version)

    @property
    def version(self):
        return self.get_option_value('version')

    def owns(self, address):
        """
        Test if IP address is from this network.
        """
        assert address is not None, "Parameter 'address' must be defined."

        parsed_addr = ipaddress.ip_address(unicode(address))
        parsed_net = ipaddress.ip_network(unicode(self.network))

        return parsed_addr in parsed_net

    def next_usable(self):
        """
        Check availability of the specific IP and return IPAddress that can be used.
        """
        parsed_net = ipaddress.ip_network(unicode(self.network), strict=False)
        for address in parsed_net.hosts():
            ips = IPAddress.objects.active(address=address)
            if len(ips) > 0:
                if ips[0].is_free:
                    return ips[0]
                else:
                    continue
            else:
                return IPAddress.create(address=address)
