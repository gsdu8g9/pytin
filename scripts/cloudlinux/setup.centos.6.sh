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
#   Script used to convert existing system to CloudLinux
#
# wget https://raw.githubusercontent.com/servancho/pytin/master/scripts/cloudlinux/setup.sh
# bash setup.sh <activation_key>
#

set -u
set -e

if [ ! -e ./firstrun ]; then
    if [ -z $1 ]; then
        echo "activation_key?"
        exit 1
    fi

    activation_key=$1

    bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)

    wget http://repo.cloudlinux.com/cloudlinux/sources/cln/cldeploy
    sh cldeploy -k ${activation_key}
    echo "[!!!] Don't forget to reboot and run this script again."

    echo "1" > ./firstrun
else
    yum -y install lvemanager cagefs
    cagefsctl --init

    yum -y groupinstall alt-php

    yum update cagefs lvemanager

    cagefsctl --force-update

    if [ -e /usr/local/directadmin ]; then
        /usr/local/directadmin/custombuild/build set suphp yes
        /usr/local/directadmin/custombuild/build set cloudlinux yes
        /usr/local/directadmin/custombuild/build update
        /usr/local/directadmin/custombuild/build apache
        /usr/local/directadmin/custombuild/build php y
        /usr/local/directadmin/custombuild/build suphp
        /usr/local/directadmin/custombuild/build rewrite_confs

        rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
        yum -y install epel-release
        rpm -Uvh http://li.nux.ro/download/nux/dextop/el6/x86_64/nux-dextop-release-0-2.el6.nux.noarch.rpm
        yum install ffmpeg ffmpeg-devel
        yum install alt-php*ffmpeg

        cagefsctl --force-update
        cagefsctl --remount-all
    fi

    echo "[!] Don't forget to reboot."

    rm -f ./firstrun
fi

exit 0
