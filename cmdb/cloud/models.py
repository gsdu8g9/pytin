import datetime

from django.db import models
from django.utils import timezone

from resources.models import Resource

HEARTBEAT_PERIOD_SEC = 60


class ExnendedNodeManager(models.Manager):
    pass


class CloudController(object):
    pass


class CloudNode(models.Model):
    """
    Class representing Cloud Node. Track its heartbeat.
    """
    resource = models.OneToOneField(Resource, default=None, db_index=True)
    service = models.ForeignKey('CloudService', default=0, db_index=True)
    heartbeat_last = models.DateTimeField('Last received heartbeat', db_index=True, null=True)
    fail_count = models.IntegerField('Number of registered errors', default=0)

    objects = ExnendedNodeManager()

    def __unicode__(self):
        return "%s [F:%s]" % (unicode(self.resource), self.fail_count)

    def heartbeat(self):
        """
        Update heartbeat_last property.
        :return:
        """

        last_seen = timezone.now() - datetime.timedelta(seconds=HEARTBEAT_PERIOD_SEC)
        if self.heartbeat_last and self.heartbeat_last <= last_seen:
            self.fail_count += 1

        self.heartbeat_last = timezone.now()
        self.save()


class CloudService(models.Model):
    """
    Class representing Cloud Service, such as Hosting or VPS.
    """
    name = models.CharField('Service name.', max_length=25, default=None, db_index=True)
    implementor = models.CharField('Implementation class name.', max_length=155, default=None, db_index=False)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.implementor)

    def add_node(self, cloud_node):
        """
        Add the cloud service node
        :param cloud_node:
        :return:
        """
        cloud_node.service = self
        cloud_node.save()

        return cloud_node

    @property
    def nodes(self):
        return CloudNode.objects.filter(service=self)
