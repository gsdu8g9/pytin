import netaddr

from resources.models import Resource


class RegionResource(Resource):
    """
    Resource grouping.
    """

    class Meta:
        proxy = True


class PortConnection(Resource):
    """
    Connection between the ports in the network
    """

    class Meta:
        proxy = True

    @property
    def device1(self):
        return self.get_option_value('device1', default=0)

    @device1.setter
    def device1(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('device1', value)

    @property
    def device2(self):
        return self.get_option_value('device2', default=0)

    @device2.setter
    def device2(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('device2', value)

    @property
    def link_speed_mbit(self):
        return self.get_option_value('link_speed_mbit', default=1000)

    @link_speed_mbit.setter
    def link_speed_mbit(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('link_speed_mbit', value)


class SwitchPort(Resource):
    """
    Network switch port
    """

    class Meta:
        proxy = True

    @property
    def number(self):
        return self.get_option_value('number', default=0)

    @number.setter
    def number(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('number', value)


class ServerPort(Resource):
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

    @property
    def number(self):
        return self.get_option_value('number', default=0)

    @number.setter
    def number(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('number', value)


class InventoryResource(Resource):
    """
    Physical resource, that have serial number to track it.
    Such is server, rack, network card, etc.
    """

    class Meta:
        proxy = True

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

    @property
    def is_failed(self):
        return super(Resource, self).is_failed or \
               Resource.objects.active(status=Resource.STATUS_FAILED, parent=self).exists()


class ServerResource(InventoryResource):
    """
    Server object
    """

    class Meta:
        proxy = True


class VirtualServerResource(InventoryResource):
    """
    Server object
    """

    class Meta:
        proxy = True


class RackResource(InventoryResource):
    """
    Rack mount object
    """

    class Meta:
        proxy = True
