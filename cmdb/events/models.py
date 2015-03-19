from django.db import models


class Event(models.Model):
    RESOURCE_CREATE = 'resource_create'
    RESOURCE_UPDATE = 'resource_update',
    RESOURCE_DELETE = 'resource_delete'

    source_object_id = models.PositiveIntegerField(null=True, db_index=True)
    source_model = models.CharField(max_length=64, null=True, db_index=True)
    type = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.TextField(null=True)

    class Meta:
        db_table = "events"
