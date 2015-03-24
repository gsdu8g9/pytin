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

    def test_find(self):
        self._create_test_resources(50)

        self.assertEqual(50, len(Resource.objects.all()))
        self.assertEqual(2500, len(ResourceOption.objects.all()))

        # search by fields
        self.assertEqual(50, len(Resource.find(field_2='value_2')))
        self.assertEqual(1, len(Resource.find(field_2='value_2', namespace='ns10')))
        self.assertEqual(50, len(Resource.find(field_2__contains='value')))

        # search by existing fields
        self.assertEqual(10, len(Resource.find(status=Resource.STATUS_FREE)))
        self.assertEqual(10, len(Resource.find(status=Resource.STATUS_DELETED)))

        # status from Resource, namespace from ResourceOption
        self.assertEqual(1, len(Resource.find(status=Resource.STATUS_FREE, namespace='ns5')))

    def _create_test_resources(self, count):
        for idx1 in range(1, count + 1):
            resource = Resource.objects.create(status=Resource.STATUS_CHOICES[idx1 % len(Resource.STATUS_CHOICES)][0])

            for idx2 in range(1, count + 1):
                resource.set_option('field_%s' % idx2, 'value_%s' % idx2, namespace='ns%s' % idx1)
