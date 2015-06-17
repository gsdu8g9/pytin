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
from api_sqlite import DDoSSQLite
from nginx_log_data_provider import NginxLogDataProvider

class DDoSAnalizer:
    def __init__(self, filename, type_file, limitrequests = 10):
        """
        Инициализация класса парсера
        """
        self.filename = filename
        self.stat = DDoSStat()
        self.type_file = type_file
        self.quiet = False

    def cli_progress_test(self, cur):
        """
        Прогресс бар
        """
        if not self.quiet:
            text = "\rОбработано " + str(cur) + " записей. В списке " + str(len(self.stat.IPs.iplist)) + " записей IP, "
            text += str(len(self.stat.Domains.domainlist)) + " записей доменов и " + str(len(self.stat.loglist)) + " в общей таблице"
            sys.stdout.write(text)
            sys.stdout.flush()

    def get_log_value(self, line):
        """
        Парсинг строки на элементы
        """
        result = []
        prevCh = ''
        words = ['']
        inQuote = False
        Quote = ''

        para = {'"': '"', '(': ')', '[': ']', "'": "'"}
        for Ch in line:
            if(Ch==' ') and (prevCh!='\\') and (not inQuote):
                if(len(words[len(words)-1])!=0):
                    words.append('')
            else:
                if (para.get(Ch)) and (prevCh!='\\') and (not inQuote):
                    if(len(words[len(words)-1])!=0):
                        words.append('')
                    words[len(words)-1] += Ch
                    Quote = Ch
                    inQuote = True
                elif inQuote:
                    if (Ch==para[Quote]) and (prevCh!='\\'):
                        words[len(words)-1] += Ch
                        words.append('')
                        inQuote = False
                        Quote = ''
                    else:
                        words[len(words)-1] += Ch
                else:
                    words[len(words)-1] += Ch
            prevCh = Ch

        if(len(words[-1:][0])==0):
            words.pop()
        result = words
        return result

    def get_date(self, line):
        """
        Получить штамп времени записи из лога
        """
        result = False
        match = re.findall('(\d+)\/([A-Za-z]+)\/(\d+)\:(\d+)\:(\d+)\:(\d+)', line)
        if match:
            result = datetime.datetime.strptime(
                str(match[0][2]) + " " + match[0][1] + " " + str(match[0][0]) + " " + str(match[0][3]) + " " + str(
                    match[0][4]), '%Y %b %d %H %M')
        return result

    def get_time_diff(time1, time2):
        """
        Получить разницу во времени
        """
        result = time1 - time2
        return result

    def get_domain(self, url):
        """
        Получить имя домена из url
        """
        result = ''
        match = re.findall('^"(http:\/\/|https:\/\/)', url)
        if match:
            url = url[len(match[0]):].strip()
        match = re.findall('([^\/?#]+)(?:[\/?#]|$)', url)
        if match:
            result = match[0]
        return result

    def start(self):
        """
        Обработка записей
        """
#        with open(self.filename, 'r') as f:
        f = None
        if self.type_file == 'nginx':
            f = NginxLogDataProvider(self.filename)
        elif self.type_file == 'apache':
            print 'apache'
        i = 0
        for line in f:
            stamp = line['date']
            i += 1
            if not self.stat.IPs.isRFC(line['ip']):
                if line['domain'] != '"-"':
                    domain = self.get_domain(line['domain'])
                else:
                    domain = "-"
                self.stat.addLogLine(stamp, line['ip'], domain)
                if self.type_file == 'apache':
                    if len(log_value)<11:
                        print "Ошибка при разборе строки"
                        print line
                        print ''
                    else:
                        if log_value[10] != '"-"':
                            domain = self.get_domain(log_value[10])
                        else:
                            domain = "-"
                        self.stat.addLogLine(stamp, log_value[0], domain)
#                    result.append(log_value[0])
            if not stamp:
                sys.exit(0)
#                if self.quiet:
            if i%1000 == 0:
                self.cli_progress_test(i)

def main():
    parser = argparse.ArgumentParser(description='DDoS log parser',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-o", "--outfile", dest="outfile", help="Файл для вывода")
    parser.add_argument("-B", "--block", dest="blockpath", help="Путь для блокировки")
    parser.add_argument("-l", "--log", dest="log_file", required=True,
        help="Лог-файл для анализа")
    parser.add_argument("-t", "--type", dest="type_file", choices=["apache", "nginx"],
        required=True, help="Тип парсера")
    parser.add_argument("-D", "--database", dest="database", help="Файл базы данных")
    parser.add_argument("--limit", dest="limitrequests", type=int, default=10,
        help="Лимит запросов с одного IP к одному домену")
    parser.add_argument("-S", "--statistics", dest="statistics", action='store_true',
        help="Вывести статистику")

    args = parser.parse_args()

    # Проверка переданных параметров
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

    # Инициализация анализатора и его запуск
    ddos_analizer = DDoSAnalizer(args.log_file, args.type_file)
    ddos_analizer.start()

    # Получить данные
    stat = ddos_analizer.stat

    # Вывод статистики
    if args.statistics:
        stat.statistics(args.outfile, int(args.limitrequests))

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

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
