#!/bin/sh

apt-get install python-argparse sudo

wget http://repo.zabbix.com/zabbix/2.2/debian/pool/main/z/zabbix/zabbix-agent_2.2.10-1+squeeze_amd64.deb
dpkg -i zabbix-agent_2.2.10-1+squeeze_amd64.deb

# wget http://repo.zabbix.com/zabbix/2.2/rhel/6/x86_64/zabbix-2.2.10-1.el6.x86_64.rpm
# rpm -i zabbix-2.2.10-1.el6.x86_64.rpm

# arcconf location
arcpath=`whereis arcconf | awk '{ print $2; }'`

# /etc/sudoers.d/arcconf
# Cmnd_Alias ARCCONF_GETCONFIG = /sbin/arcconf getconfig *, /sbin/arcconf getversion
# zabbix ALL=(root) NOPASSWD: ARCCONF_GETCONFIG

# /etc/sudoers.d/zpoolconf
# Cmnd_Alias ZPOOL_STATUS = /sbin/zpool status, /sbin/zpool list
# zabbix ALL=(root) NOPASSWD: ZPOOL_STATUS

echo 'Cmnd_Alias ARCCONF_GETCONFIG = '$arcpath' getconfig *, '$arcpath' getversion' > /etc/sudoers.d/arcconf
echo 'zabbix ALL=(root) NOPASSWD: ARCCONF_GETCONFIG' >> /etc/sudoers.d/arcconf
chmod 0440 /etc/sudoers.d/arcconf

cd /etc/zabbix

wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/zabbix/zbx_adaptec.py
wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/zabbix/conf/adaptec.conf

mv adaptec.conf zabbix_agentd.d/

chmod +x /etc/zabbix/zbx_adaptec.py

service zabbix-agent restart
