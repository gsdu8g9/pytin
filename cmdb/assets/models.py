import netaddr

from resources.models import Resource, ResourceOption


class RegionResource(Resource):
    """
    Resource grouping by region.
    """

    class Meta:
        proxy = True


class PortConnection(Resource):
    """
    Connection between the ports in the network
    """

    class Meta:
        proxy = True

    def __str__(self):
        port1 = Resource.objects.get(pk=self.port1)
        port2 = Resource.objects.get(pk=self.port2)

        return "%s:%d<->%s:%d" % (port1.parent.id, port1.number, port2.parent.id, port2.number)

    @property
    def port1(self):
        return self.get_option_value('port1', default=0)

    @port1.setter
    def port1(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('port1', value, format=ResourceOption.FORMAT_INT)

    @property
    def port2(self):
        return self.get_option_value('port2', default=0)

    @port2.setter
    def port2(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('port2', value, format=ResourceOption.FORMAT_INT)

    @property
    def link_speed_mbit(self):
        return self.get_option_value('link_speed_mbit', default=1000)

    @link_speed_mbit.setter
    def link_speed_mbit(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('link_speed_mbit', value, format=ResourceOption.FORMAT_INT)


class SwitchPort(Resource):
    """
    Network switch port
    """

    class Meta:
        proxy = True

    def __str__(self):
        return "%s:%d" % (self.parent.as_leaf_class(), self.number)

    @property
    def number(self):
        return self.get_option_value('number', default=0)

    @number.setter
    def number(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('number', value, format=ResourceOption.FORMAT_INT)


class ServerPort(SwitchPort):
    """
    Network port
    """

    class Meta:
        proxy = True

    @property
    def mac(self):
        return self.get_option_value('mac', default="000000000000")

    @mac.setter
    def mac(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        _mac = netaddr.EUI(value, dialect=netaddr.mac_bare)

        self.set_option('mac', str(_mac))


class InventoryResource(Resource):
    """
    Physical resource, that have serial number to track it.
    Such is server, rack, network card, etc.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.label

    @property
    def label(self):
        return self.get_option_value('label', default="s%s" % self.id)

    @label.setter
    def label(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('label', value)

    @property
    def serial(self):
        return self.get_option_value('serial', default="sn%s" % self.id)

    @serial.setter
    def serial(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('serial', value)


class Switch(InventoryResource):
    """
    Switch object
    """

    class Meta:
        proxy = True


class GatewaySwitch(InventoryResource):
    """
    Gateway device (BGP, announce networks)
    """

    class Meta:
        proxy = True


class Server(InventoryResource):
    """
    Server object
    """

    class Meta:
        proxy = True


class VirtualServer(InventoryResource):
    """
    Server object
    """

    class Meta:
        proxy = True


class Rack(InventoryResource):
    """
    Rack mount object
    """

    class Meta:
        proxy = True
