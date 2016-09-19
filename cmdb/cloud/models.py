from __future__ import unicode_literals

import json
import time

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from assets.models import Server
from cmdb.lib import loader
from cmdb.settings import logger
from resources.models import Resource


class TaskTrackerStatus(object):
    STATUS_NEW = 'new'
    STATUS_PROGRESS = 'progress'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_NEW, 'Request created.'),
        (STATUS_PROGRESS, 'Request in progress.'),
        (STATUS_SUCCESS, 'Request completed.'),
        (STATUS_FAILED, 'Request failed.'),
    )


@python_2_unicode_compatible
class CloudTaskTracker(models.Model):
    task_class = models.CharField('Python class of the cloud task.', max_length=55, db_index=True)
    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)
    status = models.CharField(max_length=25, db_index=True, choices=TaskTrackerStatus.STATUS_CHOICES,
                              default=TaskTrackerStatus.STATUS_NEW)

    context_json = models.TextField('Cloud command context.')
    return_json = models.TextField('Cloud command return data.')

    error = models.TextField('Error message in case of failed state.')

    def __str__(self):
        return "%s %s (%s)" % (self.id, self.task_class, self.status)

    @property
    def is_failed(self):
        return self.status == TaskTrackerStatus.STATUS_FAILED

    @property
    def is_success(self):
        return self.status == TaskTrackerStatus.STATUS_SUCCESS

    @property
    def is_progress(self):
        return self.status == TaskTrackerStatus.STATUS_PROGRESS

    @property
    def is_new(self):
        return self.status == TaskTrackerStatus.STATUS_NEW

    @property
    def is_ready(self):
        return self.is_failed or self.is_success

    @property
    def context(self):
        return json.loads(self.context_json)

    @context.setter
    def context(self, value):
        assert value

        self.context_json = json.dumps(value)

    @property
    def return_data(self):
        return json.loads(self.return_json)

    @return_data.setter
    def return_data(self, value):
        self.return_json = json.dumps(value)

    def progress(self):
        self.updated_at = timezone.now()
        self.status = TaskTrackerStatus.STATUS_PROGRESS
        self.save()

    def success(self, return_data=None):
        if not return_data:
            return_data = {}

        self.return_data = return_data
        self.status = TaskTrackerStatus.STATUS_SUCCESS
        self.save()

    def failed(self, error_message=None):
        if not error_message:
            error_message = ''

        self.error = error_message
        self.status = TaskTrackerStatus.STATUS_FAILED
        self.save()

    @property
    def task(self):
        tracked_task_class = loader.get_class(self.task_class)
        wrapped_task = tracked_task_class(self, **self.context)
        return wrapped_task

    @staticmethod
    def execute(cloud_task_class, **context):
        assert cloud_task_class

        full_cloud_task_class_name = "%s.%s" % (cloud_task_class.__module__, cloud_task_class.__name__)

        task_tracker = CloudTaskTracker(task_class=full_cloud_task_class_name)
        task_tracker.context = context
        task_tracker.save()

        task_tracker.task.execute()

        return task_tracker

    @staticmethod
    def get(tracker_id):
        assert tracker_id > 0

        return CloudTaskTracker.objects.get(pk=tracker_id)

    @staticmethod
    def find(**query):
        assert id > 0

        return CloudTaskTracker.objects.filter(**query)

    def poll(self):
        if self.is_success:
            return self.return_data

        if self.is_failed:
            return self.error

        try:
            ready, result_data = self.task.poll()
            if ready:
                self.success(result_data)
            else:
                logger.info("progress: %s" % result_data)
                self.progress()

            return result_data
        except Exception as ex:
            self.failed(ex.message)
            raise ex

    def wait(self):
        if self.is_success:
            return self.return_data

        if self.is_failed:
            return self.error

        try:
            last_data = ''
            while True:
                ready, result_data = self.task.poll()
                if ready:
                    self.success(result_data)
                    return result_data

                # in progress
                self.progress()

                if last_data != result_data:
                    last_data = result_data
                    logger.info("progress: %s" % last_data)

                time.sleep(1)
        except Exception as ex:
            self.failed(ex.message)
            raise ex


class CmdbCloudConfig(object):
    """
    Entry point for the CMDB data query.

    Every hypervisor node in CMDB must have options:
        role = hypervisor.
        hypervisor_driver (kvm, openvz, etc).
        agentd_taskqueue: task queue used to feed the specific agent.
        agentd_heartbeat: last heartbeat time.
    """
    TECH_HV_KVM = 'kvm'
    TECH_HV_OPENVZ = 'openvz'

    task_tracker = CloudTaskTracker

    def get_hypervisors(self, **query):
        """
        Returns the known hypervisors from the cloud. Query can contain hypervisor_driver option.
        :return:
        """

        query['role'] = 'hypervisor'
        query['status'] = Resource.STATUS_INUSE

        return Server.active.filter(**query).order_by('id')
