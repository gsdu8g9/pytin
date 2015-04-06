# -*- coding: utf-8 -*-

from django.test import TestCase

from resources.models import Resource, ResourceOption, ResourcePool


class ResourceTest(TestCase):
    def test_static_create(self):
        new_res = Resource.create(status=Resource.STATUS_INUSE, somekey1='someval1', somekey2='someval2')

        self.assertEqual(Resource.STATUS_INUSE, new_res.status)
        self.assertEqual('someval1', new_res.get_option_value('somekey1', namespace='Resource'))
        self.assertEqual('someval2', new_res.get_option_value('somekey2', namespace='Resource'))

        new_res1 = ResourcePool.create(status=Resource.STATUS_LOCKED, somekey1='someval11', somekey2='someval21')

        self.assertEqual(Resource.STATUS_LOCKED, new_res1.status)
        self.assertEqual('someval11', new_res1.get_option_value('somekey1', namespace='ResourcePool'))
        self.assertEqual('someval21', new_res1.get_option_value('somekey2', namespace='ResourcePool'))

    def test_option_type(self):
        resource1 = Resource()
        resource1.save()

        res_id = resource1.pk

        resource1.set_option('g_field1', 155, format=ResourceOption.FORMAT_INT)
        resource1.set_option('g_field2', 155.551, format=ResourceOption.FORMAT_FLOAT)
        resource1.set_option('g_field3', {'name1': 'val1', 'name2': 'val2'}, format=ResourceOption.FORMAT_DICT)

        del resource1

        resource1 = Resource.objects.get(pk=res_id)

        self.assertEqual(155, resource1.get_option_value('g_field1'))
        self.assertEqual(155.551, resource1.get_option_value('g_field2'))
        self.assertEqual({'name1': 'val1', 'name2': 'val2'}, resource1.get_option_value('g_field3'))

    def test_option_type_guessed_format(self):
        resource1 = Resource()
        resource1.save()

        resource1.set_option('g_field0', None)
        resource1.set_option('g_field1', 'alksdj')
        resource1.set_option('g_field2', 155)
        resource1.set_option('g_field3', 155.551)
        resource1.set_option('g_field4', {'name1': 'val1', 'name2': 'val2'})

        self.assertEqual(ResourceOption.FORMAT_STRING, resource1.get_option('g_field0').format)
        self.assertEqual(ResourceOption.FORMAT_STRING, resource1.get_option('g_field1').format)
        self.assertEqual(ResourceOption.FORMAT_INT, resource1.get_option('g_field2').format)
        self.assertEqual(ResourceOption.FORMAT_FLOAT, resource1.get_option('g_field3').format)
        self.assertEqual(ResourceOption.FORMAT_DICT, resource1.get_option('g_field4').format)

    def test_create(self):
        resource1 = Resource()
        resource1.save()

        resource2 = Resource(status=Resource.STATUS_DELETED)
        resource2.save()

        resource3 = Resource(status=Resource.STATUS_LOCKED)
        resource3.save()

        self.assertEqual(3, len(Resource.objects.all()))
        self.assertEqual(2, len(Resource.objects.active()))

    def test_filter_queryset_active(self):
        resource1 = Resource()
        resource1.save()

        resource2 = Resource(status=Resource.STATUS_DELETED)
        resource2.save()

        resource3 = Resource(status=Resource.STATUS_LOCKED)
        resource3.save()

        self.assertEqual(0, len(Resource.objects.active(status=Resource.STATUS_DELETED)))
        self.assertEqual(1, len(Resource.objects.active(status=Resource.STATUS_LOCKED)))

        self.assertEqual(2, len(Resource.objects.active()))
        self.assertEqual(1, len(Resource.objects.active(status=Resource.STATUS_LOCKED)))
        self.assertEqual(0, len(Resource.objects.active(type='unknown')))

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

    def test_proxy_models(self):
        resource1 = Resource()
        resource1.status = Resource.STATUS_FREE
        resource1.save()

        resource_pool1 = ResourcePool()
        resource_pool1.status = Resource.STATUS_INUSE
        resource_pool1.save()

        resource_pool1.name = 'test pool'

        # search with target type
        resource = Resource.objects.filter(status=Resource.STATUS_FREE)[0].get_proxy()
        resource_pool = Resource.objects.filter(status=Resource.STATUS_INUSE)[0].get_proxy()

        self.assertEqual(Resource, resource)
        self.assertEqual(ResourcePool, resource_pool)

    def test_find_objects(self):
        self._create_test_resources(50)

        self.assertEqual(50, len(Resource.objects.all()))
        self.assertEqual(2500, len(ResourceOption.objects.all()))

        # search by fields
        self.assertEqual(50, len(Resource.objects.filter(field_2='value_2')))
        self.assertEqual(1, len(Resource.objects.filter(field_2='value_2', namespace='ns10')))
        self.assertEqual(50, len(Resource.objects.filter(field_2__contains='value')))
        self.assertEqual(0, len(Resource.objects.filter(notexists_4='notexists_value_4')))

        # search by existing fields
        self.assertEqual(10, len(Resource.objects.filter(status=Resource.STATUS_FREE)))
        self.assertEqual(10, len(Resource.objects.filter(status=Resource.STATUS_DELETED)))

        # status from Resource, namespace from ResourceOption
        self.assertEqual(1, len(Resource.objects.filter(status=Resource.STATUS_FREE, namespace='ns5')))

    def _create_test_resources(self, count):
        for idx1 in range(1, count + 1):
            resource = Resource.objects.create(status=Resource.STATUS_CHOICES[idx1 % len(Resource.STATUS_CHOICES)][0])

            for idx2 in range(1, count + 1):
                resource.set_option('field_%s' % idx2, 'value_%s' % idx2, namespace='ns%s' % idx1)
