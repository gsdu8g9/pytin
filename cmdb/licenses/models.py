from __future__ import unicode_literals

from django.db import models
from django.db.models import DO_NOTHING
from django.utils.encoding import python_2_unicode_compatible

from ipman.models import GlobalIPManager, IPAddressGeneric, IPAddressPoolGeneric


@python_2_unicode_compatible
class DirectAdminLicense(models.Model):
    assigned_ip = models.OneToOneField(IPAddressGeneric, related_name='directadminlicense', on_delete=DO_NOTHING)
    cid = models.IntegerField("Client ID.", db_index=True)
    lid = models.IntegerField("License ID.", db_index=True)

    def __str__(self):
        return "DA %s (%s)" % (self.lid, self.assigned_ip)

    @staticmethod
    def register_license(cid, lid, ip_address, pool):
        assert cid > 0
        assert lid > 0
        assert ip_address
        assert pool
        assert isinstance(pool, IPAddressPoolGeneric)

        if not isinstance(ip_address, IPAddressGeneric):
            ip_address = GlobalIPManager.get_ip(ip_address)

        da_license, created = DirectAdminLicense.objects.update_or_create(
            cid=cid,
            lid=lid,
            defaults=dict(
                status=ip_address.status,
                assigned_ip=ip_address
            )
        )

        GlobalIPManager.move_ips(pool, ip_address, count=1)

        return da_license

    @property
    def status(self):
        return self.assigned_ip.status

    @property
    def last_seen(self):
        return self.assigned_ip.last_seen

    def free(self):
        self.assigned_ip.free()

    def use(self):
        self.assigned_ip.use()

    def lock(self):
        self.assigned_ip.lock()

    def delete(self, using=None, keep_parents=False):
        self.assigned_ip.release()

        return super(DirectAdminLicense, self).delete(using, keep_parents)
