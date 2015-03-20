from django.contrib import admin
from events.models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_object_id', 'source_model', 'type', 'created_at', 'data']
    list_filter = ['type']

admin.site.register(Event, EventAdmin)

