from django.db import models
from django.utils import timezone


class Resource(models.Model):
    parent = models.ForeignKey("self", default=0)
    name = models.CharField(max_length=155, db_index=True)
    created_at = models.DateTimeField('Date created', db_index=True, default=timezone.now())
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)

    class Meta:
        db_table = "resources"

    def __str__(self):
        return "%d\t%s (%s, %s)" % (self.pk, self.name, self.created_at, self.updated_at)


class ResourceOption(models.Model):
    resource = models.ForeignKey(Resource)
    name = models.CharField(max_length=155, db_index=True)
    value = models.TextField('Option value')
    updated_at = models.DateTimeField('Date updated', auto_now=True, db_index=True)

    class Meta:
        db_table = "resource_options"

    def __str__(self):
        return "%s = '%s'..." % (self.name, self.value[:15])
