from django.db import models
from django.utils import timezone
from django.core import exceptions


class ActiveResources(models.Manager):
    def get_query_set(self):
        return super(ActiveResources, self).get_queryset().exclude(status=Resource.STATUS_DELETED)


class ResourceOption(models.Model):
    FORMAT_JSON = 'json'
    FORMAT_INT = 'int'
    FORMAT_FLOAT = 'float'
    FORMAT_STRING = 'string'
    FORMAT_CHOICES = (
        (FORMAT_JSON, 'JSON string'),
        (FORMAT_INT, 'Integer value'),
        (FORMAT_FLOAT, 'Float value'),
        (FORMAT_STRING, 'String value'),
    )

    resource = models.ForeignKey('Resource')
    name = models.CharField(max_length=155, db_index=True)
    namespace = models.CharField(max_length=155, db_index=True, default='')
    value = models.TextField('Option value')
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)
    format = models.CharField(max_length=25, db_index=True, choices=FORMAT_CHOICES, default=FORMAT_STRING)

    class Meta:
        db_table = "resource_options"

    def __str__(self):
        return "%s = '%s'..." % (self.name, self.value[:15])


class Resource(models.Model):
    TYPE_GENERIC = 'generic'
    TYPE_CHOICES = (
        (TYPE_GENERIC, 'Generic resource'),
    )

    STATUS_FREE = 'free'
    STATUS_INUSE = 'inuse'
    STATUS_FAILED = 'failed'
    STATUS_LOCKED = 'locked'
    STATUS_DELETED = 'deleted'
    STATUS_CHOICES = (
        (STATUS_FREE, 'Free to use'),
        (STATUS_INUSE, 'Used by someone'),
        (STATUS_FAILED, 'Failed resource'),
        (STATUS_LOCKED, 'Locked by business'),
        (STATUS_DELETED, 'Deleted'),
    )

    parent = models.ForeignKey("self", default=0)
    type = models.CharField(max_length=155, db_index=True, choices=TYPE_CHOICES, default=TYPE_GENERIC)
    status = models.CharField(max_length=25, db_index=True, choices=STATUS_CHOICES, default=STATUS_FREE)
    created_at = models.DateTimeField('Date created', db_index=True, default=timezone.now())
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)

    active = ActiveResources()
    objects = models.Manager()

    class Meta:
        db_table = "resources"

    def set_option(self, name, value, format=ResourceOption.FORMAT_STRING, namespace=''):
        if not name:
            raise exceptions.ValueError('name')

        query = dict(
            name=name,
            namespace=namespace,
            defaults=dict(
                format=format,
                value=value,
                namespace=namespace
            )
        )

        self.resourceoption_set.update_or_create(**query)

    def get_option(self, name, namespace=''):
        query = dict(
            name=name,
            namespace=namespace
        )

        return self.resourceoption_set.get(**query)

    def has_option(self, name, namespace=''):
        try:
            self.get_option(name, namespace=namespace)
        except exceptions.ObjectDoesNotExist:
            return False

        return True

    def get_option_value(self, name, namespace='', default=''):
        option_value = default
        try:
            option = self.get_option(name, namespace=namespace)
            option_value = option.value
        except exceptions.ObjectDoesNotExist:
            option_value = default

        return option_value

    def _field_exists(self, name):
        if not name:
            raise exceptions.ValueError("store_path")

        try:
            self._meta.get_field_by_name(name)

            return True
        except models.FieldDoesNotExist:
            return False

    def __str__(self):
        return "%d\t%s\t%s (%s, %s)" % (self.pk, self.type, self.status, self.created_at, self.updated_at)
