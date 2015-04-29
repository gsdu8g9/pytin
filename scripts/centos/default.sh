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
ntpdate -d ntp1.vniiftri.ru
chkconfig ntpd on
/etc/init.d/ntpd restart

sed -e "s/\e\[5~/\e\[A/g" /etc/inputrc > /tmp/inputrc
sed -e "s/\e\[6~/\e[B/g" /tmp/inputrc > /etc/inputrc

### Install BFD and APF
mkdir secdistr && cd secdistr

mkdir bfd && cd bfd
wget http://www.rfxn.com/downloads/bfd-current.tar.gz
tar --strip-components=1 -xzf bfd-current.tar.gz
./install.sh
cd ..

mkdir apf && cd apf
wget http://www.rfxn.com/downloads/apf-current.tar.gz
tar --strip-components=1 -xzf apf-current.tar.gz
./install.sh
cd ..

cp /etc/apf/conf.apf /etc/apf/conf.apf.bkp
perl -pi -e 's/DEVEL_MODE="1"/DEVEL_MODE="0"/g' /etc/apf/conf.apf
