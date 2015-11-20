from django.db import models

from resources.models import ResourceOption


class ZabbixMetric(models.Model):
    cmdb_node_option = models.ForeignKey(ResourceOption)
    zbx_metric_id = models.IntegerField('Metric ID from Zabbix.', db_index=True)

    def __unicode__(self):
        return "%s -> %s=%s (%s)" % (
            self.zbx_metric_id, self.cmdb_node_option.name, self.cmdb_node_option.value, self.cmdb_node_option.format)
