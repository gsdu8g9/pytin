import json

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core import exceptions as djexceptions
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.datetime_safe import datetime


class ModelFieldChecker:
    """
    Utility class to query Django model fields.
    """
    builtin = ['pk']

    def __init__(self):
        pass

    @staticmethod
    def is_field_or_property(object, name):
        """
        Check if field name belongs to model fields or properties
        """
        assert name is not None, "Parameter 'name' must be defined."
        assert issubclass(object.__class__, models.Model), "Class 'class_type' must be the subclass of models.Model."

        return ModelFieldChecker.is_model_field(object.__class__, name) or hasattr(object, name)

    @staticmethod
    def is_model_field(class_type, name):
        """
        Check if field name belongs to model fields
        """
        assert name is not None, "Parameter 'name' must be defined."
        assert issubclass(class_type, models.Model), "Class 'class_type' must be the subclass of models.Model."

        if name in ModelFieldChecker.builtin:
            return True

        try:
            return name in [f.name for f in class_type._meta.fields]
        except models.FieldDoesNotExist:
            return False


class SubclassingQuerySet(QuerySet):
    def __getitem__(self, k):
        result = super(SubclassingQuerySet, self).__getitem__(k)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result

    def __iter__(self):
        for item in super(SubclassingQuerySet, self).__iter__():
            yield item.as_leaf_class()

    def filter(self, *args, **kwargs):
        """
        Search for Resources using Options
        search_fields keys can be specified with lookups:
        https://docs.djangoproject.com/en/1.7/ref/models/querysets/#field-lookups

        Resource fields has higher priority than ResourceOption fields
        """

        search_fields = kwargs

        # if filter is called for proxy model, filter by proxy type
        if self.model != Resource:
            search_fields['type'] = self.model.__name__

        query = {}
        related_query = []

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
                    field_related_value = field_name_with_lookup.replace(field_name, 'resourceoption__value')
                    related_query.append(
                        {'resourceoption__name__exact': field_name,
                         field_related_value: search_fields[field_name_with_lookup]}
                    )

        # Chaining queries
        query_set = super(SubclassingQuerySet, self).filter(*args, **query)
        for related_query_item in related_query:
            query_set = super(SubclassingQuerySet, query_set).filter(*args, **related_query_item)

        return query_set.distinct()

    def get(self, *args, **kwargs):
        return super(SubclassingQuerySet, self).get(*args, **kwargs).as_leaf_class()


class ResourcesWithOptionsManager(models.Manager):
    """
    Query manager with support for query by options.
    """

    def get_queryset(self):
        return SubclassingQuerySet(self.model)

    def active(self, *args, **kwargs):
        """
        Search for Resources with Options (only on active resources)
        search_fields keys can be specified with lookups:
        https://docs.djangoproject.com/en/1.7/ref/models/querysets/#field-lookups

        Resource fields has higher priority than ResourceOption fields
        """
        return self.filter(*args, **kwargs).exclude(status=Resource.STATUS_DELETED)


