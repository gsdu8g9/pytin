from django.test import TestCase

from ipman.models import IPAddress
from resources.models import Resource
from software.models import DirectAdminLicense


class SoftwareAppTest(TestCase):
    def test_directadmin_delete(self):
        dalic1 = DirectAdminLicense.objects.create(name='Test LIC', cid=1234, lid=12345,
                                                   status=Resource.STATUS_INUSE)
        ip2 = IPAddress.objects.create(address='46.17.40.29', status=Resource.STATUS_INUSE)

        self.assertEqual(Resource.STATUS_INUSE, dalic1.status)
        self.assertEqual(Resource.STATUS_INUSE, ip2.status)

        dalic1.parent = ip2
        dalic1.save()

        # IP deleted with related objects
        ip2.delete()

        ip2.refresh_from_db()
        dalic1.refresh_from_db()

        self.assertTrue(ip2.is_free)
        self.assertTrue(dalic1.is_free)
