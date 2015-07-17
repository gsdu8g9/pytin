import unittest

from lib.nginx_log_parser import NginxLogParser
from lib.data_providers import FileDataProvider


class TestDDoSAnalizer(unittest.TestCase):
    def test_dict_test(self):
        dict = {
            'dom1': {
                'ip1': 5,
                'ip2': 7,
                'ip3': 10,
            },
            'dom2': {
                'ip4': 5,
                'ip2': 70,
                'ip7': 10,
            },
            'dom3': {
                'ip3': 5,
                'ip2': 3,
                'ip9': 10,
            }
        }

        print dict.values()

    def test_parse_minilog(self):
        minilog = 'tests/access.log-mini'

        log_parser = NginxLogParser(FileDataProvider(minilog))

        records_list = list(log_parser)

        self.assertEqual('46.118.121.72', records_list[0].ip)
        self.assertEqual(302, records_list[0].http_code)
        self.assertEqual('razdacha-akkauntov.ru', records_list[0].domain)

        self.assertEqual('201.254.106.234', records_list[261].ip)
        self.assertEqual(200, records_list[261].http_code)
        self.assertEqual('provoloka34.ru', records_list[261].domain)


if __name__ == '__main__':
    unittest.main()
