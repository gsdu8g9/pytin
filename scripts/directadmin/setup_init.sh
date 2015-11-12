#!/usr/bin/env bash

# Description:
#   Install CentoS defaults and DirectAdmin
#
# Requirements:
#	CentOS 6
#
# bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/directadmin/setup_init.sh)
#

(
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/directadmin/setup_da.sh)
) 2>> /root/setup.err | tee -a /root/setup.log
chmod o-r,g-r setup.*
