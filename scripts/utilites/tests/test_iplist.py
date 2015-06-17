##!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os
import unittest
import sys
import re
sys.path.append('../')

from iplist import IPList

class TestIPList(unittest.TestCase):

    def test_isRFC(self):
        analize = IPList()
        self.assertEqual(analize.isRFC('192.168.255.254'), True)
        self.assertEqual(analize.isRFC('10.0.255.254'), True)
        self.assertEqual(analize.isRFC('172.16.0.1'), True)
        self.assertEqual(analize.isRFC('8.8.8.8'), False)

if __name__ == '__main__':
    unittest.main()
