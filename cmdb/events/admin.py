from django.contrib import admin
from events.models import HistoryEvent


class HistoryEventAdmin(admin.ModelAdmin):
    list_filter = ['type']

admin.site.register(HistoryEvent, HistoryEventAdmin)

