##!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import unittest
from badguys import IPList

class TestBadguysIPList(unittest.TestCase):
    def test_add(self):
        iplist = IPList()
        self.assertEqual(iplist.Add('8.8.8.8'), '8.8.8.8')
        self.assertEqual(iplist.Add('8.8.4.4'), '8.8.4.4')
        self.assertEqual(iplist.Add('8.8.2.2:'), None)


class TestFW(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
