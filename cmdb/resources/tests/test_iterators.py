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

        path_list = [(node, level) for node, level in TreeIterator(res5)]
        self.assertEqual(('res5', 1), (path_list[0][0].name, path_list[0][1]))

        path_list = [(node, level) for node, level in TreeIterator(res4)]
        self.assertEqual(('res4', 1), (path_list[0][0].name, path_list[0][1]))
        self.assertEqual(('res5', 2), (path_list[1][0].name, path_list[1][1]))

        path_list = [(node, level) for node, level in TreeIterator(res4)]
        self.assertEqual(('res4', 1), (path_list[0][0].name, path_list[0][1]))
        self.assertEqual(('res5', 2), (path_list[1][0].name, path_list[1][1]))
        self.assertEqual(('res6', 2), (path_list[2][0].name, path_list[2][1]))

        path_list = [(node, level) for node, level in TreeIterator(res1)]
        self.assertEqual(('res1', 1), (path_list[0][0].name, path_list[0][1]))
        self.assertEqual(('res2', 2), (path_list[1][0].name, path_list[1][1]))
        self.assertEqual(('res3', 3), (path_list[2][0].name, path_list[2][1]))
        self.assertEqual(('res4', 3), (path_list[3][0].name, path_list[3][1]))
        self.assertEqual(('res5', 4), (path_list[4][0].name, path_list[4][1]))
        self.assertEqual(('res6', 4), (path_list[5][0].name, path_list[5][1]))
