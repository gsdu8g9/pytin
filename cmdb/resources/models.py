from __future__ import unicode_literals

import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.core import exceptions as djexceptions
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.apps import apps
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey

from cmdb.settings import logger


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

    @staticmethod
    def get_field_value(resource, field_name, default=''):
        if ModelFieldChecker.is_field_or_property(resource, field_name):
            return getattr(resource, field_name, default)
        else:
            return resource.get_option_value(field_name, default=default)


class SubclassingQuerySet(QuerySet):
    def __getitem__(self, k):
        result = super(SubclassingQuerySet, self).__getitem__(k)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result

    def create(self, **kwargs):
        """
        Create new model of calling class type. Model fields are only checked for Resource() model
        to not interfere with proxy model properties. All extra options are saved as ResourceOption.
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

        requested_model = self.model
        if 'type' in kwargs:
            requested_model = apps.get_model(kwargs['type'])
        # else:
        #     model_fields['type'] = requested_model.__name__

        new_object = requested_model(**model_fields)
        self._for_write = True
        new_object.save(force_insert=True, using=self.db)

        need_save = False
        for option_field in option_fields.keys():
            # if model have property with the given name, then set it via setattr,
            # because of possible custom behaviour
            if hasattr(new_object, option_field):
                setattr(new_object, option_field, option_fields[option_field])
                need_save = True
            else:
                new_object.set_option(option_field, option_fields[option_field])

        if need_save:
            new_object.save()

        return new_object

    def __iter__(self):
        for item in super(SubclassingQuerySet, self).__iter__():
            yield item.as_leaf_class() if isinstance(item, Resource) else item

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
        logger.debug("%s, %s" % (args, kwargs))

        return super(SubclassingQuerySet, self).get(*args, **kwargs).as_leaf_class()


class ResourcesWithOptionsManager(TreeManager):
    """
    Query manager with support for query by options.
    """

    def get_queryset(self):
        return SubclassingQuerySet(self.model)


class ResourcesActiveWithOptionsManager(TreeManager):
    """
    Query manager with support for query by options.
    """

    def get_queryset(self):
        return SubclassingQuerySet(self.model).filter().exclude(status=Resource.STATUS_DELETED)


class ResourceComment(models.Model):
    """
    Resource comments.
    """
    resource = models.ForeignKey('Resource')
    author = models.ForeignKey(User)

    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)

    message = models.TextField('Comment text')


class ResourceOption(models.Model):
    """
    Resource options. Resources is able to have different options and
    client can search by them.
    """

    class StringValue:
        _value = ''

        def __init__(self, value):
            self._value = unicode(value)

        def __unicode__(self):
            return "'%s'" % self.typed_value()

        def typed_value(self):
            return self._value

        def raw_value(self):
            return self._value

    class IntegerValue(StringValue):
        def __unicode__(self):
            return "%d" % self.typed_value()

        def typed_value(self):
            return int(self._value)

    class BooleanValue(StringValue):
        true_vals = ['yes', 'true', '1']

        def __init__(self, value):
            value_str = unicode(value).lower()
            self._value = True if value_str in self.true_vals else False

        def __unicode__(self):
            return "%s" % self.typed_value()

        def typed_value(self):
            return bool(self._value)

    class FloatValue(StringValue):
        def __unicode__(self):
            return "%f" % self.typed_value()

        def typed_value(self):
            return float(self._value)

    class DictionaryValue(StringValue):
        def __init__(self, value):
            self._value = value

            if isinstance(value, dict):
                self._value = json.dumps(value)

        def __unicode__(self):
            return "'%s'" % self.typed_value()

        def typed_value(self):
            return json.loads(self._value, encoding='utf-8', parse_float=True, parse_int=True, parse_constant=True)

    FORMAT_DICT = 'dict'
    FORMAT_INT = 'int'
    FORMAT_BOOL = 'bool'
    FORMAT_FLOAT = 'float'
    FORMAT_STRING = 'string'
    FORMAT_CHOICES = (
        (FORMAT_DICT, 'Dictionary string'),
        (FORMAT_INT, 'Integer value'),
        (FORMAT_BOOL, 'Boolean value'),
        (FORMAT_FLOAT, 'Float value'),
        (FORMAT_STRING, 'String value'),
    )
    FORMAT_HANDLERS = {
        FORMAT_DICT: DictionaryValue,
        FORMAT_INT: IntegerValue,
        FORMAT_BOOL: BooleanValue,
        FORMAT_FLOAT: FloatValue,
        FORMAT_STRING: StringValue,
    }

    resource = models.ForeignKey('Resource')
    name = models.CharField(max_length=155, db_index=True)
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

    def __unicode__(self):
        return "%s = %s" % (self.name, self._value_handler())

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        self.format = self.guess_format(self.value) if not self.format else self.format

        super(ResourceOption, self).save(force_insert, force_update, using, update_fields)

    def _value_handler(self):
        return self.value_format_handler(self.value)

    @staticmethod
    def guess_format(value):
        ret_format = ResourceOption.FORMAT_STRING

        if isinstance(value, bool):
            ret_format = ResourceOption.FORMAT_BOOL
        elif isinstance(value, int):
            ret_format = ResourceOption.FORMAT_INT
        elif isinstance(value, float):
            ret_format = ResourceOption.FORMAT_FLOAT
        elif isinstance(value, dict):
            ret_format = ResourceOption.FORMAT_DICT

        return ret_format

    @property
    def typed_value(self):
        return self._value_handler().typed_value()


class Resource(MPTTModel):
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
        (STATUS_LOCKED, 'Resource is reserved'),
        (STATUS_DELETED, 'Resource is marked to delete'),
    )

    # parent = models.ForeignKey("self", default=None, db_index=True, null=True)
    parent = TreeForeignKey("self", blank=True, db_index=True, null=True, related_name='children')
    content_type = models.ForeignKey(ContentType, editable=False, null=True)

    name = models.CharField(default='resource', db_index=True, max_length=155)
    type = models.CharField(default='Resource', db_index=True, max_length=155)
    status = models.CharField(max_length=25, db_index=True, choices=STATUS_CHOICES, default=STATUS_FREE)
    created_at = models.DateTimeField('Date created', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)
    last_seen = models.DateTimeField('Date last seen', db_index=True, default=timezone.now)

    objects = ResourcesWithOptionsManager()
    active = ResourcesActiveWithOptionsManager()

    class Meta:
        db_table = "resources"

    def __unicode__(self):
        return self.name

    def __contains__(self, item):
        return Resource.active.filter(pk=item.id, parent=self).exists()

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
        for resource in Resource.active.filter(parent=self):
            yield resource

    def touch(self, cascade=False):
        """
        Update last_seen date of the resource
        """

        if cascade:
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

    def _change_status(self, new_status, method_name, cascade=False):
        assert new_status, "new_status must be defined."
        assert method_name, "method_name must be defined."

        if cascade:
            for child in self:
                getattr(child, method_name)(cascade)

        if self.status != new_status:
            logger.debug("Setting resource ID:%s status: %s -> %s" % (self.id, self.status, new_status))

            self.status = new_status
            self.save()

    def delete(self, using=None):
        """
        Override Model .delete() method. Instead of actual deleting object from the DB
        set status Deleted.
        """
        logger.debug("Removing resource ID:%s %s" % (self.id, self))

        if len(list(self)) > 0:
            raise ValidationError(_("Object have one or more childs."))

        self.status = Resource.STATUS_DELETED
        self.save()

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

    @property
    def is_saved(self):
        return self.id is not None

    @property
    def typed_parent(self):
        return self.parent.as_leaf_class()

    def set_option(self, name, value, format=None):
        """
        Set resource option. If format is omitted, then format is guessed from value type.
        """

        assert self.is_saved, "Resource must be saved before setting options"
        assert name is not None, "Parameter 'name' must be defined."

        query = dict(
            name=name,
            defaults=dict(
                value=value,
                format=format,
            )
        )

        self.resourceoption_set.update_or_create(**query)

    def get_options(self):
        query = dict(
        )

        return self.resourceoption_set.filter(**query)

    def get_option(self, name):
        assert name is not None, "Parameter 'name' must be defined."

        query = dict(
            name=name,
        )

        return self.resourceoption_set.get(**query)

    def has_option(self, name):
        assert name is not None, "Parameter 'name' must be defined."

        try:
            self.get_option(name)
        except djexceptions.ObjectDoesNotExist:
            return False

        return True

    def get_option_value(self, name, default=''):
        assert name is not None, "Parameter 'name' must be defined."

        option_value = default
        try:
            option = self.get_option(name)
            option_value = option.typed_value
        except djexceptions.ObjectDoesNotExist:
            option_value = default

        return option_value

    def get_type_name(self):
        return self.__class__.__name__ if not self.content_type else self.content_type.model_class().__name__

    def cast_type(self, new_class_type):
        assert new_class_type

        self.content_type = ContentType.objects.get_for_model(new_class_type,
                                                              for_concrete_model=not new_class_type._meta.proxy)

        if self.content_type.model_class == new_class_type:
            return self

        self.type = new_class_type.__name__

        super(Resource, self).save()

        new_object = self.as_leaf_class()

        return new_object

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

        if self.type != self.get_type_name():
            self.type = self.get_type_name()

        if not self.last_seen:
            self.last_seen = timezone.now()

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
        for res in Resource.active.filter(parent=self, status=Resource.STATUS_FREE):
            yield res
