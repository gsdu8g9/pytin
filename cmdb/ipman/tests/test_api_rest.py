# coding=utf-8
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from assets.models import Datacenter
from assets.models import RegionResource
from ipman.models import IPAddressPoolFactory, IPAddressGeneric
from ipman.tests import utils
from resources.models import Resource


class IpmanAPITests(APITestCase):
    def setUp(self):
        super(IpmanAPITests, self).setUp()

        user_name = 'admin'

        user, created = User.objects.get_or_create(username=user_name, password=user_name, email='admin@admin.com',
                                                   is_staff=True)
        self.token, created = Token.objects.get_or_create(user=user)

    def test_ip_address_find(self):
        """Поиск IP адресов"""
        self._auth()

        moscow = RegionResource.objects.create(name='Moscow')
        dc1 = Datacenter.objects.create(name='Test DC 1', parent=moscow)
        dc2 = Datacenter.objects.create(name='Test DC 2', parent=moscow)

        net_pool1 = IPAddressPoolFactory.from_network(network="46.17.40.0/24", parent=dc1)
        net_pool2 = IPAddressPoolFactory.from_network(network="46.17.41.0/24", parent=dc2)

        # filter by param1
        response = self.client.get('/v1/ip/', data={'status': Resource.STATUS_INUSE}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data['results']))

        response = self.client.get('/v1/ip/', data={'address': '46.17.40.10'}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data['results']))

        response = self.client.get('/v1/ip/', data={'address__exact': '46.17.40.10'}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data['results']))

        response = self.client.get('/v1/ip/', data={'address__endswith': '111'}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data['results']))

        # разбивка по страницам
        response = self.client.get('/v1/ip/', data={'address__contains': '17.4'}, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(508, response.data['count'])
        self.assertEqual(50, len(response.data['results']))

    def test_ip_address_no_post(self):
        """Создать и удалить IP - нельзя."""
        self._auth()

        response = self.client.post('/v1/ip/', {})
        self.assertEqual(405, response.status_code)
        self.assertEqual('Method "POST" not allowed.', response.data['detail'])

    def test_ip_address_no_delete(self):
        """Создать и удалить IP - нельзя."""
        self._auth()

        response = self.client.delete('/v1/ip/', {})
        self.assertEqual(405, response.status_code)
        self.assertEqual('Method "DELETE" not allowed.', response.data['detail'])

    def test_ip_address_crud(self):
        """
        API управления IP позволяет только запрашивать, обновлять и искать IP.
        Создать и удалить IP - нельзя.
        """
        self._auth()

        moscow = RegionResource.objects.create(name='Moscow')
        dc1 = Datacenter.objects.create(name='Test DC 1', parent=moscow)
        dc2 = Datacenter.objects.create(name='Test DC 2', parent=moscow)

        net_pool1 = IPAddressPoolFactory.from_network(network="46.17.40.0/24", parent=dc1)
        net_pool2 = IPAddressPoolFactory.from_network(network="46.17.41.0/24", parent=dc1)

        net_pool3 = IPAddressPoolFactory.from_network(network="46.17.42.0/24", parent=dc2)

        # арендуем 5 IP
        response = self.client.get('/v1/ip/rent/dc?dc=%s&count=5' % dc1.id, format='json')

        self.assertEqual(200, response.status_code)

        # проверить данные
        items = response.data['results']

        self.assertEqual('46.17.40.1', items[0]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[0]['status'])

        self.assertEqual('46.17.41.1', items[1]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[1]['status'])

        # объекты для работы
        ip1 = items[0]
        ip2 = items[1]

        ip1_obj = IPAddressGeneric.objects.get(pk=ip1['id'])
        ip2_obj = IPAddressGeneric.objects.get(pk=ip2['id'])

        self.assertEqual(Resource.STATUS_LOCKED, ip1_obj.status)
        self.assertEqual(Resource.STATUS_LOCKED, ip2_obj.status)

        # обновить статус
        response = self.client.patch('/v1/ip/%s/' % ip1_obj.id, {
            'status': Resource.STATUS_INUSE
        })

        self.assertEqual(200, response.status_code)

        ip1_obj.refresh_from_db()
        ip2_obj.refresh_from_db()

        self.assertEqual(Resource.STATUS_INUSE, ip1_obj.status)
        self.assertEqual(Resource.STATUS_LOCKED, ip2_obj.status)

    def test_error_handle(self):
        self._auth()

        response = self.client.get('/v1/ip/rent/dc?dc=1&count=1', format='json')

        self.assertEqual(400, response.status_code)
        self.assertEqual('Resource matching query does not exist.', response.data['detail'])

    def test_api_no_auth(self):
        self._no_auth()

        response = self.client.get('/v1/ip/rent/dc?dc=%s&count=25' % 1, format='json')

        self.assertEqual(401, response.status_code)

    def test_rent_from_datacenter(self):
        self._auth()

        moscow = RegionResource.objects.create(name='Moscow')
        dc1 = Datacenter.objects.create(name='Test DC 1', parent=moscow)
        dc2 = Datacenter.objects.create(name='Test DC 2', parent=moscow)

        net_pool1 = IPAddressPoolFactory.from_network(network="46.17.40.0/24", parent=dc1)
        net_pool2 = IPAddressPoolFactory.from_network(network="46.17.41.0/24", parent=dc1)

        net_pool3 = IPAddressPoolFactory.from_network(network="46.17.42.0/24", parent=dc2)

        response = self.client.get('/v1/ip/rent/dc?dc=%s&count=25' % dc1.id, format='json')

        self.assertEqual(200, response.status_code)
        self.assertEqual(25, response.data['count'])
        self.assertEqual(25, len(response.data['results']))

        items = response.data['results']

        self.assertEqual('46.17.40.1', items[0]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[0]['status'])

        self.assertEqual('46.17.41.1', items[1]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[1]['status'])

        self.assertEqual('46.17.40.2', items[2]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[2]['status'])

        self.assertEqual(241, net_pool1.get_free_ips().count())
        self.assertEqual(242, net_pool2.get_free_ips().count())
        self.assertEqual(254, net_pool3.get_free_ips().count())

    def test_rent_from_pools(self):
        self._auth()

        ipnet1 = IPAddressPoolFactory.from_name(name='Generic pool 1')
        utils.fill_ip_pool(ipnet1, c_size=3, d_size=25, prefix='46.17.')

        ipnet2 = IPAddressPoolFactory.from_name(name='Generic pool 2')
        utils.fill_ip_pool(ipnet2, c_size=5, d_size=35, prefix='46.18.')

        response = self.client.get('/v1/ip/rent/pool?pool=%s&pool=%s&count=3' % (ipnet1.id, ipnet2.id),
                                   format='json')

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, response.data['count'])
        self.assertEqual(3, len(response.data['results']))

        items = response.data['results']

        self.assertEqual('46.17.1.1', items[0]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[0]['status'])
        self.assertEqual(False, items[0]['main'])

        self.assertEqual('46.18.1.1', items[1]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[1]['status'])
        self.assertEqual(False, items[0]['main'])

        self.assertEqual('46.17.1.2', items[2]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[2]['status'])
        self.assertEqual(False, items[0]['main'])

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def _no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token wrong')
