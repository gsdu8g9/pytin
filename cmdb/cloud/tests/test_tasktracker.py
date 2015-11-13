from django.test import TestCase

from cloud.models import CloudConfig, CloudTaskTracker, TaskTrackerStatus


class CloudControllerTest(TestCase):
    def test_controller_create_success(self):
        cloud = CloudConfig()
        tracker_class = cloud.get_task_tracker()

        task_tracker1 = tracker_class(task_class='SomeClassName')
        task_tracker1.context = {'some': 'value'}
        task_tracker1.save()

        task_tracker2 = tracker_class(task_class='SomeClassName')
        task_tracker2.context = {'some': 'value'}
        task_tracker2.failed('some error')
        task_tracker2.save()

        self.assertEqual(task_tracker1.id, tracker_class.get(task_tracker1.id).id)
        self.assertEqual(task_tracker2.id, tracker_class.get(task_tracker2.id).id)
        self.assertEqual(2, len(tracker_class.find()))
        self.assertEqual(1, len(tracker_class.find(status=TaskTrackerStatus.STATUS_NEW)))
        self.assertEqual(1, len(tracker_class.find(status=TaskTrackerStatus.STATUS_FAILED)))
        self.assertEqual(0, len(tracker_class.find(status=TaskTrackerStatus.STATUS_SUCCESS)))
