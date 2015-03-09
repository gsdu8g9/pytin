#!/bin/bash

if [ -z $1 ];
then
    echo "named zones path?"
    exit 1
fi

NAMED_ZONES_PATH=$1

for file in `ls ${NAMED_ZONES_PATH}/*.db`; do

    db_file=${file}

    echo "Updating: " ${db_file}
    python dns_updater.py ${db_file}

done


exit 0
