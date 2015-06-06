#!/usr/bin/env bash

# Copyright (C) 2015 JustHost.ru, Alex Remizoff
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
#   Script used to test DNS every 5 seconds
#
# Usage:
#   zbx_check_dns.sh
#

TEST_DOMAIN="justhost.ru"
DNS1="46.17.40.200"
DNS2="46.17.46.200"

pidfile=/var/run/dnschk.pid

pid=`echo $$`
oldpid=`cat ${pidfile}`

# Checks process of runnig
if ps -p ${oldpid} > /dev/null 2>&1
then
	echo "Check DNS alredy running"
	exit 0
else
    # Write pid to file
    echo ${pid} > ${pidfile}

    while [ 1 ]; do
        /usr/bin/nslookup ${TEST_DOMAIN} ${DNS1} > /dev/null 2>&1

        zabbix_sender -z 127.0.0.1 -p 10051 -s "DNS ${TEST_DOMAIN}" -k baxetns1 -o $?

        /usr/bin/nslookup ${TEST_DOMAIN} ${DNS2} > /dev/null 2>&1

        zabbix_sender -z 127.0.0.1 -p 10051 -s "DNS ${TEST_DOMAIN}" -k baxetns2 -o $?

        sleep 5
    done
fi
