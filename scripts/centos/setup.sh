#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт обновления свежеустановленной ОС CentOS
#	и настройки для быстрого поиска по истории команд
#
# Requirements:
#	CentOS 6/7
#
# bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)
#

echo "Disable SELinux"
/usr/sbin/setenforce 0

yum clean all
yum -y update
yum -y install man nano wget ntp mc net-tools smartmontools

rm -f /etc/localtime
ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime

service ntpd stop
ntpdate -d ntp1.vniiftri.ru
chkconfig ntpd on
service ntpd restart

sed -e "s/\e\[5~/\e\[A/g" /etc/inputrc > /tmp/inputrc
sed -e "s/\e\[6~/\e[B/g" /tmp/inputrc > /etc/inputrc

if [ ! -e /etc/cron.d ]; then
    yum -y install cronie
fi
