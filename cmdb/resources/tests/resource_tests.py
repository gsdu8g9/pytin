# -*- coding: utf-8 -*-
from django.test import TestCase

from resources.models import Resource, ResourceOption


class ResourceTest(TestCase):
    def test_create(self):
        resource1 = Resource()
        resource1.save()

        resource2 = Resource(status=Resource.STATUS_DELETED)
        resource2.save()

        resource3 = Resource(status=Resource.STATUS_LOCKED)
        resource3.save()

        self.assertEqual(3, len(Resource.objects.all()))
        self.assertEqual(2, len(Resource.active.all()))

    def test_find(self):
        resource1 = Resource()
        resource1.save()

        resource2 = Resource(status=Resource.STATUS_DELETED)
        resource2.save()

        resource3 = Resource(status=Resource.STATUS_LOCKED)
        resource3.save()

        self.assertEqual(0, len(Resource.active.filter(status=Resource.STATUS_DELETED)))
        self.assertEqual(1, len(Resource.active.filter(status=Resource.STATUS_LOCKED)))

        self.assertEqual(2, len(Resource.active.filter(type=Resource.TYPE_GENERIC)))
        self.assertEqual(1, len(Resource.active.filter(type=Resource.TYPE_GENERIC, status=Resource.STATUS_LOCKED)))
        self.assertEqual(0, len(Resource.active.filter(type='unknown')))

    def test_set_get_options(self):
        resource1 = Resource()
        resource1.save()
        resource2 = Resource()
        resource2.save()

        self.assertEqual(0, len(ResourceOption.objects.all()))

        resource1.set_option('g_field1', 'value1')
        resource1.set_option('ns_field2', 'value2', namespace='test')

        # пременная с одинаковым именем
        resource1.set_option('nst_field', 'value_1', namespace='nst1')
        resource1.set_option('nst_field', 'value_2', namespace='nst2')
        resource1.set_option('nst_field', 'value_3')

        self.assertEqual(5, len(ResourceOption.objects.all()))

        # get_option
        self.assertEqual('value_3', resource1.get_option_value('nst_field'))
        self.assertEqual('', resource1.get_option_value('nst_field_unk'))
        self.assertEqual('def', resource1.get_option_value('nst_field_unk', default='def'))
        self.assertEqual('value_1', resource1.get_option_value('nst_field', namespace='nst1'))
        self.assertEqual('value_2', resource1.get_option_value('nst_field', namespace='nst2'))
        self.assertEqual('', resource1.get_option_value('nst_field', namespace='nst3'))

        # has_option
        self.assertEqual(False, resource1.has_option('nst_field', namespace='nst3'))
        self.assertEqual(True, resource1.has_option('nst_field', namespace='nst2'))
        self.assertEqual(True, resource1.has_option('nst_field'))
        self.assertEqual(False, resource1.has_option('nst_field_unk'))

        # set_option / edit
        resource2.set_option('nst_field', 'value_1', namespace='nst1')
        resource2.set_option('nst_field', 'value_2', namespace='nst2')
        resource2.set_option('nst_field', 'value_3')

        self.assertEqual('value_1', resource1.get_option_value('nst_field', namespace='nst1'))
        self.assertEqual('value_2', resource1.get_option_value('nst_field', namespace='nst2'))
        self.assertEqual('value_3', resource1.get_option_value('nst_field'))

        self.assertEqual('value_1', resource2.get_option_value('nst_field', namespace='nst1'))
        self.assertEqual('value_2', resource2.get_option_value('nst_field', namespace='nst2'))
        self.assertEqual('value_3', resource2.get_option_value('nst_field'))

        resource1.set_option('nst_field', 'value_3_ed')
        resource2.set_option('nst_field', 'value_2_ed', namespace='nst2')

        self.assertEqual('value_3_ed', resource1.get_option_value('nst_field'))
        self.assertEqual('value_2_ed', resource2.get_option_value('nst_field', namespace='nst2'))

    def test_find_by_options(self):
        resource1 = Resource()
        resource1.save()

        option1, created = resource1.resourceoption_set.update_or_create(name='test1',
                                                                         defaults=dict(
                                                                             format=ResourceOption.FORMAT_STRING,
                                                                             value='testval1'
                                                                         ))

        self.assertEqual(True, created)
        self.assertEqual('test1', option1.name)
        self.assertEqual('testval1', option1.value)
        self.assertEqual(ResourceOption.FORMAT_STRING, option1.format)

        option1, created = resource1.resourceoption_set.update_or_create(name='test1',
                                                                         defaults=dict(
                                                                             format=ResourceOption.FORMAT_INT,
                                                                             value='1000'
                                                                         ))

        self.assertEqual(False, created)  # updated
        self.assertEqual('test1', option1.name)
        self.assertEqual('1000', option1.value)
        self.assertEqual(ResourceOption.FORMAT_INT, option1.format)
