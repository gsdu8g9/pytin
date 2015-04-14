from resources.models import ResourcePool, Resource


class RegionResource(ResourcePool):
    """
    Resource grouping.
    """

    class Meta:
        proxy = True


class PortResource(Resource):
    """
    Network port
    """

    class Meta:
        proxy = True

    @property
    def mac(self):
        return self.get_option_value('mac', default="00:00:00:00:00:00")

    @mac.setter
    def mac(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('mac', value)

    @property
    def number(self):
        return self.get_option_value('number', default="0")

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


class RackResource(InventoryResource):
    """
    Rack mount object
    """

    class Meta:
        proxy = True
