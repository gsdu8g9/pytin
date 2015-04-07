import json

from django.db import models
from django.core import exceptions as djexceptions
from django.apps import apps


class ModelFieldChecker:
    def __init__(self):
        pass

    @staticmethod
    def is_model_field(class_type, name):
        """
        Check if field name belongs to model fields
        """
        assert name is not None, "Parameter 'name' must be defined."
        assert issubclass(class_type, models.Model), "Class 'class_type' must be the subclass of models.Model."

        try:
            return name in [f.name for f in class_type._meta.fields]
        except models.FieldDoesNotExist:
            return False


class ResourcesWithOptionsManager(models.Manager):
    def active(self, *args, **kwargs):
        return self.filter(*args, **kwargs).exclude(status=Resource.STATUS_DELETED)

    def filter(self, *args, **kwargs):
        """
        Search for Resources using Options (only in active resources)
        search_fields keys can be specified with lookups:
        https://docs.djangoproject.com/en/1.7/ref/models/querysets/#field-lookups

        Resource fields has higher priority than ResourceOption fields
        """

        search_fields = kwargs

        # if filter is called for proxy model, filter by proxy type
        if self.model.__name__ != Resource.__name__:
            search_fields['type'] = self.model.__name__

        query = {}

        for field_name_with_lookup in search_fields.keys():
            field_name = field_name_with_lookup.split('__')[0]

            if ModelFieldChecker.is_model_field(Resource, field_name):
                query[field_name_with_lookup] = search_fields[field_name_with_lookup]
            else:
                if ModelFieldChecker.is_model_field(ResourceOption, field_name):
                    query['resourceoption__%s' % field_name_with_lookup] = search_fields[field_name_with_lookup]
                else:
                    # convert field__lookup = value to:
                    # resourceoption__name__exact = field
                    # resourceoption__value__lookup = value
                    query['resourceoption__name__exact'] = field_name
                    query[field_name_with_lookup.replace(field_name, 'resourceoption__value')] = \
                        search_fields[field_name_with_lookup]

        return super(ResourcesWithOptionsManager, self).get_queryset().filter(*args, **query).distinct()


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
    updated_at = models.DateTimeField('Date updated', auto_now_add=True, db_index=True)
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
    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)

    objects = ResourcesWithOptionsManager()

    class Meta:
        db_table = "resources"

    def __str__(self):
        return "%d\t%s\t%s" % (self.id, self.type, self.status)

    @classmethod
    def create(cls, **kwargs):
        """
        Create new model of calling class type. Model fields are only checked for Resource() model
        to not interfere with proxy model properties.
        :param kwargs: model parameters with model options
        :return: created model
        """
        model_fields = {}
        option_fields = {}

        for field_name in kwargs.keys():
            if ModelFieldChecker.is_model_field(Resource, field_name):
                model_fields[field_name] = kwargs[field_name]
            else:
                option_fields[field_name] = kwargs[field_name]

        new_object = cls(**model_fields)
        new_object.save()
        for option_field in option_fields.keys():
            if hasattr(new_object, option_field):
                setattr(new_object, option_field, option_fields[option_field])
            else:
                new_object.set_option(option_field, option_fields[option_field], namespace=new_object.type)

        return new_object

    def get_proxy(self):
        return apps.get_model(self._meta.app_label, self.type)

    def lock(self):
        self.status = self.STATUS_LOCKED

    def use(self):
        self.status = self.STATUS_INUSE

    def fail(self):
        self.status = self.STATUS_FAILED

    def free(self):
        self.status = self.STATUS_FREE

    @property
    def is_locked(self):
        return self.status == self.STATUS_LOCKED

    @property
    def is_used(self):
        return self.status == self.STATUS_INUSE

    @property
    def is_failed(self):
        return self.status == self.STATUS_FAILED

    @property
    def is_free(self):
        return self.status == self.STATUS_FREE

    def set_option(self, name, value, format=None, namespace=''):
        """
        Set resource option. If format is omitted, then format is guessed from value type.
        If namespace is omitted, then namespace = calling class name
        """

        assert self._is_saved(), "Resource must be saved before setting options"
        assert name is not None, "Parameter 'name' must be defined."

        if not format:
            format = ResourceOption.guess_format(value)

        if not namespace:
            namespace = self.type

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
        assert name is not None, "Parameter 'name' must be defined."

        if not namespace:
            namespace = self.type

        query = dict(
            name=name,
            namespace=namespace
        )

        return self.resourceoption_set.get(**query)

    def has_option(self, name, namespace=''):
        assert name is not None, "Parameter 'name' must be defined."

        try:
            self.get_option(name, namespace=namespace)
        except djexceptions.ObjectDoesNotExist:
            return False

        return True

    def get_option_value(self, name, namespace='', default=''):
        assert name is not None, "Parameter 'name' must be defined."

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


class ResourcePool(Resource):
    """
    Resource grouping.
    """

    class Meta:
        proxy = True

    @property
    def name(self):
        return self.get_option_value('name', 'ResourcePool', None)

    @name.setter
    def name(self, value):
        self.set_option('name', value, namespace='ResourcePool')

    @property
    def usage(self):
        raise NotImplementedError()

