Cloud management module
=======================

Install
-------

pip install pyzabbix


settings.py
-----------

ZABBIX_APP = {
    'SERVER_URL': 'http://127.0.0.1/',
    'USER': 'Admin',
    'PASSWORD': 'zabbix'
}


CLI
---

В целях интеграции, существует возможность передавать значения метрик из Zabbix в аттрибуты объектов CMDB.
После привязки будет создан аттрибут ATTRIBUTE ноды ID в CMDB.
./manage.py zabbixctl metric --zbx-item ITEM-ID --cmdb-node ID --populate ATTRIBUTE


Автоматически опросить все привязанные метрики и обновить аттрибуты объектов в CMDB.
./manage.py zabbixctl metric --auto-poll
