#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
#   Дополнение Brute Force Detection (BFD)
#
# Requirements:
#   CentOS 6

import datetime
import re
import sys
import argparse
import traceback
import os
import sqlite3

from iplist import IPList
from ddos_stat import DDoSStat
from data_provider import DataProvider
from nginx_log_data_provider import NginxLogDataProvider
from apache_log_data_provider import ApacheLogDataProvider
from clsDDoSAnalizer import DDoSAnalizer

def main():
    # PID
    pid = str(os.getpid())

    parser = argparse.ArgumentParser(description='DDoS log parser',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--limit", dest="limitrequests", type=int, default=10,
        help="Лимит запросов с одного IP к одному домену")

    args = parser.parse_args()

#    print str(sys.stdin.readline())
    dataprovider = NginxLogDataProvider(sys.stdin)
    ddos_analizer = DDoSAnalizer(dataprovider)
    ddos_analizer.start()
    stat = ddos_analizer.stat
    for log in stat.loglist:
        if log[4] > args.limitrequests:
            print stat.IPs.iplist[log[1]][1] + ":" + str(log[4]) + ":" + stat.Domains.domainlist[log[2]][1]

    exit(0)

    args = parser.parse_args()

    # Проверка переданных параметров
    if args.pidfile:
        if os.path.isfile(args.pidfile):
            print "%s already exists, exiting" % args.pidfile
            sys.exit()
        else:
            file(args.pidfile, 'w').write(pid)
    if not os.path.exists(args.log_file):
        raise Exception("Лог-файл не существует: %s" % args.log_file)
    if args.database:
        if os.path.exists(args.database):
            raise Exception("Файл БД существует: %s" % args.database)

    # Описание переменных
    # Список исключённых IP
    excludeip = ''

    iplist = []
    hostlist = []

    # Инициализация провайдера данных
    dataprovider = None
    if args.type_file == 'nginx':
        dataprovider = NginxLogDataProvider(args.log_file)
    elif args.type_file == 'apache':
        dataprovider = ApacheLogDataProvider(args.log_file)
    # Инициализация анализатора и его запуск
    ddos_analizer = DDoSAnalizer(dataprovider)
    ddos_analizer.start()

    # Получить данные
    stat = ddos_analizer.stat

    # Вывод статистики
    if args.statistics:
        stat.statistics(args.outfile, int(args.limitrequests))

    # Test вывод в централизованную базу
    if os.path.exists("./list.py"):
        execfile("./list.py")

    outfile = open(args.blockpath + '/blocklist.py', "w")
    outfile.write('blocklist = [')
    for log in stat.loglist:
        if log[4] > args.limitrequests:
            outfile.write("{'ip': '" + stat.IPs.iplist[log[1]][1] + "', 'count': '" + str(log[4]) + "'},\n")
    outfile.write(']')
    outfile.close()

    # Заблокировать
    if args.blockpath and args.limitrequests > 0:
        if not os.path.isdir(args.blockpath):
            raise Exception("Путь не существует: %s" % args.blockpath)
        outfile = open(args.blockpath + '/block_' + datetime.datetime.now().strftime('%Y%m%d%H%M'), "w")
        outfile.write('#!/bin/bash\n')
        for log in stat.loglist:
            if log[4] > args.limitrequests:
                outfile.write("iptables -A INPUT -s " + stat.IPs.iplist[log[1]][1] +" -j DROP -m comment --comment 'pytin'" + '\n')
        outfile.write('rm ' + args.blockpath + '/block_' + datetime.datetime.now().strftime('%Y%m%d%H%M') + '\n')
        outfile.close()
        outfile = open(args.blockpath + '/unblock_' + datetime.datetime.now().strftime('%Y%m%d%H%M'), "w")
        outfile.write('#!/bin/bash\n')
        futuredate = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime('%Y%m%d%H%M')
        outfile.write('cond="' + futuredate + '"\n')
        outfile.write('if [[ `date +%Y%m%d%H%M` < $cond ]]; then\n')
        outfile.write('exit\n')
        outfile.write('fi\n')
        for log in stat.loglist:
            if log[4] > args.limitrequests:
                outfile.write("iptables -D INPUT -s " + stat.IPs.iplist[log[1]][1] +" -j DROP -m comment --comment 'pytin'" + '\n')
        outfile.write('rm ' + args.blockpath + '/unblock_' + datetime.datetime.now().strftime('%Y%m%d%H%M') + '\n')
        outfile.close()

    if args.pidfile:
        os.unlink(args.pidfile)

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
