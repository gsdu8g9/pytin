from __future__ import unicode_literals

from django.test import TestCase

from events.models import HistoryEvent
from ipman.models import IPAddress
from resources.models import Resource


class HistoryEventTest(TestCase):
    def setUp(self):
        super(HistoryEventTest, self).setUp()
        HistoryEvent.objects.filter().delete()

    def test_resource_option_journaling(self):
        """
        Test journaling on/off
        :return:
        """
        ip1 = IPAddress.objects.create(address='172.1.1.10')
        self.assertEqual(1, len(HistoryEvent.objects.filter(type=HistoryEvent.CREATE)))
        self.assertEqual(5, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval1')
        self.assertEqual(6, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval2', journaling=False)
        self.assertEqual(6, len(HistoryEvent.objects.all()))

        # final state
        self.assertEqual(6, len(HistoryEvent.objects.all()))
        self.assertEqual(1, len(HistoryEvent.objects.filter(type=HistoryEvent.CREATE)))
        self.assertEqual(5, len(HistoryEvent.objects.filter(type=HistoryEvent.UPDATE)))

    def test_core_fields_change(self):
        ip1 = IPAddress.objects.create(address='172.1.1.10')
        self.assertEqual(1, len(HistoryEvent.objects.filter(type=HistoryEvent.CREATE)))
        self.assertEqual(5, len(HistoryEvent.objects.all()))

        for event in HistoryEvent.objects.all():
            print event.id, event.field_name, event.type, event.field_old_value, '->', event.field_new_value

        print "---"

        ip1.use()
        self.assertEqual(6, len(HistoryEvent.objects.all()))

        for event in HistoryEvent.objects.all():
            print event.id, event.field_name, event.type, event.field_old_value, '->', event.field_new_value

    def test_related_resource_option_change_history(self):
        ip1 = IPAddress.objects.create(address='172.1.1.10')
        self.assertEqual(1, len(HistoryEvent.objects.filter(type=HistoryEvent.CREATE)))

        ip1.set_option('testfield', 'testval1')
        self.assertEqual(6, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval2')
        self.assertEqual(7, len(HistoryEvent.objects.all()))

        self.assertEqual(1, len(HistoryEvent.objects.filter(type=HistoryEvent.CREATE)))
        self.assertEqual(6, len(HistoryEvent.objects.filter(type=HistoryEvent.UPDATE)))

    def test_resource_option_change_history(self):
        res1 = Resource.objects.create(name='res1')

        self.assertEqual(1, len(HistoryEvent.objects.all()))

        res1.set_option('testfield', 'testval1')

        self.assertEqual(2, len(HistoryEvent.objects.all()))

        res1.set_option('testfield', 'testval2')

        self.assertEqual(3, len(HistoryEvent.objects.all()))

        events = HistoryEvent.objects.filter(type=HistoryEvent.UPDATE)

        self.assertEqual(2, len(events))
        self.assertEqual(HistoryEvent.UPDATE, events[0].type)
        self.assertEqual('testfield', events[0].field_name)
        self.assertEqual(None, events[0].field_old_value)
        self.assertEqual('testval1', events[0].field_new_value)

        self.assertEqual(HistoryEvent.UPDATE, events[1].type)
        self.assertEqual('testfield', events[1].field_name)
        self.assertEqual('testval1', events[1].field_old_value)
        self.assertEqual('testval2', events[1].field_new_value)

    def test_resource_change_history(self):
        res1 = Resource.objects.create(name='res1')
        res2 = Resource.objects.create(name='res2', parent=res1)

        # two create events
        events = HistoryEvent.objects.all()
        self.assertEqual(2, len(events))
        self.assertEqual(HistoryEvent.CREATE, events[0].type)
        self.assertEqual('res1', events[0].resource.name)
        self.assertEqual(HistoryEvent.CREATE, events[1].type)
        self.assertEqual('res2', events[1].resource.name)

        # Resource field changes
        res1.name = 'res1_new'
        res1.save()

        res2.name = 'res2_new'
        res2.parent = None
        res2.save()

        events = HistoryEvent.objects.all()
        self.assertEqual(5, len(events))

        events = HistoryEvent.objects.filter(type=HistoryEvent.UPDATE)
        self.assertEqual(3, len(events))
        self.assertEqual('res1_new', events[0].resource.name)
        self.assertEqual('name', events[0].field_name)
        self.assertEqual('res1', events[0].field_old_value)
        self.assertEqual('res1_new', events[0].field_new_value)

        self.assertEqual('res2_new', events[1].resource.name)
        self.assertEqual('parent_id', events[1].field_name)
        self.assertEqual(unicode(res1.id), events[1].field_old_value)
        self.assertEqual(None, events[1].field_new_value)
