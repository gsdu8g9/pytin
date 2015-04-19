#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт обновления свежеустановленной ОС CentOS
#	и настройки для быстрого поиска по истории команд
#
# Requirements:
#	CentOS 6/7

yum clean all
yum -y update
yum -y install nano wget ntp mc

rm -f /etc/localtime
ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime

/etc/init.d/ntpd stop
ntpdate pool.ntp.org
chkconfig ntpd on
/etc/init.d/ntpd restart

sed -e "s/\e\[5~/\e\[A/g" /etc/inputrc > /tmp/inputrc
sed -e "s/\e\[6~/\e[B/g" /tmp/inputrc > /etc/inputrc
