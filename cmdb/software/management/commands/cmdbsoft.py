# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
from argparse import ArgumentParser

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="Software management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # res_add_cmd = subparsers.add_parser('add', help="Add new resource.")
        # res_add_cmd.add_argument('-t', '--type', default='resources.Resource',
        #                          help="Type of the resource in format 'app.model'.")
        # res_add_cmd.add_argument('fields', nargs=argparse.ONE_OR_MORE, help="Key=Value pairs.")
        # self._register_handler('add', self._handle_command_add)

        for method in dir(self):
            if method.startswith('cmd_'):
                cmd_name = method[4:]
                subparsers.add_parser(cmd_name, help=getattr(self, method))

    def cmd_add_da_license(self, **kwargs):
        print "Adding lic: %s" % kwargs
        pass

    cmd_add_da_license.description = 'This is a descr'

    def handle(self, *args, **options):
        pass
