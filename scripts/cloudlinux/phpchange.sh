#!/bin/bash

#
# Change PHP version from Native to DEFAULT_PHP for all users
#

DEFAULT_PHP="5.2"

for user in `ls /home`;
do
    userDir=/home/${user}
    if [[ -f ${userDir}/.cl.selector/defaults.cfg ]]
        then
        phpv=`cat ${userDir}/.cl.selector/defaults.cfg | grep "php="`

        if [ $phpv == "php=native" ];
        then
            echo ${user}: ${phpv} "-> " ${DEFAULT_PHP}
            /usr/bin/cl-selector --user=${user} --select=php --version=${DEFAULT_PHP}
        fi
    fi
done
