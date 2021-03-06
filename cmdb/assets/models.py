from __future__ import unicode_literals

import netaddr
from django.utils.encoding import python_2_unicode_compatible

from resources.models import Resource, ResourceOption


class RegionResource(Resource):
    """
    Resource grouping by region.
    """

    class Meta:
        proxy = True


class Datacenter(Resource):
    class Meta:
        proxy = True

    @property
    def support_email(self):
        return self.get_option_value('support_email', default='')

    @support_email.setter
    def support_email(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('support_email', value)


@python_2_unicode_compatible
class AssetResource(Resource):
    """
    Physical resource, that have serial number to track it.
    Such is server, rack, network card, etc.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "a%s %s (SN: %s)" % (self.id, self.label, self.serial)

    @property
    def label(self):
        return self.get_option_value('label', default="no label")

    @label.setter
    def label(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('label', value)

    @property
    def serial(self):
        return self.get_option_value('serial', default=self.id)

    @serial.setter
    def serial(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('serial', value.lower())


@python_2_unicode_compatible
class RackMountable(AssetResource):
    """
    Physical resource, that can be mounted in Rack.
    Such is server, switch.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "i%s %s (%sU)" % (self.id, self.label, self.unit_size)

    @staticmethod
    def is_rack_mountable(resource):
        return isinstance(resource, RackMountable)

    @property
    def on_rails(self):
        return self.get_option_value('on_rails', default=False)

    @on_rails.setter
    def on_rails(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('on_rails', value, format=ResourceOption.FORMAT_BOOL)

    @property
    def position(self):
        return int(self.get_option_value('rack_position', default=0))

    @position.setter
    def position(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('rack_position', value, format=ResourceOption.FORMAT_INT)

    @property
    def unit_size(self):
        return self.get_option_value('unit_size', default=1)

    @unit_size.setter
    def unit_size(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('unit_size', value, format=ResourceOption.FORMAT_INT)

    @property
    def is_mounted(self):
        if not self.parent or not isinstance(self.typed_parent, Rack):
            self.position = 0

        return self.position > 0

    def mount_to(self, rack):
        assert rack
        assert isinstance(rack, Rack)

        if self.parent_id != rack.id:
            self.parent = rack
            self.save()

            self.position = 0

    def save(self, *args, **kwargs):
        super(AssetResource, self).save(*args, **kwargs)

        if self.is_saved and self.name.lower() == 'resource':
            self.name = "i%s" % self.id

            super(AssetResource, self).save()


@python_2_unicode_compatible
class NetworkPort(Resource):
    """
    Network port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s:%s%s" % (self.parent.id, self.number, " (uplink)" if self.uplink else "")

    @property
    def device(self):
        return self.typed_parent

    @staticmethod
    def normalize_mac(mac):
        mac = netaddr.EUI(mac, dialect=netaddr.mac_bare)
        return unicode(mac).upper()

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

        self.set_option('mac', NetworkPort.normalize_mac(value))

    @property
    def uplink(self):
        return self.get_option_value('uplink', default=0)

    @uplink.setter
    def uplink(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('uplink', value, format=ResourceOption.FORMAT_INT)

    def delete(self, using=None):
        """
        Remove linked resources
        """
        for connection in PortConnection.active.filter(linked_port_id=self.id):
            connection.delete()

        super(NetworkPort, self).delete(using=using)


@python_2_unicode_compatible
class PortConnection(Resource):
    """
    Connection between the ports in the network
    """

    class Meta:
        proxy = True

    def __str__(self):
        linked_device = '?'
        if self.linked_port and self.linked_port.parent:
            linked_device = self.linked_port.typed_parent

        return "%s <- %s Mbit -> %s" % (
            self.typed_parent, self.link_speed_mbit, linked_device)

    @property
    def switch_port(self):
        return self.typed_parent

    @property
    def linked_port_id(self):
        return self.get_option_value('linked_port_id', default=0)

    @property
    def linked_port(self):
        """
        Return the connected server port.
        """
        linked_port_id = self.linked_port_id

        if linked_port_id > 0:
            ports = Resource.active.filter(pk=linked_port_id)
            if len(ports) <= 0:
                return None
            else:
                return ports[0]

        return None

    @linked_port_id.setter
    def linked_port_id(self, value):
        self.set_option('linked_port_id', value, format=ResourceOption.FORMAT_INT)

        port_object = Resource.objects.get(pk=value)
        self.set_option('linked_port_mac', unicode(port_object))

        if port_object.parent:
            self.set_option('linked_port_parent', unicode(port_object.typed_parent))

    @property
    def link_speed_mbit(self):
        return self.get_option_value('link_speed_mbit', default=1000)

    @link_speed_mbit.setter
    def link_speed_mbit(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('link_speed_mbit', value, format=ResourceOption.FORMAT_INT)

    @staticmethod
    def create(switch_port, server_port):
        assert switch_port
        assert server_port

        return PortConnection.objects.create(parent=switch_port, linked_port_id=server_port.id)


class SwitchPort(NetworkPort):
    """
    Network port
    """

    class Meta:
        proxy = True

    @property
    def connections(self):
        """
        Returns iterable with the specified port types.
        """
        return PortConnection.active.filter(parent=self)


@python_2_unicode_compatible
class ServerPort(NetworkPort):
    """
    Network port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "eth%s:%s" % (self.number, self.mac)

    @property
    def connection(self):
        try:
            return PortConnection.active.get(linked_port_id=self.id)
        except:
            return None

    @property
    def switch_port(self):
        try:
            return self.connection.typed_parent
        except:
            return None


class Switch(RackMountable):
    """
    Switch object
    """

    class Meta:
        proxy = True

    def get_port(self, number):
        assert number > 0

        return SwitchPort.active.get(parent=self, number=number)


class GatewaySwitch(Switch):
    """
    Gateway device (BGP, announce networks)
    """

    class Meta:
        proxy = True


class Server(RackMountable):
    """
    Server object
    """

    class Meta:
        proxy = True

    @staticmethod
    def is_server(resource):
        return isinstance(resource, Server)

    @property
    def ethernet_ports(self):
        return ServerPort.active.filter(parent=self)


@python_2_unicode_compatible
class Rack(AssetResource):
    """
    Rack mount object
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.name

    @property
    def size(self):
        return self.get_option_value('rack_size', default=45)

    @size.setter
    def size(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('rack_size', value, format=ResourceOption.FORMAT_INT)


@python_2_unicode_compatible
class VirtualServerPort(NetworkPort):
    """
    Network port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "veth%s:%s" % (self.number, self.mac)


@python_2_unicode_compatible
class VirtualServer(AssetResource):
    """
    VirtualServer object. This is not inventory.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "vm%s %s" % (self.id, self.label)

    @property
    def ethernet_ports(self):
        return VirtualServerPort.active.filter(parent=self)

    @property
    def tech(self):
        """
        Getting the VPS virtualization technology.
        :return:
        """
        return self.get_option_value('tech', default='')

    @tech.setter
    def tech(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('tech', value)
