from __future__ import unicode_literals

import ipaddress
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from assets.models import Datacenter
from resources.models import Resource, ResourceOption


@python_2_unicode_compatible
class IPAddressGeneric(models.Model):
    HISTORY_FIELDS = ['pool_id', 'parent_id', 'address', 'status']

    pool = models.ForeignKey(Resource)
    parent = models.ForeignKey(Resource, null=True, blank=True, related_name='ipaddress')

    address = models.GenericIPAddressField("IPv4/v6 address", db_index=True, unique=True)
    status = models.CharField(max_length=25,
                              db_index=True,
                              choices=Resource.STATUS_CHOICES,
                              default=Resource.STATUS_FREE)

    version = models.IntegerField("IP address version", db_index=True, default=0)

    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)
    last_seen = models.DateTimeField('Date last seen', db_index=True, default=timezone.now)
    main = models.BooleanField("Main IP of the device", db_index=True, default=False)

    def __str__(self):
        return "%s" % self.address

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.version:
            ip = ipaddress.ip_address(self.address)
            self.version = ip.version

        return super(IPAddressGeneric, self).save(force_insert, force_update, using, update_fields)

    def free(self):
        """
        Free this IP.
        """
        self.set_status(Resource.STATUS_FREE)

    def use(self, parent=None):
        """
        Use this IP.
        """
        self.set_status(Resource.STATUS_INUSE, parent)

    def lock(self, parent=None):
        """
        Use this IP.
        """
        self.set_status(Resource.STATUS_LOCKED, parent)

    def release(self):
        """
        Release IP address from the parent and move to initial IP pool.
        """
        self.free()

        if self.parent:
            self.parent = None
            self.save()

    def assign_to_resource(self, parent):
        assert parent
        assert isinstance(parent, Resource)

        self.parent = parent
        self.save()

    def touch(self):
        """
        Update last_seen date of the resource
        """
        self.last_seen = timezone.now()
        self.save()

    def move_to_pool(self, target_pool):
        assert target_pool
        assert isinstance(target_pool, Resource), "target_pool must be of Resource type"

        if not self.pool or self.pool.id != target_pool.id:
            self.pool = target_pool
            self.save()

            return True

        return False

    def set_status(self, status, parent=None):
        assert status

        changed = False

        if parent:
            if not self.parent or (self.parent and parent.id != self.parent.id):
                self.parent = parent
                changed = True

        if self.status != status:
            self.status = status
            changed = True

        if changed:
            self.save()


class IPAddressPoolGeneric(Resource):
    class Meta:
        proxy = True

    @property
    def usage(self):
        total = float(self.total_addresses)
        used = float(self.used_addresses)

        usage_value = int(round((float(used) / total) * 100)) if total > 0 else 0

        self.set_option('ipman_usage', usage_value, ResourceOption.FORMAT_INT)

        return usage_value

    @property
    def total_addresses(self):
        return self.get_ips().count()

    @property
    def used_addresses(self):
        return self.get_used_ips().count()

    @property
    def version(self):
        return self.get_option_value('version', default=4)

    def get_used_ips(self):
        return self.get_ips().exclude(status=Resource.STATUS_FREE)

    def get_free_ips(self, **query):
        return self.get_ips(status=Resource.STATUS_FREE, **query)

    def get_ips(self, **query):
        return IPAddressGeneric.objects.filter(pool=self, **query)

    def add_ip(self, address):
        """
        Add IP address to the IP pool.
        """
        assert address

        if not isinstance(address, IPAddressGeneric):
            address, create = IPAddressGeneric.objects.update_or_create(
                address=address,
                defaults=dict(pool=self))

        return address


class IPAddressRenter(object):
    def __init__(self):
        self.sources = []

    def add_source(self, ip_pool):
        assert ip_pool
        assert isinstance(ip_pool, IPAddressPoolGeneric)

        self.sources.append(ip_pool)

    @staticmethod
    def from_pools(pools):
        assert pools, "IP pools are not available."

        renter = IPAddressRenter()
        for pool in pools:
            renter.add_source(pool)

        return renter

    @staticmethod
    def from_datacenter(datacenter, ip_version=4):
        """
        Create IP renter from available pools in Datacenter.
        :param ip_version: Specify version of the IP.
        :param datacenter: Where to lease IPs.
        :return: Rented IPs or ValueError.
        """
        assert datacenter
        assert isinstance(datacenter, Datacenter)

        free_ippools = datacenter.filter_childs(IPAddressPoolGeneric,
                                                status=Resource.STATUS_FREE,
                                                version=ip_version)

        return IPAddressRenter.from_pools(free_ippools)

    def rent(self, count=1):
        """
        Rent Count IPs from available pools.
        :param count: Number of IPs to rent.
        :return: Locked IPs, that can be used.
        """
        assert len(self.sources) > 0, "Add IP pools"

        result_ips = []
        while len(result_ips) < count:
            last_len = len(result_ips)

            for pool in self.sources:
                if len(result_ips) >= count:
                    break

                for ip in pool.get_free_ips().order_by('last_seen')[:1]:
                    ip.lock()
                    ip.touch()
                    result_ips.append(ip)

            if last_len == len(result_ips):
                raise ValueError("Can't rent %s IPs" % count)

        return result_ips


