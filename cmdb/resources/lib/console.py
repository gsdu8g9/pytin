from __future__ import unicode_literals

from django.db import models
from django.db.models import DateTimeField
from django.utils import timezone

from prettytable import PrettyTable

from cmdb.settings import logger
from resources.models import ModelFieldChecker


class ConsoleResourceWriter:
    def __init__(self, resources_iterable):
        if not resources_iterable:
            resources_iterable = []

        self.indent = 4
        self.resources_iterable = resources_iterable

    def print_table(self, fields=None, sort_by=None):
        assert fields

        table = PrettyTable(fields)
        table.padding_width = 1
        table.sortby = sort_by

        for afield in table.align:
            table.align[afield] = 'l'

        for resource in self.resources_iterable:
            if isinstance(resource, models.Model):
                table.add_row(self._get_resource_data_row(resource, fields))
            else:
                table.add_row(resource)

        logger.info(table.get_string())

    def print_path(self, fields=None):
        assert fields

        indent = 0
        for resource in self.resources_iterable:
            columns = self._get_resource_data_row(resource, fields)

            logger.info("%s%s" % ("".ljust(indent * self.indent), " ".join([unicode(col_value) for col_value in columns])))
            indent += 1

    def print_tree(self, fields=None):
        assert fields

        for resource in self.resources_iterable:
            indent = self.resources_iterable.level - 1

            columns = ['']
            columns.extend(self._get_resource_data_row(resource, fields))
            columns.append('')

            logger.info(
                "%s%s" % ("".ljust(indent * self.indent), " | ".join([unicode(col_value) for col_value in columns])))

    def dump(self):
        for resource in self.resources_iterable:
            self.dump_item(resource)

    @staticmethod
    def dump_item(resource):
        assert resource

        # dump model fields
        for field in resource.__class__._meta.fields:
            field_value = getattr(resource, field.name)
            if isinstance(field, DateTimeField):
                field_value = timezone.localtime(field_value)

            logger.info("%s = %s" % (field.name, field_value))

        # dump resource options
        for option in resource.get_options():
            logger.info("%s" % option)

    @staticmethod
    def _get_resource_data_row(resource, fields=None):
        assert resource
        assert fields

        columns = []
        for field in fields:
            if field == 'parent_id':
                field_value = resource.parent_id
            elif field == 'self':
                field_value = unicode(resource)
            else:
                field_value = ModelFieldChecker.get_field_value(resource, field, '%s?' % field)

            columns.append(field_value)

        return columns
