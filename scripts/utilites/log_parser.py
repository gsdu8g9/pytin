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

from ddos_stat import DDoSStat
from api_sqlite import DDoSSQLite

class DDoSAnalizer:
    def __init__(self, filename, patterns, type_file):
        """
        Инициализация класса парсера
        """
        self.filename = filename
        self.patterns = patterns
        self.stat = DDoSStat()
        self.type_file = type_file
        self.quiet = False
        self.patterns = ["192\.168\.\d{1,3}\.\d{1,3}", "10\.\d{1,3}\.\d{1,3}\.\d{1,3}", "172\.(3[01]|2[0-9]|1[6-9])"]

    def isRFC(self, ip):
        """
        Проверка на совпадение с RFC
        """
        result = False
        if ip == "127.0.0.1":
            result = True
        for pattern in self.ippatterns:
            match = re.findall(pattern, ip)
            if match:
                result = True
        return result


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
       
        for Ch in line:
            if(Ch==' ') and (prevCh!='\\') and (not inQuote):
                if(len(words[len(words)-1])!=0):
                    words.append('')
            else:
                if(Ch=='"') and (prevCh!='\\') and (not inQuote):
                    if(len(words[len(words)-1])!=0):
                        words.append('')
                    words[len(words)-1] += Ch
                    inQuote = True
                elif(Ch=='"') and (prevCh!='\\') and (inQuote):
                    words[len(words)-1] += Ch
                    words.append('')
                    inQuote = False
                elif(Ch=='[') and (prevCh!='\\') and (not inQuote):
                    if(len(words[len(words)-1])!=0):
                        words.append('')
                    words[len(words)-1] += Ch
                    inQuote = True
                elif(Ch==']') and (prevCh!='\\') and (inQuote):
                    words[len(words)-1] += Ch
                    words.append('')
                    inQuote = False
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
        with open(self.filename, 'r') as f:
            i = 0
            for line in f:
                line = line.replace("\n", "")
                stamp = self.get_date(line)
                #		controltime = datetime.datetime.now()
                #		if get_time_diff(controltime, stamp) < datetime.timedelta(minutes=60):
                #			for pattern in patterns:
                #				result.append(get_log_value(line))
                #		for pattern in patterns:
                log_value = self.get_log_value(line)
                i += 1
                if not self.isRFC(log_value[0]):
#                    self.stat.addIP(log_value[0])
                    if self.type_file == 'nginx':
                        if log_value[7] != '"-"':
                            domain = self.get_domain(log_value[7])
                        else:
                            domain = "-"
                        self.stat.addLogLine(stamp, log_value[0], domain)
                    elif self.type_file == 'apache':
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
#            self.iplist.sort(key=lambda tup: tup[1])

def statistics(iplist):
    """
    Вывод статистики
    """
    print()
    print("Всего уникальных IP: " + str(len(iplist)))
    for ip in iplist:
        print("IP: " + ip[0] + " обратился " + str(ip[1]) + " раз")

def main():
    parser = argparse.ArgumentParser(description='DDoS log parser',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-o", "--outfile", dest="outfile", help="Файл для вывода")
    parser.add_argument("-l", "--log", dest="log_file", required=True,
        help="Лог-файл для анализа")
    parser.add_argument("-t", "--type", dest="type_file", choices=["apache", "nginx"],
        required=True, help="Тип парсера")
    parser.add_argument("-D", "--database", dest="database", help="Файл базы данных")

    args = parser.parse_args()

    # Проверка переданных параметров
    if not os.path.exists(args.log_file):
        raise Exception("Лог-файл не существует: %s" % args.log_file)
    if args.database:
        if os.path.exists(args.database):
            raise Exception("Файл БД существует: %s" % args.database)

#    tmp = DDoSSQLite(args.database)

    # Описание переменных
    # Паттерны парсера
    patterns = ''
    # Список исключённых IP
    excludeip = ''

    iplist = []
    hostlist = []

    """
    Паттерны для парсинга
    """
    if args.type_file == 'apache':
        patterns = ['^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)',  # IP remote
                    '^\-',  # -
                    '^(\S+|"\S*")',  # Remote user
                    '^\[\S*\s\S*\]',  # Dateime
                    '^\"\S+[^\"]*\"',  # , # Request
                    '^(\S+|"\S*")',  # Status
                    '^(\S+|"\S*")',  # Body bytes sent
                    '^(""|"(.*?)"|\S*\s\S*")', # '^(\d*|\S+|"\S*")',  # URL
                    '^(""|"(.*?)"|\(null\)|\S*\s\S*")', # '^\".[^\"]*\"',  # '"$http_user_agent"
                    '^".*"/U', # X-Forwarded-For
#                    '^(""|-|unknown|\(null\)|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)(,\s*(unknown|\(null\)|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*))*"',  # X-Forwarded-For
                    '^\"*\S*\"*']
#                    '^\(\S+|"\S*")']  # Domain
    elif args.type_file == 'nginx':
        patterns = ['^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)',  # IP remote
                    '^\-',  # -
                    '^(\S+|"\S*")',  # Remote user
                    '^\[\S*\s\S*\]',  # Dateime
                    '^\"\S+[^\"]*\"',  # Request
                    '^(\S+|"\S*")',  # Status
                    '^(\S+|"\S*")',  # Body bytes sent
                    '^\"\S*"',  # URL
                    '^\".[^\"]*\"',  # '"$http_user_agent"
                    '^\"(-|unknown|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)(, \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)*"']  # X-Forwarded-For

    ddos_analizer = DDoSAnalizer(args.log_file, patterns, args.type_file)
    ddos_analizer.start()
#    for ip in ddos_analizer.iplist:
#        tmp.addIP(ip[0])

    ddos_analizer.stat.statistics(args.outfile)

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