class IPAddressPoolFactory(object):
    MAX_POOL_SIZE = 1024

    @staticmethod
    def from_name(name, **options):
        assert name

        pool, created = IPAddressPoolGeneric.objects.update_or_create(name=name, defaults=options)

        return pool

    @staticmethod
    def from_network(network, **options):
        assert network

        parsed_net = ipaddress.ip_network(network, strict=False)

        network_address = int(parsed_net.network_address)
        broadcast = int(parsed_net.broadcast_address)
        pool_size = broadcast - network_address

        if pool_size >= IPAddressPoolFactory.MAX_POOL_SIZE:
            raise ValueError("Pool size %s exceeds maximum size %s" % (pool_size, IPAddressPoolFactory.MAX_POOL_SIZE))

        pool, created = IPAddressPoolGeneric.objects.update_or_create(name=network, defaults=options)
        pool.set_option('netmask', parsed_net.netmask)
        pool.set_option('gateway', "%s" % (parsed_net.network_address + 1))
        pool.set_option('version', parsed_net.version)

        for address in parsed_net.hosts():
            IPAddressGeneric.objects.update_or_create(address="%s" % address, defaults=dict(pool=pool))

        return pool

    @staticmethod
    def from_range(range_from, range_to, **options):
        assert range_from
        assert range_to

        parsed_ip_from = ipaddress.ip_address(range_from)
        ip_from = int(parsed_ip_from)
        ip_to = int(ipaddress.ip_address(range_to))

        if ip_from > ip_to:
            raise ValueError("Property 'range_from' must be less than 'range_to'")

        pool_size = ip_to - ip_from
        if pool_size >= IPAddressPoolFactory.MAX_POOL_SIZE:
            raise ValueError("Pool size %s exceeds maximum size %s" % (pool_size, IPAddressPoolFactory.MAX_POOL_SIZE))

        pool, created = IPAddressPoolGeneric.objects.update_or_create(
            name="%s-%s" % (range_from, range_to),
            defaults=options
        )

        pool.set_option('version', parsed_ip_from.version)

        for address in range(ip_from, ip_to + 1):
            ipaddr = ipaddress.ip_address(address)
            IPAddressGeneric.objects.update_or_create(address="%s" % ipaddr, defaults=dict(pool=pool))

        return pool


class GlobalIPManager(object):
    @staticmethod
    def find_pools(datacenter=None, **query):
        if not datacenter:
            return IPAddressPoolGeneric.active.filter(**query)
        else:
            assert datacenter
            assert isinstance(datacenter, Datacenter)

            return datacenter.filter_childs(IPAddressPoolGeneric, **query)

    @staticmethod
    def find_ips(**query):
        return IPAddressGeneric.objects.filter(**query)

    @staticmethod
    def get_ip(ip_address):
        assert ip_address

        return IPAddressGeneric.objects.get(address__exact=ip_address)

    @staticmethod
    def move_ips(target_pool, start_ip, count=1, end_ip=None):
        assert target_pool
        assert isinstance(target_pool, Resource), "target_pool must be of Resource type"
        assert start_ip

        if not end_ip and not count:
            raise ValueError("end_ip or count must be defined.")

        moved_ips = []
        ip_from = int(ipaddress.ip_address("%s" % start_ip))
        ip_to = (ip_from + count) if count > 0 else (int(ipaddress.ip_address("%s" % end_ip)) + 1)
        for ip_raw in range(ip_from, ip_to):
            ipaddr = ipaddress.ip_address(ip_raw)
            ip_obj = GlobalIPManager.get_ip("%s" % ipaddr)

            if ip_obj.move_to_pool(target_pool):
                moved_ips.append(ip_obj)

        return moved_ips
