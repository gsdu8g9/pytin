#!/usr/bin/env bash

DA_USERS=/usr/local/directadmin/data/users

if [ -z $1 ]; then
    echo "Target map file?"
    exit 1
fi

for user in `ls ${DA_USERS}`; do
    domains_list=${DA_USERS}/${user}/domains.list
done
