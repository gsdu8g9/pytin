from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelForm
from django_mptt_admin.admin import DjangoMpttAdmin

from resources.models import Resource, ResourceOption, ResourceComment


class ResourceForm(ModelForm):
    """
    Form with correct handling of content_type editing.
    """
    APP_LABELS = ['assets', 'ipman', 'licenses', 'resources']

    class Meta:
        model = Resource
        fields = '__all__'

    type = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        field_choices = []
        for obj_type in ContentType.objects.all():
            if obj_type.app_label in self.APP_LABELS:
                nat_key = ".".join(obj_type.natural_key())
                field_choices.append((nat_key, nat_key))

        self.base_fields['type'].choices = field_choices

        instance = kwargs.get('instance')
        if instance:
            self.base_fields['type'].initial = ".".join(instance.content_type.natural_key())

        super(ResourceForm, self).__init__(*args, **kwargs)


class ResourceOptionInline(admin.TabularInline):
    model = ResourceOption
    extra = 0


class ResourceCommentInline(admin.StackedInline):
    model = ResourceComment
    extra = 0


class ResourceAdmin(DjangoMpttAdmin):
    form = ResourceForm
    raw_id_fields = ['parent']

    exclude = ['content_type']
    date_hierarchy = 'last_seen'
    list_display = ['id', 'name', 'content_type', 'status', 'last_seen']
    search_fields = ['id', 'status', 'name']
    list_filter = ['content_type', 'status']
    ordering = ['name']

    tree_auto_open = False
    tree_load_on_demand = True

    inlines = [
        ResourceCommentInline,
        ResourceOptionInline
    ]

    def filter_tree_queryset(self, queryset):
        return queryset.exclude(status__in=[Resource.STATUS_DELETED, Resource.STATUS_FAILED])

    def save_model(self, request, obj, form, change):
        (app_label, model_name) = form.cleaned_data['type'].split('.', 2)
        obj.content_type = ContentType.objects.get(app_label=app_label, model=model_name)

        super(ResourceAdmin, self).save_model(request, obj, form, change)


class ResourceOptionAdmin(admin.ModelAdmin):
    list_display = ['resource', 'id', 'name', 'value', 'format', 'updated_at']
    search_fields = ['name', 'value', 'format', 'resource']
    list_filter = ['name', 'format']
    raw_id_fields = ['resource']


admin.site.register(Resource, ResourceAdmin)
admin.site.register(ResourceOption, ResourceOptionAdmin)
