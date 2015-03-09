# Copyright (C) 2015 JustHost.ru
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND JUSTHOST.RU DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL JUSTHOST.RU BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# Based on dnspython library (http://www.dnspython.org/docs/1.12.0/)

import exceptions
import os
import sys

import dns.zone
import dns.rdata
import dns.rdataset


####################
#
# Config and run
#
####################
node_updates = [
    {
        'nodes': ['pop', 'smtp', 'mail', 'ftp', 'ssh', 'pop.mn1', 'smtp.mn1', 'mail.mn1', 'ftp.mn1', 'ssh.mn1'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.A,
        'value': '46.29.160.31',
    },
    {
        'nodes': ['pop', 'smtp', 'mail', 'ftp', 'ssh', 'pop.mn1', 'smtp.mn1', 'mail.mn1', 'ftp.mn1', 'ssh.mn1'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.AAAA,
        'value': '2a00:b700:1::31',
    },
    {
        'nodes': ['@'],
        'class': dns.rdataclass.IN,
        'type': dns.rdatatype.TXT,
        'value': 'v=spf1 a mx ip4:46.29.160.31 ~all',
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
            zone_dataset.items[0] = rdata_item
        else:
            zone_dataset.add(rdata_item, ttl=14400)

    def save(self):
        self.dns_zone.to_file(self.db_file_path)



if len(sys.argv) < 2:
    raise Exception('Specify bind db file')

dns_file = BindDbFileUpdater(sys.argv[1])

for update_info in node_updates:
    for node_name in update_info['nodes']:
        dns_file.update_node(node_name, update_info['class'], update_info['type'], update_info['value'])

dns_file.save()