#!/bin/bash

# Script used to check that specified IPs are responding to ping.
# Usage: check_ips.sh ip_list_file.txt

if [ -z $1 ]; then
	echo "IP list file?"
	exit 1
fi

IP_LIST=$1

while read ipaddr; do
	if [ ${ipaddr} != "" ]; then
		
		ping -c 1 ${ipaddr} >/dev/null 2>&1
		if [ -z $? ]; then
			echo ${ipaddr} "    BUSY"
		else
			echo ${ipaddr} "    FREE"
		fi
	fi
done <${IP_LIST}

exit 0
