from __future__ import unicode_literals

from cloud.provisioning import HypervisorBackend, CloudTask


class CreateMockVpsTask(CloudTask):
    def execute(self, tracker):
        self.result = {'result': self.context}


class MockHypervisorBackend(HypervisorBackend):
    """
    Backend is just the factory for the commands.
    """

    def create_vps(self, ram, cpu, hdd, success=True):
        return self.send_task(CreateMockVpsTask(ram=ram, cpu=cpu, hdd=hdd, success=success))

    def create_vps_sync(self, ram, cpu, hdd, success=True):
        task = CreateMockVpsTask(ram=ram, cpu=cpu, hdd=hdd, success=success)
        task_tracker = self.send_task(task)

        if success:
            task_tracker.success(task.result)
        else:
            task_tracker.fail('Some error occured.')

        return task_tracker
