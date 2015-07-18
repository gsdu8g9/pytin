import sys
import argparse
import traceback
import os

from lib.data_providers import StdInDataProvider, FileDataProvider
from lib.nginx_log_parser import NginxLogParser
from lib.analyzers import GenericDDoSAnalyzer
from lib.blockers import ApfBlocker


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

    enter_pid_lock(args.pidfile)
    try:
        parser_impl_class = known_formats[args.log_format]

        if args.stdin:
            data_provider = StdInDataProvider()
        else:
            data_provider = FileDataProvider(args.log_file)

        log_parser = parser_impl_class(data_provider)

        analyzer = GenericDDoSAnalyzer(log_parser, threshold=100)
        blocker = ApfBlocker()
        for attacker_ip in analyzer.attacker_ip_list():
            blocker.block(attacker_ip)
            sys.stdout.write("IP %s blocked.\n" % attacker_ip)

    finally:
        exit_pid_lock(args.pidfile)


if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
