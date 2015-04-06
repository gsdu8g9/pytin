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

    def _get_mac(self):
        return self.get_option_value('mac', default="00:00:00:00:00:00")

    def _set_mac(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('mac', value)

    def _get_number(self):
        return self.get_option_value('number', default="0")

    def _set_number(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('number', value)

    mac = property(fget=_get_mac, fset=_set_mac)
    number = property(fget=_get_number, fset=_set_number)


class InventoryResource(Resource):
    """
    Physical resource, that have serial number to track it.
    Such is server, rack, network card, etc.
    """

    class Meta:
        proxy = True

    def _get_label(self):
        return self.get_option_value('label', default="s%s" % self.id)

    def _set_label(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('label', value)

    def _get_serial(self):
        return self.get_option_value('serial', default="sn%s" % self.id)

    def _set_serial(self, value):
        assert value is not None, "Parameter 'value' must be defined."

        self.set_option('serial', value)

    def _get_is_failed(self):
        return self.objects.active(status=Resource.STATUS_FAILED).exists()

    label = property(fget=_get_label, fset=_set_label)
    serial = property(fget=_get_serial, fset=_set_serial)
    is_failed = property(fget=_get_is_failed)


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
