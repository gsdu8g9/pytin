from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter

from ipman.models import IPAddressGeneric


@admin.register(IPAddressGeneric)
class IPAddressGenericAdmin(admin.ModelAdmin):
    date_hierarchy = 'last_seen'
    raw_id_fields = ['pool', 'parent']
    list_display = ['id', 'address', 'status', 'pool', 'last_seen', 'parent']
    search_fields = ['address']
    list_filter = ['status', 'version', ('pool', RelatedOnlyFieldListFilter)]
    ordering = ['id']
