from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from events.models import HistoryEvent
from ipman.models import IPAddressPoolFactory, IPAddressGeneric
from resources.models import Resource


class HistoryEventTest(TestCase):
    def setUp(self):
        super(HistoryEventTest, self).setUp()
        HistoryEvent.objects.filter().delete()

    def test_ipaddress_history(self):
        pool = IPAddressPoolFactory.from_name('Test pool')

        ip1 = IPAddressGeneric.objects.create(address='192.168.1.2', pool=pool)
        ip2 = IPAddressGeneric.objects.create(address='192.168.2.2', pool=pool)
        ip3 = IPAddressGeneric.objects.create(address='192.168.3.2', pool=pool)

        self.assertEqual(4, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))
        self.assertEqual(11, len(HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)))

        # skip record with no changes
        ip1.address = '192.168.1.2'
        ip1.save()
        self.assertEqual(11, len(HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)))

    def test_resource_option_no_changes(self):
        """
        Test journaling on/off
        :return:
        """
        ip1 = Resource.objects.create(address='172.1.1.10')
        self.assertEqual(1, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))
        self.assertEqual(4, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval1')
        self.assertEqual(5, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval1')
        self.assertEqual(5, len(HistoryEvent.objects.all()))

        # final state
        self.assertEqual(5, len(HistoryEvent.objects.all()))
        self.assertEqual(1, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))
        self.assertEqual(4, len(HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)))

    def test_resource_option_journaling(self):
        """
        Test journaling on/off
        :return:
        """
        ip1 = Resource.objects.create(address='172.1.1.10')
        self.assertEqual(1, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))
        self.assertEqual(4, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval1')
        self.assertEqual(5, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval2', journaling=False)
        self.assertEqual(5, len(HistoryEvent.objects.all()))

        # final state
        self.assertEqual(5, len(HistoryEvent.objects.all()))
        self.assertEqual(1, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))
        self.assertEqual(4, len(HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)))

    def test_core_fields_change(self):
        ip1 = Resource.objects.create(address='172.1.1.10')
        self.assertEqual(1, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))
        self.assertEqual(3, len(HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)))
        self.assertEqual(4, len(HistoryEvent.objects.all()))

        ip1.use()

        self.assertEqual(4, len(HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)))
        self.assertEqual(5, len(HistoryEvent.objects.all()))

    def test_related_resource_option_change_history(self):
        ip1 = Resource.objects.create(address='172.1.1.10')
        self.assertEqual(1, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))

        ip1.set_option('testfield', 'testval1')
        self.assertEqual(5, len(HistoryEvent.objects.all()))

        ip1.set_option('testfield', 'testval2')
        self.assertEqual(6, len(HistoryEvent.objects.all()))

        self.assertEqual(1, len(HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)))
        self.assertEqual(5, len(HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)))

    def test_resource_option_change_history(self):
        res1 = Resource.objects.create(name='res1')

        self.assertEqual(3, len(HistoryEvent.objects.all()))

        res1.set_option('testfield', 'testval1')

        self.assertEqual(4, len(HistoryEvent.objects.all()))

        res1.set_option('testfield', 'testval2')

        self.assertEqual(5, len(HistoryEvent.objects.all()))

        events = HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)

        self.assertEqual(4, len(events))
        self.assertEqual(HistoryEvent.UPDATE, events[2].event_type)
        self.assertEqual('testfield', events[2].field_name)
        self.assertEqual(None, events[2].field_old_value)
        self.assertEqual('testval1', events[2].field_new_value)

        self.assertEqual(HistoryEvent.UPDATE, events[3].event_type)
        self.assertEqual('testfield', events[3].field_name)
        self.assertEqual('testval1', events[3].field_old_value)
        self.assertEqual('testval2', events[3].field_new_value)

    def test_resource_change_history(self):
        res1 = Resource.objects.create(name='res1')
        res2 = Resource.objects.create(name='res2', parent=res1)

        # two create events
        self.assertEqual(7, HistoryEvent.objects.all().count())

        events = HistoryEvent.objects.filter(event_type=HistoryEvent.CREATE)
        self.assertEqual(2, len(events))
        self.assertEqual(HistoryEvent.CREATE, events[0].event_type)
        self.assertEqual(res1.id, events[0].object_id)
        self.assertEqual(HistoryEvent.CREATE, events[1].event_type)
        self.assertEqual(res2.id, events[1].object_id)

        # Resource field changes
        res1.name = 'res1_new'
        res1.save()

        res2.name = 'res2_new'
        res2.parent = None
        res2.save()

        events = HistoryEvent.objects.all()
        self.assertEqual(10, len(events))

        events = HistoryEvent.objects.filter(event_type=HistoryEvent.UPDATE)

        self.assertEqual(8, len(events))
        self.assertEqual(res1.id, events[0].object_id)
        self.assertEqual('name', events[0].field_name)
        self.assertEqual(None, events[0].field_old_value)
        self.assertEqual('res1', events[0].field_new_value)

        self.assertEqual(res2.id, events[2].object_id)
        self.assertEqual('parent_id', events[2].field_name)
        self.assertEqual(None, events[2].field_old_value)
        self.assertEqual(res1.id, int(events[2].field_new_value))

        self.assertEqual(res1.id, events[5].object_id)
        self.assertEqual('name', events[5].field_name)
        self.assertEqual('res1', events[5].field_old_value)
        self.assertEqual('res1_new', events[5].field_new_value)
