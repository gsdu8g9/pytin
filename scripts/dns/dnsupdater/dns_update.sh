#!/bin/bash

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

# Description:
#
# Script is used to update DNS zones in NAMED format.
# All config parameters are in dns_updater.py script
#
# Usage:
# dns_update.sh /path/to/db/files /path/to/named/domains.list

if [ -z $1 ];
then
    echo "Specify path to the zone DB files."
    exit 1
fi

NAMED_ZONES_PATH=$1
DOMAINS_LIST_FILE=

if [ ! -z $2 ];
then
    echo "Using domain list: $2"
    DOMAINS_LIST_FILE=$2
fi

SAVED_DB_PATH=${NAMED_ZONES_PATH}/$(date +"%s")
mkdir -p ${SAVED_DB_PATH}

for zone_db in `ls ${NAMED_ZONES_PATH}/*.db`; do
    if [ "${zone_db}" != "" ];
    then
        db_file=${zone_db}
        domain_name=$(basename ${db_file} .db)

        if [ -e ${db_file} ]; then
            if [ ! -z ${DOMAINS_LIST_FILE} ]; then
                exists=$(cat ${DOMAINS_LIST_FILE} | grep "^$domain_name$")

                if [ -z ${exists} ]; then
                    continue
                fi
            fi

            echo "Updating:" ${db_file} "(${domain_name})"

            cp ${db_file} ${SAVED_DB_PATH}/$(basename ${db_file})

            python dns_updater.py ${db_file}

            # Fix for DirectAdmin
            perl -pi -e 's/[^ ]+ \d+ IN SOA/@ IN SOA/g' ${db_file}
            perl -pi -e 's/ ([\d ]+)$/ \($1\)/g' ${db_file}
        else
            echo "Missing file: " ${db_file}
        fi
    fi
done


exit 0
