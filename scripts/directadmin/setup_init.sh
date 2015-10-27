#!/usr/bin/env bash

(
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/directadmin/setup_da.sh)
) 2>> /root/setup.err | tee -a /root/setup.log
chmod o-r,g-r setup.*
