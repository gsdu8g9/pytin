#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
# Класс анализатора
#
# Requirements:
# Python 2

import datetime
import re
import sys

from ddos_stat import DDoSStat


class DDoSAnalizer:
    """
    Класс анализатора событий
    """

    def __init__(self, dataprovider, limitrequests=10, silent=True):
        """
        Инициализация класса анализатора событий
        """
        self.stat = DDoSStat()
        self.silent = silent
        self.dataprovider = dataprovider

    def cli_progress_test(self, cur):
        """
        Прогресс бар
        """
        if not self.silent:
            text = "\rОбработано " + str(cur) + " записей. В списке " + str(len(self.stat.IPs.iplist)) + " записей IP, "
            text += str(len(self.stat.Domains.domainlist)) + " записей доменов и " + str(
                len(self.stat.loglist)) + " в общей таблице"
            sys.stdout.write(text)
            sys.stdout.flush()

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
        i = 0
        for line in self.dataprovider:
            stamp = line['date']
            i += 1
            if not self.stat.IPs.isRFC(line['ip']):
                if line['domain'] != '"-"':
                    domain = self.get_domain(line['domain'])
                else:
                    domain = "-"
                self.stat.addLogLine(stamp, line['ip'], domain)
            if not stamp:
                sys.exit(0)
            #                if self.quiet:
            if i % 1000 == 0:
                self.cli_progress_test(i)
