import json

from django.db import models
from django.db.models.loading import get_model
from django.utils import timezone
from django.core import exceptions as djexceptions


class ResourcesWithOptions(models.Manager):
    def active(self, *args, **kwargs):
        return super(ResourcesWithOptions, self).get_queryset() \
            .filter(*args, **kwargs) \
            .exclude(status=Resource.STATUS_DELETED)

    def filter(self, *args, **kwargs):
        """
        Search for Resources using Options (only in active resources)
        search_fields keys can be specified with lookups:
        https://docs.djangoproject.com/en/1.7/ref/models/querysets/#field-lookups

        Resource fields has higher priority than ResourceOption fields

        convert field__lookup = value to:
            resourceoption__name__exact = field
            resourceoption__value__lookup = value
        """

        search_fields = kwargs

        query = {}

        for field_name_with_lookup in search_fields.keys():
            field_name = field_name_with_lookup.split('__')[0]

            if hasattr(Resource(), field_name):
                query[field_name_with_lookup] = search_fields[field_name_with_lookup]
            else:
                if hasattr(ResourceOption(), field_name):
                    query['resourceoption__%s' % field_name_with_lookup] = search_fields[field_name_with_lookup]
                else:
                    query['resourceoption__name__exact'] = field_name
                    query[field_name_with_lookup.replace(field_name, 'resourceoption__value')] = \
                        search_fields[field_name_with_lookup]

        return super(ResourcesWithOptions, self).get_queryset().filter(*args, **query).distinct()


class ResourceOption(models.Model):
    """
    Resource option with support for namespaces. Resources is able to have different options and
    client can search by them.
    """

    class StringValue:
        _value = ''

        def __init__(self, value):
            self._value = str(value)

        def get_value(self):
            return self._value

        def __str__(self):
            return self._value

    class IntegerValue(StringValue):
        def get_value(self):
            return int(self._value)

    class FloatValue(StringValue):
        def get_value(self):
            return float(self._value)

    class DictionaryValue(StringValue):
        def __init__(self, value):
            self._value = value

            if isinstance(value, dict):
                self._value = json.dumps(value)

        def get_value(self):
            return json.loads(self._value, encoding='utf-8', parse_float=True, parse_int=True, parse_constant=True)

    FORMAT_DICT = 'dict'
    FORMAT_INT = 'int'
    FORMAT_FLOAT = 'float'
    FORMAT_STRING = 'string'
    FORMAT_CHOICES = (
        (FORMAT_DICT, 'Dictionary string'),
        (FORMAT_INT, 'Integer value'),
        (FORMAT_FLOAT, 'Float value'),
        (FORMAT_STRING, 'String value'),
    )
    FORMAT_HANDLERS = {
        FORMAT_DICT: DictionaryValue,
        FORMAT_INT: IntegerValue,
        FORMAT_FLOAT: FloatValue,
        FORMAT_STRING: StringValue,
    }

    resource = models.ForeignKey('Resource')
    name = models.CharField(max_length=155, db_index=True)
    namespace = models.CharField(max_length=155, db_index=True, default='')
    value = models.TextField('Option value')
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)
    format = models.CharField(max_length=25, db_index=True, choices=FORMAT_CHOICES, default=FORMAT_STRING)

    format_handler = None

    class Meta:
        db_table = "resource_options"

    def __init__(self, *args, **kwargs):
        super(ResourceOption, self).__init__(*args, **kwargs)
        self.format_handler = self.FORMAT_HANDLERS[self.format]

    @staticmethod
    def save_value(value, format):
        assert format is not None, "Parameter 'format' must be defined."

        return str(ResourceOption.FORMAT_HANDLERS[format](value))

    @staticmethod
    def guess_format(value):
        ret_format = ResourceOption.FORMAT_STRING

        if isinstance(value, int):
            ret_format = ResourceOption.FORMAT_INT
        elif isinstance(value, float):
            ret_format = ResourceOption.FORMAT_FLOAT
        elif isinstance(value, dict):
            ret_format = ResourceOption.FORMAT_DICT

        return ret_format

    def get_value(self, typed=True):
        """
        Returns stored option value.
        If typed=True, then value is converted to object of specific format.
        """
        return self.format_handler(self.value).get_value() if typed else self.value

    def __str__(self):
        return "%s = '%s'..." % (self.name, self.value[:15])


class Resource(models.Model):
    """
    Generic resource representation. Support for search by ResourceOptions.
    """
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
    type = models.CharField(max_length=155, db_index=True, default='Resource')
    status = models.CharField(max_length=25, db_index=True, choices=STATUS_CHOICES, default=STATUS_FREE)
    created_at = models.DateTimeField('Date created', db_index=True, default=timezone.now())
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)

    objects = ResourcesWithOptions()

    class Meta:
        db_table = "resources"

    def get_proxy(self):
        return get_model(self._meta.app_label, self.type)

    def set_option(self, name, value, format=None, namespace=''):
        """
        Set resource option. If format is omitted, then format is guessed from value type.
        """

        assert self._is_saved(), "Resource must be saved before setting options"
        assert name is not None, "Parameter 'name' must be defined."

        if not format:
            format = ResourceOption.guess_format(value)

        query = dict(
            name=name,
            namespace=namespace,
            defaults=dict(
                format=format,
                value=ResourceOption.save_value(value, format),
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
        except djexceptions.ObjectDoesNotExist:
            return False

        return True

    def get_option_value(self, name, namespace='', default=''):
        option_value = default
        try:
            option = self.get_option(name, namespace=namespace)
            option_value = option.get_value()
        except djexceptions.ObjectDoesNotExist:
            option_value = default

        return option_value

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.type = self.__class__.__name__

        return super(Resource, self).save(force_insert, force_update, using, update_fields)

    def _is_saved(self):
        return self.id is not None

    def _field_exists(self, name):
        assert name is not None, "Parameter 'name' must be defined."

        try:
            self._meta.get_field_by_name(name)

            return True
        except models.FieldDoesNotExist:
            return False

    def __str__(self):
        return "%d\t%s\t%s (%s, %s)" % (self.pk, self.type, self.status, self.created_at, self.updated_at)


class ResourcePool(Resource):
    """
    Resource grouping.
    """

    class Meta:
        proxy = True

    def _get_pool_name(self):
        return self.get_option_value('name', 'ResourcePool', None)

    def _set_pool_name(self, value):
        self.set_option('name', value, namespace='ResourcePool')

    name = property(fget=_get_pool_name, fset=_set_pool_name)
