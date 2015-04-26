#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт обновления свежеустановленной ОС Debian или Ubuntu
#	и настройки для быстрого поиска по истории команд
#
# Requirements:
#	Debian/Ubuntu

apt-get -y update
apt-get -y upgrade
apt-get -y install wget nano ntpdate

ntpdate -d ntp1.vniiftri.ru

apt-get -y install ntp

sed -i 's/.*history-search-backward$/"\e[A": history-search-backward/g' /etc/inputrc
sed -i 's/.*history-search-forward$/"\e[B": history-search-forward/g' /etc/inputrc
