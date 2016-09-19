from __future__ import unicode_literals

from django.apps import AppConfig


class Config(AppConfig):
    name = 'cmdb'
    verbose_name = 'CMDB app config'

    def ready(self):
        pass
