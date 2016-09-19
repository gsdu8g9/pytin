from __future__ import unicode_literals

from django.apps import AppConfig


class Config(AppConfig):
    name = 'events'
    verbose_name = 'Events app config'

    def ready(self):
        pass
