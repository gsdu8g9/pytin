from __future__ import unicode_literals

import ipaddress

from resources.models import Resource, ResourceOption


class IPAddress(Resource):
    """
    IP address
    Note: IPAddress is added to the IP pool with ipman_pool_id option. This option allows to organize Resources and
          keep tracking of IP-IP_pool relations.
    """

    class Meta:
        proxy = True

    @staticmethod
    def is_valid_address(address):
        try:
            ipaddress.ip_address(unicode(address))
        except:
            return False

        return True

    def __str__(self):
        return self.address

    def _get_beauty(self, address):
        assert address, "address must be defined."
        """
        Count beauty factor: 1 - 10
        """
        diff_map = {}
        for ch in address:
            diff_map[ch] = 1

        return (12 if self.version == 4 else 17) - len(diff_map)

    @property
    def address(self):
        return unicode(self.get_option_value('address'))

    @address.setter
    def address(self, address):
        assert address is not None, "Parameter 'address' must be defined."

        parsed_addr = ipaddress.ip_address(unicode(address))
        self.set_option('address', parsed_addr)
        self.set_option('version', parsed_addr.version)
        self.set_option('beauty', self._get_beauty(unicode(address)), format=ResourceOption.FORMAT_INT)

    @property
    def version(self):
        return self.get_option_value('version')

    @property
    def beauty(self):
        return self.get_option_value('beauty', default=self._get_beauty(self.address))

    def delete(self, cascade=False, purge=False):
        """
        Override delete: free instead of delete
        """
        if purge:
            self.delete(cascade=cascade, purge=purge)
        else:
            self.parent_id = self.get_option_value('ipman_pool_id')
            self.free()
            self.save()

            # delete related objects
            for child in self:
                child.delete(cascade=cascade, purge=purge)

    def save(self, *args, **kwargs):
        need_save = True

        if not self.is_saved():
            if self.parent and not isinstance(self.parent, IPAddressPool):
                raise Exception("IP address must be added to the pool for the first time.")

            super(IPAddress, self).save(*args, **kwargs)
            need_save = False

        if self.parent and isinstance(self.parent, IPAddressPool):
            self.set_option('ipman_pool_id', self.parent.id)

        if need_save:
            super(IPAddress, self).save(*args, **kwargs)


class IPAddressPool(Resource):
    ip_pool_types = [
        'IPAddressPool',
        'IPAddressRangePool',
        'IPNetworkPool'
    ]

    class InfiniteList:
        """
        Implementation of the ring buffer. Infinitely iterate through the given list.
        """

        def __init__(self, list):
            if not list:
                raise ValueError('list')

            self.list = list

        def __iter__(self):
            idx = 0
            while True:
                yield self.list[idx % len(self.list)]
                idx += 1

    class Meta:
        proxy = True

    def __str__(self):
        return self.name

    @staticmethod
    def globally_available(ip_pool_ids, count=1):
        """
        Returns given number of IPs from different IP address pools.
        """

        assert ip_pool_ids
        assert count > 0

        rented_ips = []
        for ip_pool_id in IPAddressPool.InfiniteList(ip_pool_ids):
            if len(rented_ips) >= count:
                break

            ip_pool_resource = Resource.objects.get(pk=ip_pool_id)

            ip = ip_pool_resource.available().next()
            ip.lock()

            rented_ips.append(ip)

        return rented_ips

    @staticmethod
    def is_valid_network(network):
        try:
            ipaddress.ip_network(unicode(network), strict=False)
        except:
            return False

        return True

    @staticmethod
    def get_all_pools():
        return Resource.objects.active(type__in=IPAddressPool.ip_pool_types)

    @property
    def version(self):
        return self.get_option_value('version')

    @property
    def usage(self):
        return self.get_usage()

    @property
    def total_addresses(self):
        return IPAddress.objects.active(ipman_pool_id=self.id).count()

    @property
    def used_addresses(self):
        return IPAddress.objects.active(ipman_pool_id=self.id, status=Resource.STATUS_INUSE).count()

    def delete(self, cascade=False, purge=False):
        """
        Override: delete allocated and other non deleted IPs from this Pool
        """
        # delete all related objects
        super(IPAddressPool, self).delete(cascade=True)

        # delete allocated IPs
        IPAddress.objects.active(ipman_pool_id=self.id).delete()

    def get_usage(self):
        total = float(self.total_addresses)
        used = float(self.used_addresses)

        return int(round((float(used) / total) * 100))

    def browse(self):
        """
        Iterate through all IP in this pool, even that are not allocated.
        """
        for addr in IPAddress.objects.active(ipman_pool_id=self.id, status=Resource.STATUS_FREE):
            yield addr.address

    def available(self):
        """
        Check availability of the specific IP and return IPAddress that can be used.
        """
        for address in self.browse():
            # search in the current pool
            ips = IPAddress.objects.active(address=address, ipman_pool_id=self.id)
            if len(ips) > 0:
                for ip in ips:
                    if ip.is_free:
                        yield ip
                    else:
                        continue
            else:
                # guarantee the uniq IPs, search in other pools
                existing_ips = IPAddress.objects.active(address=address)
                if len(existing_ips) <= 0:
                    yield IPAddress.objects.create(address=address, parent=self)
                else:
                    # IP from this pool is used elsewhere
                    continue


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
        return self.get_option_value('network', default='0.0.0.0/0')

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

    def _get_network_object(self):
        return ipaddress.ip_network(unicode(self.network), strict=False)
