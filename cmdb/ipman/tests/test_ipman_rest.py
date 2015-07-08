from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from ipman.models import IPNetworkPool
from resources.models import Resource


class ResourcesAPITests(APITestCase):
    def setUp(self):
        super(ResourcesAPITests, self).setUp()

        user_name = 'admin'

        user, created = User.objects.get_or_create(username=user_name, password=user_name, email='admin@admin.com',
                                                   is_staff=True)
        token, created = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_ippool_newip(self):
        ipnet1 = IPNetworkPool.objects.create(network='192.168.1.1/24')
        ipnet2 = IPNetworkPool.objects.create(network='192.169.1.1/24')

        response = self.client.get('/v1/ipman/rent?pool=%s&pool=%s&count=3' % (ipnet1.id, ipnet2.id), format='json')

        self.assertEqual(3, response.data['count'])
        self.assertEqual(3, len(response.data['results']))

        items = response.data['results']

        self.assertEqual(3, items[0]['id'])
        self.assertEqual('192.168.1.2', items[0]['address'])
        self.assertEqual(6, items[0]['beauty'])
        self.assertEqual(Resource.STATUS_LOCKED, items[0]['status'])

        self.assertEqual(4, items[1]['id'])
        self.assertEqual('192.169.1.2', items[1]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[1]['status'])

        self.assertEqual(5, items[2]['id'])
        self.assertEqual('192.168.1.3', items[2]['address'])
        self.assertEqual(Resource.STATUS_LOCKED, items[2]['status'])
