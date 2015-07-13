#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
# Парсинг журналов Apache и Nginx с выводом статистики
#
# Requirements:
# CentOS 6

import datetime
import re
import sys
import argparse
import traceback
import os
import sqlite3

from iplist import IPList
from ddos_stat import DDoSStat
from nginx_log_data_provider import NginxLogDataProvider
from apache_log_data_provider import ApacheLogDataProvider
from clsDDoSAnalizer import DDoSAnalizer

def main():
    # PID
    pid = str(os.getpid())

    parser = argparse.ArgumentParser(description='DDoS log parser',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-o", "--outfile", dest="outfile", help="Файл для вывода")
    parser.add_argument("-p", dest="pidfile", metavar="pid-file", help="Файл для вывода")
    parser.add_argument("-B", "--block", dest="blockpath", help="Путь для блокировки")
    parser.add_argument("-t", "--type", dest="type_file", choices=["apache", "nginx"],
        required=True, help="Тип парсера")
    parser.add_argument("-D", "--database", dest="database", help="Файл базы данных")
    parser.add_argument("--limit", dest="limitrequests", type=int, default=10,
        help="Лимит запросов с одного IP к одному домену")
    parser.add_argument("-S", "--statistics", dest="statistics", action='store_true',
        help="Вывести статистику")
    group1 = parser.add_argument_group('Команды')
    mutex_group1 = group1.add_mutually_exclusive_group()
    mutex_group1.add_argument("--raw", dest="raw", action='store_true', help="Сырые данные")
    mutex_group1.add_argument("-l", "--log", dest="log_file", help="Лог-файл для анализа")

    args = parser.parse_args()

    # Проверка переданных параметров
    if args.pidfile:
        if os.path.isfile(args.pidfile):
            print "%s already exists, exiting" % args.pidfile
            sys.exit()
        else:
            file(args.pidfile, 'w').write(pid)
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

    # Анализ сырых данных
    if args.raw:
        if args.type_file == 'nginx':
            dataprovider = NginxLogDataProvider(sys.stdin)
        elif args.type_file == 'apache':
            dataprovider = ApacheLogDataProvider(sys.stdin)
        ddos_analizer = DDoSAnalizer(dataprovider)
        ddos_analizer.start()
        stat = ddos_analizer.stat
        tmplist = []
        for log in stat.loglist:
            if log[4] > args.limitrequests:
                if len(tmplist) == 0:
                    tmplist.append([stat.IPs.iplist[log[1]][1], str(log[4])])
                if stat.IPs.iplist[log[1]][1] == tmplist[len(tmplist)-1][0]:
                    if str(log[4]) > tmplist[len(tmplist)-1][1]:
                        tmplist.append([stat.IPs.iplist[log[1]][1], str(log[4])])
                else:
                    tmplist.append([stat.IPs.iplist[log[1]][1], str(log[4])])
        for line in tmplist:
            print line[0] + ":" + str(line[1])

        exit(0)
    else:
        if not os.path.exists(args.log_file):
            raise Exception("Лог-файл не существует: %s" % args.log_file)

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
