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
#   Log parser rule for brute force detection tool (BFD)
#

# too many connections
# uncomment to override conf.bfd trig value
TRIG="350"

# file must exist for rule to be active
REQ="/path/to/nginx_access.log"

if [ -f "$REQ" ]; then
 LP=${REQ}
 TLOG_TF="nginx"

 ## nginx
 ARG_VAL=`${TLOG_PATH} ${LP} ${TLOG_TF} | sed -e 's/::ffff://' | grep -E '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | sed -n -e "s/\(.*\) - -.*\" \(.*\)/\1:\2/p"`
fi
