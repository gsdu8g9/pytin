zbx_adaptec.py - скрипт для контроллеров Adaptec
zbx_zpool.py - скрипт для ZFS пулов

/etc/sudoers.d/zpoolconf

Cmnd_Alias ZPOOL_STATUS = /sbin/zpool status, /sbin/zpool list
zabbix ALL=(root) NOPASSWD: ZPOOL_STATUS

/etc/sudoers.d/arcconf

Cmnd_Alias ARCCONF_GETCONFIG = /sbin/arcconf getconfig *, /sbin/arcconf getversion
zabbix ALL=(root) NOPASSWD: ARCCONF_GETCONFIG
