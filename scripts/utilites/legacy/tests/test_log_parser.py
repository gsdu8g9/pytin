##!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import unittest

from clsDDoSAnalizer import DDoSAnalizer


class TestDDoSAnalizer(unittest.TestCase):
    def test_get_log_value(self):
        line = '5.61.38.35 - - [08/May/2015:03:32:59 +0300] "GET /contact.html HTTP/1.1" "200" 4902 "seotron.ru/contact.html" "URLGrabber" "-" seotron.ru'
        analize = DDoSAnalizer(None, 'nginx', 10)
        self.assertEqual(analize._get_log_value(line), ['5.61.38.35',
                                                        '-',
                                                        '-',
                                                        '[08/May/2015:03:32:59 +0300]',
                                                        '"GET /contact.html HTTP/1.1"',
                                                        '"200"',
                                                        '4902',
                                                        '"seotron.ru/contact.html"',
                                                        '"URLGrabber"',
                                                        '"-"',
                                                        'seotron.ru'])


if __name__ == '__main__':
    unittest.main()
