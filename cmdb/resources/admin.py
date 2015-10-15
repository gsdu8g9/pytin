from __future__ import unicode_literals

from django.contrib import admin
from django_mptt_admin.admin import DjangoMpttAdmin

from resources.models import Resource, ResourceOption, ResourceComment


class ResourceOptionInline(admin.TabularInline):
    model = ResourceOption
    extra = 0


class ResourceCommentInline(admin.StackedInline):
    model = ResourceComment
    extra = 0


class ResourceAdmin(DjangoMpttAdmin):
    list_display = ['id', 'name', 'content_type', 'status']
    search_fields = ['id', 'status', 'type', 'name']
    list_filter = ['type', 'status']

    tree_auto_open = False
    tree_load_on_demand = True

    raw_id_fields = ['parent']
    inlines = [
        ResourceCommentInline,
        ResourceOptionInline
    ]

    def filter_tree_queryset(self, queryset):
        return queryset.exclude(status=Resource.STATUS_DELETED)


class ResourceOptionAdmin(admin.ModelAdmin):
    list_display = ['resource', 'id', 'name', 'value', 'format', 'updated_at']
    search_fields = ['name', 'value', 'format', 'resource']
    list_filter = ['name', 'format']
    raw_id_fields = ['resource']


admin.site.register(Resource, ResourceAdmin)
admin.site.register(ResourceOption, ResourceOptionAdmin)
