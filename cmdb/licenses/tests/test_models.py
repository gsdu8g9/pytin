from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from assets.models import Server
from ipman.models import IPAddressGeneric, IPAddressPoolFactory
from licenses.models import DirectAdminLicense
from resources.models import Resource


class LicensesModels(TestCase):
    def test_directadmin_bulk_delete_assigned_license(self):
        """
        All related objects are removed by relations.
        """
        da_pool = IPAddressPoolFactory.from_name(name='DirectAdmin pool')
        ipv4_net_pool = IPAddressPoolFactory.from_name(name='Generic pool')
        ip_addr = IPAddressGeneric.objects.create(pool=ipv4_net_pool, address='46.17.40.200')
        ip_addr1 = IPAddressGeneric.objects.create(pool=ipv4_net_pool, address='46.17.40.201')

        self.assertEqual(ipv4_net_pool.id, ip_addr.pool.id)

        da_license = DirectAdminLicense.register_license(cid=6768, lid=362163, ip_address=ip_addr, pool=da_pool)
        da_license.use()

        da_license.refresh_from_db()
        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_INUSE, da_license.status)
        self.assertEqual(Resource.STATUS_INUSE, ip_addr.status)
        self.assertEqual(da_license.assigned_ip.id, ip_addr.id)

        DirectAdminLicense.objects.all().delete()

        self.assertEqual(0, DirectAdminLicense.objects.all().count())
        self.assertEqual(2, IPAddressGeneric.objects.all().count())

    def test_directadmin_delete_assigned_license(self):
        da_pool = IPAddressPoolFactory.from_name(name='DirectAdmin pool')
        ipv4_net_pool = IPAddressPoolFactory.from_name(name='Generic pool')
        ip_addr = IPAddressGeneric.objects.create(pool=ipv4_net_pool, address='46.17.40.200')
        ip_addr1 = IPAddressGeneric.objects.create(pool=ipv4_net_pool, address='46.17.40.201')

        self.assertEqual(ipv4_net_pool.id, ip_addr.pool.id)

        da_license = DirectAdminLicense.register_license(cid=6768, lid=362163, pool=da_pool, ip_address=ip_addr)
        da_license.use()

        da_license.refresh_from_db()
        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_INUSE, da_license.status)
        self.assertEqual(Resource.STATUS_INUSE, ip_addr.status)
        self.assertEqual(da_license.assigned_ip.id, ip_addr.id)

        da_license.delete()

        self.assertEqual(0, DirectAdminLicense.objects.all().count())
        self.assertEqual(2, IPAddressGeneric.objects.all().count())

        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_FREE, ip_addr.status)
        self.assertEqual(ipv4_net_pool.id, ip_addr.pool.id)

    def test_directadmin_use_license(self):
        da_pool = IPAddressPoolFactory.from_name(name='DirectAdmin pool')
        ipv4_net_pool = IPAddressPoolFactory.from_name(name='Generic pool')
        ip_addr = IPAddressGeneric.objects.create(pool=ipv4_net_pool, address='46.17.40.200')
        server = Server.objects.create(name='Test server')

        da_license = DirectAdminLicense.register_license(cid=6768, lid=362163, pool=da_pool, ip_address=ip_addr)

        da_license.refresh_from_db()
        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_FREE, da_license.status)
        self.assertEqual(Resource.STATUS_FREE, ip_addr.status)

        ip_addr.use(server)

        da_license.refresh_from_db()
        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_INUSE, da_license.status)
        self.assertEqual(Resource.STATUS_INUSE, ip_addr.status)
        self.assertEqual(da_license.assigned_ip.id, ip_addr.id)

    def test_directadmin_ip_free(self):
        """ Test releasing of the DA license when assigned IP is freed """

        da_pool = IPAddressPoolFactory.from_name(name='DirectAdmin pool')
        ipv4_net_pool = IPAddressPoolFactory.from_name(name='Generic pool')
        ip_addr = IPAddressGeneric.objects.create(pool=ipv4_net_pool, address='46.17.40.200')

        da_license = DirectAdminLicense.register_license(cid=6768, lid=362163, pool=da_pool, ip_address=ip_addr)

        da_license.refresh_from_db()
        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_FREE, da_license.status)
        self.assertEqual(Resource.STATUS_FREE, ip_addr.status)

        da_license.use()

        da_license.refresh_from_db()
        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_INUSE, da_license.status)
        self.assertEqual(Resource.STATUS_INUSE, ip_addr.status)

        ip_addr.free()

        da_license.refresh_from_db()
        ip_addr.refresh_from_db()
        self.assertEqual(Resource.STATUS_FREE, da_license.status)
        self.assertEqual(Resource.STATUS_FREE, ip_addr.status)

    def test_directadmin_model(self):
        da_pool = IPAddressPoolFactory.from_name(name='DirectAdmin pool')
        ipv4_net_pool = IPAddressPoolFactory.from_name(name='Generic pool')
        ip_addr = IPAddressGeneric.objects.create(pool=ipv4_net_pool, address='46.17.40.200')

        da_license = DirectAdminLicense.register_license(cid=6768, lid=362163, pool=da_pool, ip_address=ip_addr)

        self.assertTrue(isinstance(da_license, DirectAdminLicense))
        self.assertEqual(Resource.STATUS_FREE, da_license.status)
        self.assertEqual(6768, da_license.cid)
        self.assertEqual(362163, da_license.lid)
        self.assertEqual('46.17.40.200', "%s" % da_license.assigned_ip)
