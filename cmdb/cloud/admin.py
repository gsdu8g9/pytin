from __future__ import unicode_literals
from django.contrib import admin

from cloud.models import CloudTaskTracker


@admin.register(CloudTaskTracker)
class CloudTaskTrackerAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'task_class', 'status', 'created_at', 'updated_at', 'error', 'context_json', 'return_json']
    list_filter = ['task_class', 'status']
    search_fields = ['context_json', 'return_json', 'error']
