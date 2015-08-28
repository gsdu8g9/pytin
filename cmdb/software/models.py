from __future__ import unicode_literals
from resources.models import Resource, ResourceOption


class DirectAdminLicense(Resource):
    """
    Resource grouping by region.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return 'DA%s' % self.lid

    @property
    def cid(self):
        return self.get_option_value('directadmin_cid', default='')

    @cid.setter
    def cid(self, value):
        assert value is not None, "Parameter 'value' must be defined."
        self.set_option('directadmin_cid', value, format=ResourceOption.FORMAT_INT)

    @property
    def lid(self):
        return self.get_option_value('directadmin_lid', default='')

    @lid.setter
    def lid(self, value):
        assert value is not None, "Parameter 'value' must be defined."
        self.set_option('directadmin_lid', value, format=ResourceOption.FORMAT_INT)
