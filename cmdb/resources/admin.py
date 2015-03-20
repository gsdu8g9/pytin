from django.contrib import admin

from resources.models import Resource, ResourceOption


class ResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at', 'updated_at']
    search_fields = ['name']


class ResourceOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'value', 'updated_at']
    search_fields = ['name', 'value']
    list_filter = ['name']


admin.site.register(Resource, ResourceAdmin)
admin.site.register(ResourceOption, ResourceOptionAdmin)
