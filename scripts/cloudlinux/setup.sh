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

set -e
set -u

if [ -z $1 ]; then
	echo "activation_key?"
	exit 1
fi

activation_key=$1

bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/default.sh)

wget http://repo.cloudlinux.com/cloudlinux/sources/cln/cldeploy
sh cldeploy -k ${activation_key}
yum -y install lvemanager
yum -y install cagefs
/usr/sbin/cagefsctl --init
yum -y groupinstall alt-php
yum -y update cagefs lvemanager

echo "Don't forget to reboot"

exit 0
