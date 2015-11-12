from __future__ import unicode_literals

import json

from django.db import models
from django.utils import timezone

from cmdb.lib import loader


class CloudTaskTracker(models.Model):
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

    task_class = models.CharField('Python class of the cloud task.', max_length=55, db_index=True)
    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)
    status = models.CharField(max_length=25, db_index=True, choices=STATUS_CHOICES, default=STATUS_NEW)

    context_json = models.TextField('Cloud command context.')
    return_json = models.TextField('Cloud command return data.')

    error = models.TextField('Error message in case of failed state.')

    def __unicode__(self):
        return "%s %s (%s)" % (self.id, self.task_class, self.status)

    @property
    def is_failed(self):
        return self.status == self.STATUS_FAILED

    @property
    def is_ok(self):
        return self.status == self.STATUS_SUCCESS

    @property
    def is_progress(self):
        return self.status == self.STATUS_PROGRESS

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
        assert value

        self.return_json = json.dumps(value)

    def progress(self):
        self.updated_at = timezone.now()
        self.status = self.STATUS_PROGRESS
        self.save()

    def success(self, return_data=None):
        if not return_data:
            return_data = {}

        self.return_data = return_data
        self.status = self.STATUS_SUCCESS
        self.save()

    def fail(self, error_message=None):
        if not error_message:
            error_message = ''

        self.error = error_message
        self.status = self.STATUS_FAILED
        self.save()

    @property
    def task(self):
        tracked_task_class = loader.get_class(self.task_class)
        wrapped_task = tracked_task_class(self, **self.context)
        return wrapped_task

    @staticmethod
    def track(cloud_task_class, **context):
        assert cloud_task_class

        full_cloud_task_class_name = "%s.%s" % (cloud_task_class.__module__, cloud_task_class.__name__)

        task_tracker = CloudTaskTracker(task_class=full_cloud_task_class_name)
        task_tracker.context = context
        task_tracker.save()

        return task_tracker

    def wait_to_end(self):
        result_data = self.task.wait_to_end()

        self.success(result_data)

        return result_data

    def ready(self):
        return self.task.ready()


class CloudConfig(object):
    """
    Entry point for the CMDB data query.
    """
    pass
