from __future__ import unicode_literals
from django.test import TestCase

from resources.iterators import PathIterator, TreeIterator
from resources.models import Resource


class ResourceTest(TestCase):
    def test_iterate_path(self):
        res1 = Resource.objects.create(name='res1')
        res2 = Resource.objects.create(name='res2', parent=res1)
        res3 = Resource.objects.create(name='res3', parent=res2)
        res4 = Resource.objects.create(name='res4', parent=res3)
        res5 = Resource.objects.create(name='res5', parent=res4)

        path_list = [node for node in PathIterator(res5)]
        self.assertEqual('res1', path_list[0].name)
        self.assertEqual('res2', path_list[1].name)
        self.assertEqual('res3', path_list[2].name)
        self.assertEqual('res4', path_list[3].name)
        self.assertEqual('res5', path_list[4].name)

    def test_iterate_tree(self):
        res1 = Resource.objects.create(name='res1')
        res2 = Resource.objects.create(name='res2', parent=res1)
        res3 = Resource.objects.create(name='res3', parent=res2)
        res4 = Resource.objects.create(name='res4', parent=res2)
        res5 = Resource.objects.create(name='res5', parent=res4)
        res6 = Resource.objects.create(name='res6', parent=res4)

        path_list = [node for node in TreeIterator(res5)]
        self.assertEqual('res5', path_list[0].name)

        path_list = [node for node in TreeIterator(res4)]
        self.assertEqual('res4', path_list[0].name)
        self.assertEqual('res5', path_list[1].name)

        path_list = [node for node in TreeIterator(res4)]
        self.assertEqual('res4', path_list[0].name)
        self.assertEqual('res5', path_list[1].name)
        self.assertEqual('res6', path_list[2].name)

        path_list = [node for node in TreeIterator(res1)]
        self.assertEqual('res1', path_list[0].name)
        self.assertEqual('res2', path_list[1].name)
        self.assertEqual('res3', path_list[2].name)
        self.assertEqual('res4', path_list[3].name)
        self.assertEqual('res5', path_list[4].name)
        self.assertEqual('res6', path_list[5].name)
