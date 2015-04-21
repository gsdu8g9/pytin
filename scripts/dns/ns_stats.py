#!/usr/bin/python

#
# Script used to create NS usage stats for the domain list.
#
# In JustHost.ru we are using it to find top NS list to identify
# our top competitors.
#
# If the client is delegated his domain to us and then delegated it
# to another hosting company, we must find where our clients go most
# and investigate it.
#
# Using foreign DNS 8.8.8.8 is important, because if own DNS is used,
# you get wrong stats.
#
# Usage:
# ns_stats.py domains.list
#
# domains.list contains plain list of domains:
#
# domain1.com
# domain2.com
# domain3.com
# ....
#

import os
import sys
import re
import operator
import exceptions
from subprocess import Popen, PIPE


if len(sys.argv) < 2:
    raise Exception('Specify domains list file')

domains_list_file = sys.argv[1]

if not os.path.exists(domains_list_file):
    raise exceptions.OSError("domains_list_file")

with open(domains_list_file, 'r') as f:
    ns_rating = {}

    for line in f:
        line = line.strip()

        print "Query domain: %s" % line
        output = Popen(["nslookup", "-q=ns", line, "8.8.8.8"], stdout=PIPE).communicate()[0]

        for ns in re.finditer('nameserver\s+=\s+([^\s]+)', output.strip()):
            nserver = ns.group(1)

            if nserver not in ns_rating.keys():
                ns_rating[nserver] = 1
            else:
                ns_rating[nserver] += 1

    sorted_rating = sorted(ns_rating.items(), key=operator.itemgetter(1), reverse=True)

    print "**********"
    for ns, cnt in sorted_rating:
        print "%s\t%s" % (ns, cnt)
