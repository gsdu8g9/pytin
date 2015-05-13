import ipaddress

from resources.models import Resource


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


class IPAddressPool(Resource):
    class Meta:
        proxy = True

    def __str__(self):
        return self.name

    def __iter__(self):
        """
        Iterates by all related IP addresses.
        """
        for ipaddr in IPAddress.objects.active(parent=self):
            yield ipaddr

    @property
    def version(self):
        return self.get_option_value('version')

    @property
    def usage(self):
        return self.get_usage()

    @property
    def total_addresses(self):
        return IPAddress.objects.active(parent=self).count()

    @property
    def used_addresses(self):
        return IPAddress.objects.active(parent=self, status=Resource.STATUS_INUSE).count()

    def get_usage(self):
        total = float(self.total_addresses)
        used = float(self.used_addresses)

        return int(round((float(used) / total) * 100))

    def browse(self):
        """
        Iterate through all IP in this pool, even that are not allocated.
        """
        for addr in self.available():
            yield addr.address

    def available(self):
        """
        Iterate through available resources in the pool. Override this method in resource specific pools.
        """
        for res in IPAddress.objects.active(parent=self, status=Resource.STATUS_FREE):
            yield res


class IPAddressRangePool(IPAddressPool):
    class Meta:
        proxy = True

    def __str__(self):
        return "%s-%s" % (self.range_from, self.range_to)

    @property
    def range_from(self):
        return self.get_option_value('range_from', default=None)

    @range_from.setter
    def range_from(self, ipaddr):
        assert ipaddr is not None, "Parameter 'ipaddr' must be defined."

        parsed_address = ipaddress.ip_address(unicode(ipaddr))
        self.set_option('range_from', parsed_address)
        self.set_option('version', parsed_address.version)

    @property
    def range_to(self):
        return self.get_option_value('range_to', default=None)

    @range_to.setter
    def range_to(self, ipaddr):
        assert ipaddr is not None, "Parameter 'ipaddr' must be defined."

        parsed_address = ipaddress.ip_address(unicode(ipaddr))
        self.set_option('range_to', parsed_address)
        self.set_option('version', parsed_address.version)

    @property
    def total_addresses(self):
        ip_from = int(ipaddress.ip_address(unicode(self.range_from)))
        ip_to = int(ipaddress.ip_address(unicode(self.range_to)))

        return ip_to - ip_from + 1

    def can_add(self, address):
        """
        Test if IP address is from this network.
        """
        assert address is not None, "Parameter 'address' must be defined."

        parsed_addr = ipaddress.ip_address(unicode(address.address if isinstance(address, IPAddress) else address))

        for ipnet in [self._get_range_addresses()]:
            if parsed_addr in ipnet:
                return True

        return False

    def browse(self):
        """
        Iterate through all IP in this pool, even that are not allocated.
        """
        for address in self._get_range_addresses():
            yield address

    def available(self):
        """
        Check availability of the specific IP and return IPAddress that can be used.
        """
        for address in self.browse():
            ips = IPAddress.objects.active(address=address, parent=self)
            if len(ips) > 0:
                if ips[0].is_free:
                    yield ips[0]
                else:
                    continue
            else:
                yield IPAddress.create(address=address, parent=self)

    def _get_range_addresses(self):
        ip_from = int(ipaddress.ip_address(unicode(self.range_from)))
        ip_to = int(ipaddress.ip_address(unicode(self.range_to)))

        assert ip_from < ip_to, "Property 'range_from' must be less than 'range_to'"

        for addr in range(ip_from, ip_to + 1):
            yield ipaddress.ip_address(addr)


class IPNetworkPool(IPAddressPool):
    """
    IP addresses network.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.network

    @property
    def network(self):
        return self.get_option_value('network', default=None)

    @network.setter
    def network(self, network):
        assert network is not None, "Parameter 'network' must be defined."

        parsed_net = ipaddress.ip_network(unicode(network), strict=False)
        self.set_option('network', parsed_net)
        self.set_option('version', parsed_net.version)

        # populate network parameters
        self.set_option('netmask', parsed_net.netmask)
        self.set_option('prefixlen', parsed_net.prefixlen)
        self.set_option('gateway', str(parsed_net[1]) if parsed_net.num_addresses > 0 else '')

    @property
    def total_addresses(self):
        return self._get_network_object().num_addresses

    def can_add(self, address):
        """
        Test if IP address can be added to this pool.
        """
        assert address is not None, "Parameter 'address' must be defined."

        parsed_addr = ipaddress.ip_address(unicode(address.address if isinstance(address, IPAddress) else address))
        parsed_net = self._get_network_object()

        return parsed_addr in parsed_net

    def browse(self):
        """
        Iterate through all IP in this pool, even that are not allocated.
        """
        parsed_net = self._get_network_object()
        for address in parsed_net.hosts():
            yield address

    def available(self):
        """
        Check availability of the specific IP and return IPAddress that can be used.
        """
        for address in self.browse():
            ips = IPAddress.objects.active(address=address, parent=self)
            if len(ips) > 0:
                if ips[0].is_free:
                    yield ips[0]
                else:
                    continue
            else:
                yield IPAddress.create(address=address, parent=self)

    def _get_network_object(self):
        return ipaddress.ip_network(unicode(self.network), strict=False)