class ResourceOption(models.Model):
    """
    Resource option with support for namespaces. Resources is able to have different options and
    client can search by them.
    """

    class StringValue:
        _value = ''

        def __init__(self, value):
            self._value = str(value)

        def __str__(self):
            return "'%s'" % self.typed_value()

        def typed_value(self):
            return self._value

        def raw_value(self):
            return self._value

    class IntegerValue(StringValue):
        def __str__(self):
            return "%d" % self.typed_value()

        def typed_value(self):
            return int(self._value)

    class FloatValue(StringValue):
        def __str__(self):
            return "%f" % self.typed_value()

        def typed_value(self):
            return float(self._value)

    class DictionaryValue(StringValue):
        def __init__(self, value):
            self._value = value

            if isinstance(value, dict):
                self._value = json.dumps(value)

        def __str__(self):
            return "'%s'" % self.typed_value()

        def typed_value(self):
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
    updated_at = models.DateTimeField('Date updated', auto_now_add=True, db_index=True)
    format = models.CharField(max_length=25, db_index=True, choices=FORMAT_CHOICES, default=FORMAT_STRING)
    value = models.TextField('Option value')

    value_format_handler = None

    class Meta:
        db_table = "resource_options"

    def __init__(self, *args, **kwargs):
        super(ResourceOption, self).__init__(*args, **kwargs)
        self.format = self.guess_format(self.value) if not self.format else self.format
        self.value_format_handler = self.FORMAT_HANDLERS[self.format]
        self.value = self._value_handler().raw_value()

    def __str__(self):
        return "%s:%s = %s" % (self.namespace, self.name, self._value_handler())

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        self.format = self.guess_format(self.value) if not self.format else self.format

        super(ResourceOption, self).save(force_insert, force_update, using, update_fields)

    def _value_handler(self):
        return self.value_format_handler(self.value)

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

    def typed_value(self):
        return self._value_handler().typed_value()


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

    parent = models.ForeignKey("self", default=None, db_index=True, null=True)
    name = models.CharField(max_length=155, db_index=True, default='Resource')
    type = models.CharField(max_length=155, db_index=True, default='Resource')
    content_type = models.ForeignKey(ContentType, editable=False, null=True)
    status = models.CharField(max_length=25, db_index=True, choices=STATUS_CHOICES, default=STATUS_FREE)
    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)
    last_seen = models.DateTimeField('Date last seen', db_index=True, default=datetime.now)

    objects = ResourcesWithOptionsManager()

    class Meta:
        db_table = "resources"

    def __str__(self):
        return self.name

    def __contains__(self, item):
        return Resource.objects.active(pk=item.id, parent=self).exists()

    def __add__(self, other):
        """
        Add child to the Resource object
        """
        assert isinstance(other, Resource), "Can't add object that is not a Resource"
        assert self.can_add(other), "Child resource can't be added to this Resource"

        other.parent = self
        other.save()

        return self

    def __sub__(self, other):
        """
        Remove child from the Resource object
        """
        assert isinstance(other, Resource), "Can't sub object that is not a Resource"

        other.parent = None
        other.save()

        return self

    def __iter__(self):
        """
        Iterate through resource childs
        """
        for resource in Resource.objects.active(parent=self):
            yield resource

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

        need_save = False
        for option_field in option_fields.keys():
            # if model have property with the given name, then set it via setattr,
            # because of possible custom behaviour
            if hasattr(new_object, option_field):
                setattr(new_object, option_field, option_fields[option_field])
                need_save = True
            else:
                new_object.set_option(option_field, option_fields[option_field], namespace='')

        if need_save:
            new_object.save()

        return new_object

    def cast_type(self, new_class_type):
        assert new_class_type

        self.content_type = ContentType.objects.get_for_model(new_class_type,
                                                              for_concrete_model=not self._meta.proxy)

        self.type = new_class_type.__name__

        super(Resource, self).save()
        new_object = self.as_leaf_class()

        return new_object

    def touch(self, recursive=False):
        """
        Update last_seen date of the resource
        """

        if recursive:
            for child in self:
                child.last_seen = timezone.now()
                child.save()

        self.last_seen = timezone.now()
        self.save()

    def lock(self, cascade=False):
        self._change_status(self.STATUS_LOCKED, 'lock', cascade)

    def use(self, cascade=False):
        self._change_status(self.STATUS_INUSE, 'use', cascade)

    def fail(self, cascade=False):
        self._change_status(self.STATUS_FAILED, 'fail', cascade)

    def free(self, cascade=False):
        self._change_status(self.STATUS_FREE, 'free', cascade)

    def delete(self, cascade=False, purge=False):
        """
        Override Model .delete() method. Instead of actual deleting object from the DB
        set status Deleted.
        """
        if purge:
            super(Resource, self).delete()
        else:
            self._change_status(self.STATUS_DELETED, 'delete', cascade)

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

    @property
    def is_deleted(self):
        return self.status == self.STATUS_DELETED

    def set_option(self, name, value, format=None, namespace=''):
        """
        Set resource option. If format is omitted, then format is guessed from value type.
        """

        assert self.is_saved(), "Resource must be saved before setting options"
        assert name is not None, "Parameter 'name' must be defined."

        query = dict(
            name=name,
            namespace=namespace,
            defaults=dict(
                value=value,
                format=format,
                namespace=namespace
            )
        )

        self.resourceoption_set.update_or_create(**query)

    def get_options(self, namespace=''):
        query = dict(
            namespace=namespace
        )

        return self.resourceoption_set.filter(**query)

    def get_option(self, name, namespace=''):
        assert name is not None, "Parameter 'name' must be defined."

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
            option_value = option.typed_value()
        except djexceptions.ObjectDoesNotExist:
            option_value = default

        return option_value

    def get_type_name(self):
        return self.__class__.__name__ if not self.content_type else self.content_type.model_class().__name__

    def as_leaf_class(self):
        content_type = self.content_type
        model = content_type.model_class()
        if model == Resource or self.__class__ == model:
            return self

        return model.objects.get(pk=self.id)

    def save(self, *args, **kwargs):
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__,
                                                                  for_concrete_model=not self._meta.proxy)

        if not self.last_seen:
            self.last_seen = timezone.now()

        self.type = self.get_type_name()

        super(Resource, self).save(*args, **kwargs)

    def can_add(self, child):
        """
        Test if child can be added to this resource.
        """
        return True

    def available(self):
        """
        Iterate through available related resources. Override this method for custom behavior.
        """
        for res in Resource.objects.active(parent=self, status=Resource.STATUS_FREE):
            yield res

    def _change_status(self, new_status, method_name, cascade=False):
        assert new_status, "new_status must be defined."
        assert method_name, "method_name must be defined."

        if cascade:
            for child in self:
                getattr(child, method_name)()

        self.status = new_status
        self.save()

    def is_saved(self):
        return self.id is not None
