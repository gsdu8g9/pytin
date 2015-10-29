from __future__ import unicode_literals

import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from cmdb.lib import loader


class ServiceRequest(object):
    """
    Basic object that incapsulates the service request.
    """

    def __init__(self, target, options):
        assert target

        if not options:
            options = {}

        self.request_id = 0
        self.target = target
        self.options = options
        self.response = {}


class VpsServiceRequest(ServiceRequest):
    def __init__(self, target, tech, vcpu, ram, hdd, template):
        pass


class ServiceRequestTracker(models.Model):
    STATUS_PROGRESS = 'progress'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_PROGRESS, 'Request in progress.'),
        (STATUS_SUCCESS, 'Request completed.'),
        (STATUS_FAILED, 'Request failed.'),
    )

    target = models.CharField('Target cloud service name.', max_length=55, db_index=True)
    type = models.CharField('Request type.', max_length=55, db_index=True)
    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)

    status = models.CharField(max_length=25, db_index=True, choices=STATUS_CHOICES, default=STATUS_PROGRESS)

    json_options = models.TextField('Comment text')
    json_response = models.TextField('Comment text')

    def __unicode__(self):
        return "%s %s (%s)" % (self.id, self.target, self.implementor)

    @property
    def options(self):
        return json.loads(self.json_options)

    @options.setter
    def options(self, value):
        assert value

        self.json_options = json.dumps(value)


class CloudService(models.Model):
    """
    Class representing Cloud Service, such as Hosting or VPS.
    """
    name = models.CharField('Service name.', unique=True, max_length=25, db_index=True)
    implementor = models.CharField('Implementation class name.', max_length=155, default=None, db_index=False)
    active = models.BooleanField('Set if service is active.', default=False, db_index=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.implementor)

    @property
    def backend(self):
        """
        Return the service implementation.
        """
        return loader.get_class(self.implementor)


class CloudController(object):
    """
    Controlling known cloud services.
    """

    def registered_services(self):
        """
        Return the names of the registered services in cloud.
        """
        return CloudService.objects.filter(active=True)

    def register_service(self, implementor_class_name, name=None):
        """
        Registers the new cloud service. Backend must be already configured.
        :param implementor_class: Service implementation class.
        :return: True - if regstered, False - if exists and was updated.
        """

        implementor_class = loader.get_class(implementor_class_name)

        service, created = CloudService.objects.update_or_create(
            implementor=implementor_class_name,
            defaults=dict(
                name=name if name else implementor_class.__name__,
                active=True
            )
        )

        return created

    def get_service(self, name):
        """
        Returns the registered service implementation
        :param name: Name of the cloud service.
        :return: Instance of the cloud service implementation.
        """
        assert name

        cloud_service = CloudService.objects.get(name__exact=name)

        return cloud_service.backend()

    def service_request(self, service_request):
        """
        Perform service request on the CloudService.
        :param service_request: ServiceRequest object filled with parameters.
        :return: ServiceRequest with filled response data.
        """
        assert service_request

        # here we can log and store this request to the DB.
        request = ServiceRequestLog.objects.create(
            target=service_request.target,
            type=service_request.__class__.__name__,
            json_options=json.dumps(service_request.options)
        )

        try:
            self.get_service(service_request.target).request(service_request)
        except models.ObjectDoesNotExist:
            raise models.ObjectDoesNotExist(_("Service '%s' does not exists." % service_request.target))

        return request
