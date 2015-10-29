from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist

from django.test import TestCase

from cloud.models import CloudController, ServiceRequest


class CloudControllerTest(TestCase):
    def test_controller_initial(self):
        controller = CloudController()

        self.assertEqual(0, len(controller.registered_services()))

    def test_controller_registered_services(self):
        controller = CloudController()

        self.assertTrue(controller.register_service('cloud.tests.MockSyncServiceBackend'))
        self.assertEqual(1, len(controller.registered_services()))

        known_service = controller.registered_services()[0]
        self.assertEqual('cloud.tests.MockSyncServiceBackend', known_service.implementor)
        self.assertEqual('MockSyncServiceBackend', known_service.name)
        self.assertEqual(True, known_service.active)

    def test_controller_service_request(self):
        controller = CloudController()

        self.assertTrue(controller.register_service('cloud.tests.MockSyncServiceBackend', name='MockVPS'))

        request_with_id = controller.service_request(ServiceRequest(
            'MockVPS',
            {
                'opname1': 'optval1',
                'opname2': 'optval2',
                'opname3': 'optval3',
            })
        )

        # print request_with_id.options

    def test_controller_wrong_service_request(self):
        controller = CloudController()

        controller.register_service('cloud.tests.MockSyncServiceBackend', name='MockVPS')

        try:
            # passing wrong service name
            request_with_id = controller.service_request(ServiceRequest(
                'MockVPS1',
                {
                    'opname1': 'optval1',
                    'opname2': 'optval2',
                    'opname3': 'optval3',
                })
            )

            self.fail("Waiting for the ObjectDoesNotExist exception.")
        except ObjectDoesNotExist:
            pass
