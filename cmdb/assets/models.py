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
            self.free(cascade=cascade)


class RegionResource(Resource):
    """
    Resource grouping by region.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.name


class Datacenter(Resource):
    class Meta:
        proxy = True

    def __str__(self):
        return self.name

    @property
    def support_email(self):
        return self.get_option_value('support_email', default='')

    @support_email.setter
    def support_email(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('support_email', value)


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
        return self.get_option_value('serial', default=unicode(self.id))

    @serial.setter
    def serial(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('serial', value.lower())

    @property
    def is_rack_mountable(self):
        return isinstance(self, RackMountable)


class RackMountable(AssetResource):
    """
    Physical resource, that can be mounted in Rack.
    Such is server, switch.
    """

    class Meta:
        proxy = True

    @property
    def position(self):
        return self.get_option_value('rack_position', default=0)

    @position.setter
    def position(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('rack_position', value, format=ResourceOption.FORMAT_INT)

    @property
    def unit_size(self):
        return self.get_option_value('unit_size', default=0)

    @unit_size.setter
    def unit_size(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('unit_size', value, format=ResourceOption.FORMAT_INT)

    @property
    def is_mounted(self):
        if not self.parent or not isinstance(self.parent.as_leaf_class(), Rack):
            self.position = 0

        return self.position > 0

    def mount(self, rack):
        assert rack
        assert isinstance(rack, Rack)

        if self.parent_id != rack.id:
            self.parent_id = rack.id
            self.save()

            self.position = 0


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

        self.set_option('mac', unicode(_mac).upper())

    @property
    def uplink(self):
        return self.get_option_value('uplink', default=0)

    @uplink.setter
    def uplink(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('uplink', value, format=ResourceOption.FORMAT_INT)


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
        self.set_option('linked_port_mac', unicode(port_object))

        if port_object.parent:
            self.set_option('linked_port_parent', unicode(port_object.parent.as_leaf_class()))

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


class Switch(PhysicalAssetMixin, RackMountable):
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


class Server(PhysicalAssetMixin, RackMountable):
    """
    Server object
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "i-%s %s" % (self.id, self.label)

    @property
    def switch_port(self):
        server_port = ServerPort.objects.get(parent=self.id)
        connections = PortConnection.objects.active(linked_port_id=server_port.id)
        if len(connections) > 0:
            return connections[0].parent

        return None


class Rack(PhysicalAssetMixin, AssetResource):
    """
    Rack mount object
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s (%s, %sU)" % (self.label, self.name, self.size)

    @property
    def size(self):
        return self.get_option_value('rack_size', default=45)

    @size.setter
    def size(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('rack_size', value, format=ResourceOption.FORMAT_INT)


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
