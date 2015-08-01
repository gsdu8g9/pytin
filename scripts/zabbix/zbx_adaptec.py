#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
#   Информация от Adaptec
#
# Requirements:
#   Adaptec

import argparse
import os
import re
import subprocess
import sys
import traceback

dict_re = {'logdevnum': '^Logical device number ([0-9]+).*$',
    'status': '^\s*Status of logical device\s*:\s*(.*)$',
    'temperature': '^\s*Temperature\s*:\s*([0-9]+).*$',
    'level': '^\s*RAID level\s*:\s*([0-9]+).*$',
    'model': '^\s*Controller Model\s*:\s*(.*)$'}

cmd_arcconf = '/usr/bin/arcconf'
cmd_arcconf = '/usr/bin/arcconf'

def main():
    parser = argparse.ArgumentParser(description='Adaptec parser',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--test", dest="test", action='store_true', help="Тестовый режим из файла")
    group1 = parser.add_argument_group('Команды')
    mutex_group1 = group1.add_mutually_exclusive_group(required=True)
    mutex_group1.add_argument("--model", dest="model", action='store_true', help="Модель контроллера")
    mutex_group1.add_argument("--status", dest="status", action='store_true', help="Статус логического устройства")
    mutex_group1.add_argument("--temperature", dest="temperature", action='store_true', help="Температура контроллера")
    mutex_group1.add_argument("--level", dest="level", action='store_true', help="Уровень RAID")

    args = parser.parse_args()

    outinfo = None
    if args.test:
        outinfo = subprocess.Popen(['cat', 'test/output.txt'], stdout=subprocess.PIPE)
    else:
        outinfo = subprocess.Popen(['sudo', cmd_arcconf, 'getconfig', '1', 'al'], stdout=subprocess.PIPE)
    for line in outinfo.stdout.readlines():
        line = line.replace("\n", "")
        lstatus = None
        if args.model:
            lstatus = re.findall(dict_re['model'], line)
        elif args.status:
            lstatus = re.findall(dict_re['status'], line)
            if lstatus == 'Optimal':
                lstatus = 1
        elif args.temperature:
            lstatus = re.findall(dict_re['temperature'], line)
        elif args.level:
            lstatus = re.findall(dict_re['level'], line)
        if lstatus:
            if str(lstatus[0]) == 'Optimal':
                print '1'
            else:
                print str(lstatus[0])

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
