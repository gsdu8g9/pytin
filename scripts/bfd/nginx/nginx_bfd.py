import sys
import argparse
import traceback
import os
import operator

from lib.data_providers import StdInDataProvider, FileDataProvider
from lib.nginx_log_parser import NginxLogParser


def enter_pid_lock(lock_file):
    assert lock_file

    if os.path.exists(lock_file):
        sys.exit()

    pid = str(os.getpid())
    file(lock_file, 'w').write(pid)


def exit_pid_lock(lock_file):
    assert lock_file

    if os.path.exists(lock_file):
        os.remove(lock_file)


def main():
    known_formats = {
        'nginx': NginxLogParser
    }

    parser = argparse.ArgumentParser(description='DDoS log parser',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-p", dest="pidfile", required=True, metavar="pid-file", help="PID lock file")
    parser.add_argument("-f", "--format", dest="log_format", choices=known_formats.keys(),
                        required=True, help="Log file format.")

    group1 = parser.add_argument_group('Parser parameters.')
    mutex_group1 = group1.add_mutually_exclusive_group()
    mutex_group1.add_argument("--stdin", dest="stdin", action='store_true', help="Data from stdin")
    mutex_group1.add_argument("-l", "--log", dest="log_file", help="Log file to process.")

    args = parser.parse_args()

    try:
        enter_pid_lock(args.pidfile)

        parser_impl_class = known_formats[args.log_format]

        if args.stdin:
            data_provider = StdInDataProvider()
        else:
            data_provider = FileDataProvider(args.log_file)

        log_parser = parser_impl_class(data_provider)

        parsed_data_map = {}
        for log_record in log_parser:
            if log_record.domain not in parsed_data_map:
                parsed_data_map[log_record.domain] = {}

            if log_record.ip not in parsed_data_map[log_record.domain]:
                parsed_data_map[log_record.domain][log_record.ip] = 0

            parsed_data_map[log_record.domain][log_record.ip] += 1

        # find top request IPs
        sorted_ips = {}
        for ip_list_item in parsed_data_map.values():
            for ip in ip_list_item:
                if ip not in sorted_ips:
                    sorted_ips[ip] = ip_list_item[ip]
                elif sorted_ips[ip] < ip_list_item[ip]:
                    sorted_ips[ip] = ip_list_item[ip]

        # print resulting touples
        for sorted_ip_touple in sorted(sorted_ips.items(), key=operator.itemgetter(1), reverse=True):
            sys.stdout.write("%s:%s\n" % (sorted_ip_touple[0], sorted_ip_touple[1]))

    finally:
        exit_pid_lock(args.pidfile)


if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
