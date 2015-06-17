#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import re
import datetime

class ApacheLogDataProvider():
    def __init__(self, logfile):
        """
        Инициализация класса доступа к лог-файлу nginx
        """
        self.logfile = logfile
        self.fdesc = open(self.logfile, 'r')
        self.iterator = iter(self.fdesc)

    def __iter__(self):
        """
        Инициализация итератора
        """
        return self

    def next(self):
        """
        Выборка элемента
        """
        result = {'domain': '', 'ip': '', 'date': None}
        line = self.iterator.next()
        line = line.replace("\n", "")
        values = self.get_log_value(line)
        result['domain'] = values[10]
        result['ip'] = values[0]
        match = re.findall('(\d+)\/([A-Za-z]+)\/(\d+)\:(\d+)\:(\d+)\:(\d+)', values[3])
        if match:
            result['date'] = datetime.datetime.strptime(
                str(match[0][2]) + " " + match[0][1] + " " + str(match[0][0]) + " " + str(match[0][3]) + " " + str(
                    match[0][4]), '%Y %b %d %H %M')
        #result = line
        return result

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
