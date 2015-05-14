from django.contrib import admin

from resources.models import Resource, ResourceOption


class ResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_type', 'created_at', 'updated_at']
    search_fields = ['type']


class ResourceOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'value', 'format', 'updated_at']
    search_fields = ['name', 'value', 'format']
    list_filter = ['name', 'format']


admin.site.register(Resource, ResourceAdmin)
admin.site.register(ResourceOption, ResourceOptionAdmin)
