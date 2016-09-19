from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_init, post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from cmdb.settings import logger
from resources.models import ResourceOption


@python_2_unicode_compatible
class HistoryEvent(models.Model):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'

    TYPES = (
        (CREATE, 'create'),
        (UPDATE, 'update'),
        (DELETE, 'delete'),
    )

    object_id = models.IntegerField(db_index=True)
    object_type = models.CharField(max_length=64, db_index=True)
    event_type = models.CharField(max_length=64, choices=TYPES, db_index=True)
    field_name = models.CharField(max_length=155, db_index=True, null=True)
    field_old_value = models.CharField(max_length=255, db_index=True, null=True)
    field_new_value = models.CharField(max_length=255, db_index=True, null=True)
    created_at = models.DateTimeField(null=False, db_index=True)

    class Meta:
        db_table = "resource_history"

    def __str__(self):
        return "%s %s[%s].%s '%s'->'%s'" % (self.event_type,
                                            self.object_type,
                                            self.object_id,
                                            self.field_name,
                                            self.field_old_value,
                                            self.field_new_value)

    @staticmethod
    def add_create(entity):
        assert entity

        event = HistoryEvent(object_id=entity.id,
                             object_type=entity.__class__.__name__,
                             event_type=HistoryEvent.CREATE)
        event.save()

    @staticmethod
    def add_update(entity, field_name, field_old_value, field_new_value):
        assert entity
        assert field_name

        event = HistoryEvent(object_id=entity.id,
                             object_type=entity.__class__.__name__,
                             field_name=field_name,
                             field_old_value=field_old_value,
                             field_new_value=field_new_value,
                             event_type=HistoryEvent.UPDATE)
        event.save()

    @staticmethod
    def add_delete(entity):
        assert entity

        event = HistoryEvent(object_id=entity.id,
                             object_type=entity.__class__.__name__,
                             event_type=HistoryEvent.DELETE)
        event.save()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = timezone.now()

        super(HistoryEvent, self).save(*args, **kwargs)


@receiver(post_init)
def resource_post_init(sender, instance, **kwargs):
    if not hasattr(sender, 'HISTORY_FIELDS'):
        return

    for field in sender.HISTORY_FIELDS:
        value = getattr(instance, field)
        setattr(instance, '_original_%s' % field, value)

        logger.debug("POST INIT: %s %s %s" % (instance, field, value))


@receiver(post_save)
def resource_post_save(sender, instance, created, **kwargs):
    if not hasattr(sender, 'HISTORY_FIELDS'):
        return

    if created:
        HistoryEvent.add_create(instance)

        for field in sender.HISTORY_FIELDS:
            value = getattr(instance, field)

            if value:
                HistoryEvent.add_update(instance, field, None, value)
    else:
        for field in sender.HISTORY_FIELDS:
            value = getattr(instance, field)
            history_field = '_original_%s' % field

            logger.debug("POST SAVE: %s %s %s" % (instance, field, value))

            if hasattr(instance, history_field):
                orig_value = getattr(instance, history_field)

                logger.debug("    original value: %s" % orig_value)

                if "%s" % value != "%s" % orig_value:
                    HistoryEvent.add_update(instance, field, orig_value, value)
                    setattr(instance, '_original_%s' % field, value)


@receiver(post_delete)
def resource_post_delete(sender, instance, **kwargs):
    if not hasattr(sender, 'HISTORY_FIELDS'):
        return

    HistoryEvent.add_delete(instance)


@receiver(post_init, sender=ResourceOption)
def resource_option_post_init(sender, instance, **kwargs):
    setattr(instance, '_original_value', instance.value)


@receiver(post_save, sender=ResourceOption)
def resource_option_post_save(sender, instance, created, **kwargs):
    field_name = instance.name
    field_new_value = instance.value

    # ability to ignore some fields (such as heartbeat), to prevent event table flooding.
    if not instance.journaling:
        return

    history_field = '_original_value'
    if hasattr(instance, history_field):
        field_old_value = getattr(instance, history_field)
        if "%s" % field_new_value != "%s" % field_old_value or created:
            field_old_value = None if created else field_old_value
            HistoryEvent.add_update(instance.resource, field_name, field_old_value, field_new_value)
