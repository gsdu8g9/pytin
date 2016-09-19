from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import RelatedFieldListFilter

from licenses.models import DirectAdminLicense


class PoolListFilter(RelatedFieldListFilter):
    title = 'Pool'
    parameter_name = 'pool'

    def field_choices(self, field, request, model_admin):
        limit_choices_to = {
            'pk__in': set(model_admin.get_queryset(request).values_list('assigned_ip__pool', flat=True))}
        return field.get_choices(include_blank=False, limit_choices_to=limit_choices_to)


@admin.register(DirectAdminLicense)
class DirectAdminLicenseAdmin(admin.ModelAdmin):
    list_display = ['cid', 'lid', 'assigned_ip', 'get_status', 'get_last_seen', 'get_ip_pool', 'assigned_ip_port']
    list_filter = ['cid', 'assigned_ip__status', ('assigned_ip__pool', PoolListFilter)]
    raw_id_fields = ['assigned_ip']
    search_fields = ['assigned_ip', 'lid']

    def assigned_ip_port(self, obj):
        return obj.assigned_ip.parent

    def get_ip_pool(self, obj):
        return obj.assigned_ip.pool

    get_ip_pool.admin_order_field = 'assigned_ip__pool'
    get_ip_pool.short_description = 'Pool'

    def get_last_seen(self, obj):
        return obj.last_seen

    get_last_seen.admin_order_field = 'assigned_ip__last_seen'
    get_last_seen.short_description = 'Last seen'

    def get_status(self, obj):
        return obj.status

    get_status.admin_order_field = 'assigned_ip__status'
    get_status.short_description = 'License status'
