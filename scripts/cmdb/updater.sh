#!/usr/bin/env bash

set -e

# Script used to update CMDB data

IFS=$'\n'

for resource_id in $(./manage.py cmdbctl list type__in=Server type__in=VirtualServer | grep -Po '^\s+(\K\d+)')
do
    echo "Update server" ${resource_id} "parent ID"

    ./manage.py cmdbctl set -n=parent -v=0 ${resource_id}
done

exit 0
