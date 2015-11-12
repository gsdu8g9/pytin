from __future__ import unicode_literals

from cloud.provisioning import HypervisorBackend, CloudTask


class CreateMockVpsTask(CloudTask):
    def execute(self):
        tracker_context = self.tracker.context
        tracker_context['result'] = {'some': 'data'}

        self.tracker.context = tracker_context
        self.tracker.save()

    def wait_to_end(self):
        return self.context['result']


class MockHypervisorBackend(HypervisorBackend):
    """
    Backend is just the factory for the commands.
    """

    def create_vps(self, ram, cpu, hdd, success=True):
        return self.send_task(CreateMockVpsTask, ram=ram, cpu=cpu, hdd=hdd, success=success)
