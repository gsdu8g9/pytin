#!/bin/bash

#
# Balance chfiles.php usage by cron, to reduce server load
#

USERSDIR=/usr/local/directadmin/data/users
CRON_SPOOL=/var/spool/cron

for userDir in ${USERSDIR}/*; do
    if [ -d ${userDir} ]
    then
        RES=`cat ${userDir}/crontab.conf 2>/dev/null | grep chfiles.php`

        if [ ! -z "${RES}" ]
        then
            echo ${userDir}/crontab.conf "have chfiles.php defined"

            USERNAME=$(basename ${userDir})

            RND=$(php -r "echo rand(0,59);")

            echo "Balance DirectAdmin cron config"
            cp ${userDir}/crontab.conf ${userDir}/crontab.conf.bkp
            perl -p -i -e 's/^(\d+)=(\d+)\s/$1='${RND}' /g' ${userDir}/crontab.conf

            echo "Balance current cron config"
            perl -p -i -e 's/^(\d+)\s/'${RND}' /g' ${CRON_SPOOL}/${USERNAME}
        fi
    fi
done
