from django.test import TestCase

from ipman.models import IPAddress
from resources.models import Resource
from software.models import DirectAdminLicensePool, DirectAdminLicense


class SoftwareAppTest(TestCase):
    def test_directadmin_delete(self):
        dapool1 = DirectAdminLicensePool.objects.create(name='Test LIC pool', status=Resource.STATUS_INUSE)
        dalic1 = DirectAdminLicense.objects.create(parent=dapool1, name='Test LIC', cid=1234, lid=12345,
                                                   status=Resource.STATUS_INUSE)
        ip2 = IPAddress.objects.create(address='46.17.40.29', status=Resource.STATUS_INUSE)

        self.assertEqual(Resource.STATUS_INUSE, dapool1.status)
        self.assertEqual(Resource.STATUS_INUSE, dalic1.status)
        self.assertEqual(Resource.STATUS_INUSE, ip2.status)

        self.assertEqual(dapool1.id, dalic1.parent.id)

        dalic1.parent = ip2
        dalic1.save()

        # IP deleted with related objects
        ip2.delete()

        ip2.refresh_from_db()
        dalic1.refresh_from_db()

        self.assertTrue(ip2.is_free)
        self.assertTrue(dalic1.is_free)
