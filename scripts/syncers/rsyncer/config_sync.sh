#!/bin/bash

set -e
set -u

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
#
#
# Description:
#   Run script manually or by cron to sync files, listed in sync_files.list.
#   And if changed, perform some actions, like service restart.
#   Must be run from inside the script dir.
#
#   You must exchange with ssh keys with SSH_MASTER_HOST.
#
# Requirements:
#   rsync
#

echo "*** BEGIN"

### Config section ###
SSH_MASTER_HOST=  # user@host
CONFIG_TARGET=/

# change in this file triggers some actions
FLAG_FILE= # such as /etc/nginx/maps.conf



### Do not change
if [ -z ${SSH_MASTER_HOST} ];
then
    echo "MASTER_NODE? Usually user@host"
    exit 1
fi

if [ -z ${FLAG_FILE} ];
then
    echo "FLAG_FILE? Usually some config file"
    exit 1
fi


WORK_DIR=$(pwd)
TMP_TARGET=${WORK_DIR}/master_config.$(date +%s)
FILE_LIST_NAME=${WORK_DIR}/sync_files.list
LAST_RUN_FILE=${WORK_DIR}/last_run

mkdir -p ${TMP_TARGET}

# sync
rsync -vut --progress --recursive --files-from=${FILE_LIST_NAME} -e ssh ${SSH_MASTER_HOST}:/ ${TMP_TARGET}
cp -rf ${TMP_TARGET}/* ${CONFIG_TARGET}

# check times
if [ ! -e ${LAST_RUN_FILE} ];
then
    touch ${LAST_RUN_FILE}
fi

last_run_time=$(stat -c "%Z" ${LAST_RUN_FILE})
config_changed_time=$(stat -c "%Z" ${TMP_TARGET}/etc/nginx/maps.conf)

# update last run time as soon as possible!
touch ${LAST_RUN_FILE}

echo "if changed: $config_changed_time > lastrun: $last_run_time then Restart"

if (( $config_changed_time > $last_run_time ))
then
    source ${WORK_DIR}/actions.sh
fi

echo "*** END"

exit 0
