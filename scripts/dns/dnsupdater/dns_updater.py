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
#
# Based on dnspython library (http://www.dnspython.org/docs/1.12.0/)
#
# $ pip install dnspython
#
# This script is used to update DNS zone in NAMED format.
# All config parameters are in node_updates array
#
# Usage:
# dns_updater.py /path/to/named/zone.db

from __future__ import unicode_literals

import exceptions
import os
import sys

import dns.zone
import dns.rdata
import dns.rdataset




####################
#
# Config and run
# Use @ for domain main A-record
#
####################

# change only this IPs
subject_ips = [
    '1.2.3.4',
    '1.2.3.5',
    '1.2.3.6',
    'aa00:b00b:1::2',
    'aa00:b00b:1::3'
]

# define substitutions
# record classes and data types defined in dns.rdataclass and dns.rdatatype
node_updates = [
    {
        'nodes': ['pop', 'smtp', 'mail'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.A,
        'value': '1.2.3.7',
    },

    {
        'nodes': ['ftp'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.A,
        'value': '1.2.3.8',
    },
    {
        'nodes': ['ssh'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.A,
        'value': '1.2.3.9',
    },

    {
        'nodes': ['pop', 'smtp', 'mail'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.AAAA,
        'value': 'aa00:b00b:1::4',
    },

    {
        'nodes': ['ftp'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.AAAA,
        'value': 'aa00:b00b:1::5',
    },

    {
        'nodes': ['ssh'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.AAAA,
        'value': 'aa00:b00b:1::6',
    },
]


class BindDbFileUpdater:
    db_file_path = ''
    zone = ''
    dns_zone = None

    def __init__(self, db_file_path):
        if not db_file_path:
            raise exceptions.ValueError("db_file_path")

        if not os.path.exists(db_file_path):
            raise exceptions.OSError("db_file_path")

        if not db_file_path.endswith('.db'):
            raise exceptions.ValueError("db_file_path")

        self.db_file_path = db_file_path
        self.zone = os.path.basename(db_file_path)[:-3]

        self._load_zone()

    def _load_zone(self):
        self.dns_zone = dns.zone.from_file(self.db_file_path, self.zone)

    def update_node(self, node_name, rdclass, rdtype, rdvalue):
        zone_dataset = self.dns_zone.find_rdataset(node_name, rdtype=rdtype, create=True)

        rdata_type = dns.rdata.get_rdata_class(rdclass, rdtype)
        rdata_item = rdata_type(rdclass, rdtype, rdvalue)

        if len(zone_dataset) > 0:
            if unicode(zone_dataset.items[0]) in subject_ips:
                zone_dataset.items[0] = rdata_item
        else:
            zone_dataset.add(rdata_item, ttl=14400)

    def save(self):
        self.dns_zone.to_file(self.db_file_path, relativize=False)


if len(sys.argv) < 2:
    raise Exception('Specify bind db file')

dns_file = BindDbFileUpdater(sys.argv[1])

for update_info in node_updates:
    for node_name in update_info['nodes']:
        dns_file.update_node(node_name, update_info['class'], update_info['type'], update_info['value'])

dns_file.save()