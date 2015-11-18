from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from assets.models import Server, Datacenter
from ipman.models import IPAddress, IPNetworkPool, IPAddressPool
from resources.models import Resource


class CloudTask(object):
    def __init__(self, tracker, **context):
        assert tracker

        self.tracker = tracker
        self.context = context
        self.result = {}

    def execute(self):
        raise Exception(_("Not implemented."))

    def get_result(self):
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

        tracker = self.task_tracker.execute(cloud_task_class, **kwargs)

        return tracker


class HypervisorBackend(CloudBackend):
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
        :return: list of rented IPs
        """
        assert node_id > 0

        hv_node = Server.active.get(pk=node_id)

        datacenters = hv_node.filter_parents(Datacenter)
        if len(datacenters) <= 0:
            raise Exception("Missing parent datacenters of hypervisor node %s" % node_id)

        datacenter = datacenters[0]

        # Find free IPNetworkPool (we have free and used IP pools in  this DC)
        ippools = datacenter.filter_childs(IPNetworkPool, status=Resource.STATUS_FREE)

        leased_ips = IPAddressPool.lease_ips([ippool.id for ippool in ippools], count=1)
        if len(leased_ips) <= 0:
            raise Exception("Unable to lease main IP for hypervisor %s" % node_id)

        return self.find_ip_info(leased_ips[0].address)

    def find_ip_info(self, ip_address):
        """
        Search and return info about IP address: gateway and netmask.
        Check only in IPNetworkPools that is free.
        :param ip_address:
        :return: tuple (ip, gw, netmask)
        """
        assert ip_address

        target_net_pool = None
        found_ips = IPAddress.active.filter(address=ip_address)
        if len(found_ips) > 0:
            found_ip = found_ips[0]
            target_net_pool = found_ip.get_origin()

            netmask = target_net_pool.get_option_value('netmask', default=None)
            if not netmask:
                target_net_pool = None

        if not target_net_pool:
            for ip_net_pool in IPNetworkPool.active.filter():
                if ip_net_pool.can_add(ip_address):
                    target_net_pool = ip_net_pool
                    break

        if not target_net_pool:
            raise Exception("IP %s have no origin" % ip_address)

        # checking IP pool
        netmask = target_net_pool.get_option_value('netmask', default=None)
        gateway = target_net_pool.get_option_value('gateway', default=None)

        if not netmask or not gateway:
            raise Exception("IP pool %s have no network settings." % target_net_pool)

        return ip_address, gateway, netmask


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
