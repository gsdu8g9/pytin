##!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os
import unittest
import sys
import datetime
sys.path.append('../')

from nginx_log_data_provider import NginxLogDataProvider

class TestNginxLogDataProvider(unittest.TestCase):
    def test_get_log_value(self):
        dataProvider = NginxLogDataProvider('nginx.log')
        for line in dataProvider:
            self.assertEqual(line,{'date': datetime.datetime(2015, 5, 8, 3, 32),
                'domain': '"seotron.ru/contact.html"',
                'ip': '5.61.38.35'})

if __name__ == '__main__':
    unittest.main()
