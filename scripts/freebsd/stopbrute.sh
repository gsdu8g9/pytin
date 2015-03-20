#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт добавления в чёрный список IP, замеченных в брутфорсе
#
# Requirements:
#	FreeBSD

PATH=/etc:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/home/user

/home/user/log.py | /etc/badguys.sh check | grep -v Russian | grep -E -o '[0-9]{1,3}(\.[0-9]{1,3}){3}' >> /etc/badguys.list

/etc/badguys.sh
