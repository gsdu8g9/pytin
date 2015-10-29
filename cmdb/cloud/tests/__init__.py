from __future__ import unicode_literals

from cloud.provisioning import CloudServiceImpl


class MockSyncServiceBackend(CloudServiceImpl):
    def request(self, service_request):
        service_request.options['processed'] = 1

        return service_request
