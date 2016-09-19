from __future__ import unicode_literals

from django.contrib import admin

from events.models import HistoryEvent


@admin.register(HistoryEvent)
class HistoryEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'object_id', 'object_type', 'created_at', 'field_name', 'field_old_value',
                    'field_new_value']
    search_fields = ['=object_id', '=object_type', '=field_name', 'field_old_value', 'field_new_value']
    list_filter = ['event_type', 'object_type']
