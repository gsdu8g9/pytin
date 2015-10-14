from __future__ import unicode_literals
from django.contrib import admin

from events.models import HistoryEvent
from resources.models import Resource


class HistoryEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_resource', 'created_at', 'field_name', 'field_old_value', 'field_new_value']
    search_fields = ['resource_id', 'field_name', 'field_old_value', 'field_new_value']
    list_filter = ['type']

    raw_id_fields = ['resource']

    def get_resource(self, inst):
        typed_res = Resource.objects.get(pk=inst.resource.id)
        return "%s (%s)" % (unicode(typed_res), typed_res.type)

    get_resource.short_description = 'Resource'


admin.site.register(HistoryEvent, HistoryEventAdmin)
