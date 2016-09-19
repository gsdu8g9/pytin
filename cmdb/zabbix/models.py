from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from resources.models import ResourceOption


@python_2_unicode_compatible
class ZabbixMetric(models.Model):
    cmdb_node_option = models.ForeignKey(ResourceOption)
    zbx_metric_id = models.IntegerField('Metric ID from Zabbix.', db_index=True)

    def __str__(self):
        return "%s -> %s=%s (%s)" % (
            self.zbx_metric_id, self.cmdb_node_option.name, self.cmdb_node_option.value, self.cmdb_node_option.format)
