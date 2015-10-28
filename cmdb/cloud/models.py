from django.db import models

from cmdb.lib import loader


class CloudService(models.Model):
    """
    Class representing Cloud Service, such as Hosting or VPS.
    """
    name = models.CharField('Service name.', max_length=25, default=None, db_index=True)
    implementor = models.CharField('Implementation class name.', max_length=155, default=None, db_index=False)
    active = models.BooleanField('Set if service is active.', default=False, db_index=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.implementor)

    @property
    def implementation(self):
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
        services = []
        for svc in CloudService.objects.filter(active=True):
            services.append(svc.name)

        return services

    def register_service(self, service_class):
        """
        Registers the new cloud service.
        :param service_class: Service implementation class.
        :return: True - if regstered, False - if exists and was updated.
        """
        service, created = CloudService.objects.update_or_create(
            implementor=service_class.__name__,
            default=dict(
                name=service_class.NAME
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

        return cloud_service.implementation()
