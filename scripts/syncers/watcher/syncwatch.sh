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
#
#
# Description:
#   This script monitors some directory for the specific file events via inotifywait
#   and triggers actions.sh script.
#
#
# Requirements:
#   inotify-tools
#

# Monitor this directory and trigger on specific events
WATCH_DIR=/path/to/watch/dir

# Trigger if file with this pattern was created or written in WATCH_DIR
PATTERN=*-sync.log


LOCK_FILE=/tmp/selector-sync.lock
if [[ -f ${LOCK_FILE} ]]
then
    exit 100
fi

trap "{ echo '!!! Clean up'; rm -f ${LOCK_FILE} ; exit 0; }" EXIT
echo "progress" > ${LOCK_FILE}

while true; do
    inotifywait -e close_write --format "%w %f" ${WATCH_DIR} | while read dir file; do
        filename=${dir}${file}
        if [[ "${filename}" == ${PATTERN} ]]
        then
            # note that actions.sh runs in the background
            bash ./actions.sh >sync-actions.log 2>sync-errors.log &
        fi
    done
done
