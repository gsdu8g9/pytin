from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from cloud.models import CloudTaskTracker


class CloudTask(object):
    def __init__(self, tracker, **context):
        assert tracker

        self.tracker = tracker
        self.context = context
        self.result = {}

    def execute(self):
        raise Exception(_("Not implemented."))

    def poll(self):
        raise Exception(_("Not implemented."))

    def wait_to_end(self):
        raise Exception(_("Not implemented."))


class CloudBackend(object):
    """
    Specific Backend implementation. This is the factory for the service instances.
    """

    def __init__(self, cloud):
        assert cloud
        self.cloud = cloud

    def send_task(self, cloud_task_class, **kwargs):
        """
        Submit task to the backend. Returns CloudTaskTracker.
        """
        assert cloud_task_class

        tracker = CloudTaskTracker.track(cloud_task_class, **kwargs)

        tracker.task.execute()

        return tracker


class HypervisorBackend(CloudBackend):
    def create_vps(self, **options):
        raise Exception(_("Not implemented."))

    def start_vps(self, vmid, **options):
        raise Exception(_("Not implemented."))

    def stop_vps(self, vmid, **options):
        raise Exception(_("Not implemented."))


class CloudServiceHandler(object):
    """
    CloudService instance manager. Handles specific service instance operations.
    """

    def __init__(self, backend, **options):
        assert backend

        self.backend = backend
        self.options = options

    def start(self):
        pass

    def stop(self):
        pass

    def destroy(self):
        pass

    def modify(self, **options):
        pass


class VpsHandler(CloudServiceHandler):
    def add_ip(self, ip):
        pass

    def delete_ip(self, ip):
        pass


class HostingHandler(CloudServiceHandler):
    def get_usage(self):
        pass

    def get_info(self):
        pass
