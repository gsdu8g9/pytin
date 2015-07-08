#!/usr/bin/env bash

set -e

# Script used to update CMDB data

IFS=$'\n'

for resource_id in $(./manage.py cmdbctl search type__in=Server type__in=VirtualServer | grep -Po '^\s+(\K\d+)')
do
    echo "Update server" ${resource_id} "parent ID"

    ./manage.py cmdbctl set ${resource_id} parent=0
done

exit 0
