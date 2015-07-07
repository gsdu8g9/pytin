from __future__ import unicode_literals
from assets.models import PhysicalAssetMixin
from resources.models import Resource, ResourceOption


class DirectAdminLicensePool(PhysicalAssetMixin, Resource):
    class Meta:
        proxy = True

    def __str__(self):
        return '%s' % self.name


class DirectAdminLicense(PhysicalAssetMixin, Resource):
    """
    Resource grouping by region.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return 'DA%s' % self.lid

    @property
    def cid(self):
        return self.get_option_value('cid', default='')

    @cid.setter
    def cid(self, value):
        assert value is not None, "Parameter 'value' must be defined."
        self.set_option('cid', value, format=ResourceOption.FORMAT_INT)

    @property
    def lid(self):
        return self.get_option_value('lid', default='')

    @lid.setter
    def lid(self, value):
        assert value is not None, "Parameter 'value' must be defined."
        self.set_option('lid', value, format=ResourceOption.FORMAT_INT)

    def delete(self, cascade=False, purge=False):
        """
        Override delete: free instead of delete
        """
        if purge:
            super(DirectAdminLicense, self).delete(cascade=cascade, purge=purge)
        else:
            self.free()
            self.save()

            # delete related objects
            for child in self:
                child.delete(cascade=cascade, purge=purge)
