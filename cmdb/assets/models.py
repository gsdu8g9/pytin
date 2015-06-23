from __future__ import unicode_literals

import netaddr
from cmdb.settings import logger

from resources.models import Resource, ResourceOption


class PhysicalAssetMixin(object):
    """
    Physical mixin, overrides delete() method - free instead of delete.
    """

    class Meta:
        proxy = True

    def delete(self, cascade=False, purge=False):
        """
        Override delete: free instead of delete
        """

        logger.debug("Removing physical object %s" % self)

        if purge:
            super(PhysicalAssetMixin, self).delete(cascade=cascade, purge=purge)
        else:
            self.free(cascade=True)


class AssetResource(Resource):
    """
    Physical resource, that have serial number to track it.
    Such is server, rack, network card, etc.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "inv-%s %s (SN: %s)" % (self.id, self.label, self.serial)

    @property
    def label(self):
        return self.get_option_value('label', default="no label")

    @label.setter
    def label(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('label', value)

    @property
    def serial(self):
        return self.get_option_value('serial', default=str(self.id))

    @serial.setter
    def serial(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('serial', value.lower())


class NetworkPort(Resource):
    """
    Network port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s:%s%s" % (self.parent.id, self.number, " (uplink)" if self.uplink else "")

    @property
    def number(self):
        return self.get_option_value('number', default=0)

    @number.setter
    def number(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('number', value, format=ResourceOption.FORMAT_INT)

    @property
    def mac(self):
        return self.get_option_value('mac', default="000000000000")

    @mac.setter
    def mac(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        _mac = netaddr.EUI(value, dialect=netaddr.mac_bare)

        self.set_option('mac', str(_mac).upper())

    @property
    def uplink(self):
        return self.get_option_value('uplink', default=0)

    @uplink.setter
    def uplink(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('uplink', value, format=ResourceOption.FORMAT_INT)


class RegionResource(Resource):
    """
    Resource grouping by region.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.name


class PortConnection(Resource):
    """
    Connection between the ports in the network
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s <-> srv:%s (%s Mbit)" % (self.parent.as_leaf_class(), self.linked_port_id, self.link_speed_mbit)

    @property
    def linked_port_id(self):
        return self.get_option_value('linked_port_id', default=0)

    @linked_port_id.setter
    def linked_port_id(self, value):
        self.set_option('linked_port_id', value, format=ResourceOption.FORMAT_INT)

        port_object = Resource.objects.get(pk=value)
        self.set_option('linked_port_mac', str(port_object))

        if port_object.parent:
            self.set_option('linked_port_parent', str(port_object.parent.as_leaf_class()))

    @property
    def link_speed_mbit(self):
        return self.get_option_value('link_speed_mbit', default=1000)

    @link_speed_mbit.setter
    def link_speed_mbit(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('link_speed_mbit', value, format=ResourceOption.FORMAT_INT)

    def save(self, *args, **kwargs):
        super(PortConnection, self).save(*args, **kwargs)


class SwitchPort(PhysicalAssetMixin, NetworkPort):
    """
    Network port
    """

    class Meta:
        proxy = True


class ServerPort(PhysicalAssetMixin, NetworkPort):
    """
    Network port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "eth%s:%s" % (self.number, self.mac)


class Switch(PhysicalAssetMixin, AssetResource):
    """
    Switch object
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "sw-%s %s" % (self.id, self.label)


class GatewaySwitch(Switch):
    """
    Gateway device (BGP, announce networks)
    """

    class Meta:
        proxy = True


class Server(PhysicalAssetMixin, AssetResource):
    """
    Server object
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "i-%s %s" % (self.id, self.label)


class Rack(PhysicalAssetMixin, AssetResource):
    """
    Rack mount object
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s" % self.label


class VirtualServerPort(NetworkPort):
    """
    Network port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "veth%s:%s" % (self.number, self.mac)


class VirtualServer(AssetResource):
    """
    VirtualServer object. This is not inventory.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "vm-%s %s" % (self.id, self.label)
