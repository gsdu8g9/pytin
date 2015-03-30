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
#
# Script is used to update DNS zones in NAMED format.
# All config parameters are in dns_updater.py script
#
# Usage:
# dns_update.sh /path/to/named/zone/files

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

    # standartized way
    perl -pi -e 's/@ 14400 IN SOA/@ IN SOA/g' ${db_file}
    perl -pi -e 's/ ([\d ]+)$/ \($1\)/g' ${db_file}

done


exit 0
