#!/usr/bin/env bash

# Copyright (C) 2015 JustHost.ru, Dmitry Shilyaev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Description:
#   Script used to backup Zabbix server
#
# Usage:
#   zbx_backup.sh /path/to/backup
#

if [[ -z $1 ]]
then
	echo "ERROR: Need to specify target"
	exit 1
fi

timestamp() {
	echo $(date +%s)
}

ZBX_DB_NAME=zabbix_db
ZBX_DB_USER=zabbix_user
ZBX_DB_PASSWORD=dbpassword
OLD_THAN_DAYS=10

TIME_STAMP=$(timestamp)
BACKUP_DIR=$1/backups
BACKUP_TMP_DIR=${BACKUP_DIR}/zabbix-backup.${TIME_STAMP}

prepareTarget() {
	/bin/find ${BACKUP_DIR} -type f -mtime +${OLD_THAN_DAYS} -exec rm -f {} \;

	if [[ ! -d ${BACKUP_TMP_DIR} ]]
	then
		mkdir -p ${BACKUP_TMP_DIR}
	fi
}

dumpDatabases() {
	echo "Dumping zabbix database"
	/etc/init.d/zabbix-server stop
	/usr/bin/mysqldump -h localhost -u ${ZBX_DB_USER} -p{ZBX_DB_PASSWORD} ${ZBX_DB_NAME} > ${BACKUP_TMP_DIR}/${ZBX_DB_NAME}.sql
	/etc/init.d/zabbix-server start
}

archiveData() {
	CURR_DIR=$(pwd)
	ARCH_NAME=${BACKUP_TMP_DIR}.tar.gz

	cd ${BACKUP_TMP_DIR}

	echo "Create archive " ${ARCH_NAME}
	/bin/tar czhf ${ARCH_NAME} ./*

	cd ${CURR_DIR}

	rm -rf ${BACKUP_TMP_DIR}
}

echo "Target backups dir: " ${BACKUP_TMP_DIR}

prepareTarget
dumpDatabases
archiveData

echo "Done"
