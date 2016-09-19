from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from assets.models import Server, Datacenter
from ipman.models import GlobalIPManager, IPAddressRenter


def generate_password(length=15):
    """
    Method used to generate passwords during provisioning processes.
    :param length:
    :return:
    """
    from random import choice

    charsets = [
        'abcdefghijklmnopqrstuvwxyz',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        '0123456789',
    ]

    pwd = []
    charset = choice(charsets)
    while len(pwd) < length:
        pwd.append(choice(charset))
        charset = choice(list(set(charsets) - {charset}))

    return "".join(pwd)


class CloudTask(object):
    def __init__(self, tracker, **context):
        assert tracker

        self.tracker = tracker
        self.context = context
        self.result = {}

    def execute(self):
        raise Exception(_("Not implemented."))

    def poll(self):
        """
        Async retrieve task status.
        :return:
        """
        raise Exception(_("Not implemented."))


class CloudBackend(object):
    """
    Specific Backend implementation. This is the factory for the service instances.
    """

    def __init__(self, cloud):
        assert cloud
        self.cloud = cloud
        self.task_tracker = cloud.task_tracker

    def send_task(self, cloud_task_class, **kwargs):
        """
        Submit task to the backend. Returns CloudTaskTracker.
        """
        assert cloud_task_class

        return self.task_tracker.execute(cloud_task_class, **kwargs)


class HypervisorBackend(CloudBackend):
    def __init__(self, cloud):
        super(HypervisorBackend, self).__init__(cloud)

    def create_vps(self, **options):
        raise Exception(_("Not implemented."))

    def start_vps(self, **options):
        raise Exception(_("Not implemented."))

    def stop_vps(self, **options):
        raise Exception(_("Not implemented."))

    def lease_ip(self, node_id):
        """
        Rent IP for the VPS on the node.
        :param node_id: Node, on which VPS is created.
        :param count: Number of IPs to rent.
        :return: tuple (ip, gw, netmask, dns1, dns2)
        """
        assert node_id > 0

        hv_node = Server.active.get(pk=node_id)

        datacenters = hv_node.filter_parents(Datacenter)
        if len(datacenters) <= 0:
            raise Exception("Missing parent datacenters of hypervisor node %s" % node_id)

        renter = IPAddressRenter.from_datacenter(datacenters[0], ip_version=4)

        leased_ips = renter.rent(count=1)
        if len(leased_ips) <= 0:
            raise Exception("Unable to lease main IP for hypervisor %s" % node_id)

        return self.find_ip_info(leased_ips[0].address)

    def find_ip_info(self, ip_address):
        """
        Search and return info about IP address: gateway and netmask.
        Check only in IPNetworkPools that is free.
        :param ip_address:
        :return: tuple (ip, gw, netmask, dns1, dns2)
        """
        assert ip_address

        found_ip = GlobalIPManager.get_ip(ip_address)
        target_net_pool = found_ip.pool

        netmask = target_net_pool.get_option_value('netmask', default=None)
        if not netmask:
            target_net_pool = None

        # checking IP pool
        netmask = target_net_pool.get_option_value('netmask', default=None)
        gateway = target_net_pool.get_option_value('gateway', default=None)
        dns1 = target_net_pool.get_option_value('dns1', default=None)
        dns2 = target_net_pool.get_option_value('dns2', default=None)

        if not netmask or not gateway:
            raise Exception("IP pool %s have no network settings." % target_net_pool)

        return ip_address, gateway, netmask, dns1, dns2


class CloudServiceHandler(object):
    """
    CloudService instance manager. Handles specific service instance operations.
    """

    def __init__(self, backend, **options):
        assert backend

        self.backend = backend
        self.options = options

    def start(self):
        pass

    def stop(self):
        pass

    def destroy(self):
        pass

    def modify(self, **options):
        pass


class VpsHandler(CloudServiceHandler):
    def add_ip(self, ip):
        pass

    def delete_ip(self, ip):
        pass


class HostingHandler(CloudServiceHandler):
    def get_usage(self):
        pass

    def get_info(self):
        pass
