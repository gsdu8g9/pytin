from __future__ import unicode_literals

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
        ipnet = IPNetworkPool.create(network='192.168.1.1/24')

        count = 10
        for ip_addr in ipnet.available():
            print str(ip_addr)
            if count <= 0:
                break
            count -= 1

        response = self.client.get('/v1/ippool/%s/newip?count=3' % ipnet.id, format='json')

        self.assertEqual(3, response.data['count'])
        self.assertEqual(3, len(response.data['items']))

        items = response.data['items']

        self.assertEqual(2, items[0]['id'])
        self.assertEqual('192.168.1.1', items[0]['address'])
        self.assertEqual(6, items[0]['beauty'])
        self.assertEqual(Resource.STATUS_FREE, items[0]['status'])

        self.assertEqual(3, items[1]['id'])
        self.assertEqual('192.168.1.2', items[1]['address'])

        self.assertEqual(4, items[2]['id'])
        self.assertEqual('192.168.1.3', items[2]['address'])
