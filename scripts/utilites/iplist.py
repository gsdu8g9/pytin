#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
# Класс-коллекция IP адресов
#
# Requirements:
# Python

import re

class IPList:
    def __init__(self):
        self.iplist = []
        # Index - позиция индекса IP в элементе
        self.Index = 1

    def Add(self, IP):
        """
        Добавить IP в БД
        """
        result = self.Search(IP)
        if not result:
            self.Insert(IP)
            result = self.Search(IP)
        else:
            result[2] = result[2] + 1
        return result

    def Insert(self, IP):
        """
        Вставка в отсортированный массив
        """
        # Index - позиция индекса IP в элементе
        Index = 1
        Element = [len(self.iplist), IP, 1]
        min, max = 0, len(self.iplist)
        while max - min > 0:
            m = (min + max) // 2 # Делим отрезок пополам
            if self.iplist[m][Index] > Element[Index]:
                max = m
            else:
                min = m + 1
        result = self.iplist[:max] + [Element] + self.iplist[max:]
        self.iplist = result

    def Search(self, IP):
        """
        Бинарный поиск
        """
        i = 0
        j = len(self.iplist)-1
        Element = [None, IP, None]
        if j == -1:
            return None
        while i < j:
            m = int((i+j)/2)
            if Element[self.Index] > self.iplist[m][self.Index]:
                i = m+1
            else:
                j = m
        #тут не важно j или i
        if self.iplist[j][self.Index] == Element[self.Index]:
            return self.iplist[j]
        else:
            return None

    def isRFC(self, IP):
        """
        Проверка на совпадение с RFC
        """
        ippatterns = ["127\.\d{1,3}\.\d{1,3}\.\d{1,3}", "192\.168\.\d{1,3}\.\d{1,3}", "10\.\d{1,3}\.\d{1,3}\.\d{1,3}", "172\.(3[01]|2[0-9]|1[6-9])"]
        result = False
        for pattern in ippatterns:
            match = re.findall(pattern, IP)
            if match:
                result = True
        return result

    def isIPv6(self, IP):
        """
        Проверка на принадлежность к IPv6
        """
        ippatterns = ["127\.\d{1,3}\.\d{1,3}\.\d{1,3}", "192\.168\.\d{1,3}\.\d{1,3}", "10\.\d{1,3}\.\d{1,3}\.\d{1,3}", "172\.(3[01]|2[0-9]|1[6-9])"]
        result = False
        for pattern in ippatterns:
            match = re.findall(pattern, IP)
            if match:
                result = True
        return result
