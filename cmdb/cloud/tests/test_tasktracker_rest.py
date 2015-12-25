from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from cloud.models import CmdbCloudConfig
from cloud.provisioning import CloudTask


class MockVpsControlTask(CloudTask):
    task_name = 'tasks.async.mock_vps_control'

    def poll(self):
        return True, self.context

    def wait(self):
        pass


class ResourcesAPITests(APITestCase):
    def setUp(self):
        user_name = 'admin'
        user, created = User.objects.get_or_create(username=user_name, password=user_name, email='admin@admin.com',
                                                   is_staff=True)
        token, created = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_controller_create_success(self):
        cloud = CmdbCloudConfig()
        tracker_class = cloud.task_tracker

        full_cloud_task_class_name = "%s.%s" % (MockVpsControlTask.__module__, MockVpsControlTask.__name__)

        task_tracker1 = tracker_class(task_class=full_cloud_task_class_name)
        task_tracker1.context = {'some': 'value'}
        task_tracker1.save()

        task_tracker2 = tracker_class(task_class=full_cloud_task_class_name)
        task_tracker2.context = {'some': 'value'}
        task_tracker2.failed('some error')
        task_tracker2.save()

        response_err = self.client.patch('/v1/cloud_tasks/%s/' % task_tracker1.id)
        self.assertEqual(405, response_err.status_code)

        response1 = self.client.get('/v1/cloud_tasks/%s/' % task_tracker1.id)
        self.assertEqual(200, response1.status_code)
        self.assertEqual(task_tracker1.id, response1.data['id'])
        self.assertEqual('success', response1.data['status'])

        response2 = self.client.get('/v1/cloud_tasks/%s/' % task_tracker2.id)
        self.assertEqual(200, response2.status_code)
        self.assertEqual(task_tracker2.id, response2.data['id'])
        self.assertEqual('failed', response2.data['status'])
        self.assertEqual('some error', response2.data['error'])
