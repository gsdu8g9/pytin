#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
# Вывод статистики

from iplist import IPList


class DomainList:
    def __init__(self):
        self.domainlist = []
        # Index - позиция индекса IP в элементе
        self.Index = 1

    def Add(self, Domain):
        """
        Добавить Domain в БД
        """
        result = self.Search(Domain)
        if not result:
            self.Insert(Domain)
            result = self.Search(Domain)
        else:
            result[2] = result[2] + 1
        return result

    def Insert(self, Domain):
        """
        Вставка в отсортированный массив
        """
        min, max = 0, len(self.domainlist)
        Element = [len(self.domainlist), Domain, 1]
        while max - min > 0:
            m = (min + max) // 2  # Делим отрезок пополам
            if self.domainlist[m][self.Index] > Element[self.Index]:
                max = m
            else:
                min = m + 1
        result = self.domainlist[:max] + [Element] + self.domainlist[max:]
        self.domainlist = result

    def Search(self, Domain):
        """
        Бинарный поиск
        """
        i = 0
        j = len(self.domainlist) - 1
        Element = [None, Domain, None]
        if j == -1:
            return None
        while i < j:
            m = int((i + j) / 2)
            if Element[self.Index] > self.domainlist[m][self.Index]:
                i = m + 1
            else:
                j = m
        # тут не важно j или i
        if self.domainlist[j][self.Index] == Element[self.Index]:
            return self.domainlist[j]
        else:
            return None


class DDoSStat:
    def __init__(self):
        """
        Инициализация класса парсера
        """
        self.IPs = IPList()
        self.Domains = DomainList()
        self.loglist = []

    def Search(self, id_ip, id_domain, period):
        """
        Бинарный поиск
        """
        i = 0
        j = len(self.loglist) - 1
        Element = [None, id_ip, id_domain, period, None]
        if j == -1:
            return None
        while i < j:
            m = int((i + j) / 2)
            if Element[1] > self.loglist[m][1]:
                i = m + 1
            elif Element[1] == self.loglist[m][1] and Element[2] > self.loglist[m][2]:
                i = m + 1
            elif Element[1] == self.loglist[m][1] and Element[2] == self.loglist[m][2] and Element[3] > self.loglist[m][
                3]:
                i = m + 1
            else:
                j = m
        # тут не важно j или i
        if self.loglist[j][1] == Element[1] and self.loglist[j][2] == Element[2] and self.loglist[j][3] == Element[3]:
            return self.loglist[j]
        else:
            return None

    def Insert(self, id_ip, id_domain, period):
        """
        Вставка в отсортированный массив
        """
        min, max = 0, len(self.loglist)
        Element = [len(self.loglist), id_ip, id_domain, period, 1]
        while max - min > 0:
            m = (min + max) // 2  # Делим отрезок пополам
            if self.loglist[m][1] > Element[1]:
                max = m
            elif self.loglist[m][1] == Element[1] and self.loglist[m][2] > Element[2]:
                max = m
            elif self.loglist[m][1] == Element[1] and self.loglist[m][2] == Element[2] and self.loglist[m][3] > Element[
                3]:
                max = m
            else:
                min = m + 1
        result = self.loglist[:max] + [Element] + self.loglist[max:]
        self.loglist = result

    def addLogLine(self, logdate, IP, Domain):
        """
        Добавить строку лога
        """
        ip = self.IPs.Add(IP)
        domain = self.Domains.Add(Domain)
        period = str(logdate.year) + " " + str(logdate.month) + " " + str(logdate.day) + " " + str(
            logdate.hour) + " " + str(logdate.minute - logdate.minute % 30)
        result = self.Search(ip[0], domain[0], period)
        if not result:
            self.Insert(ip[0], domain[0], period)
            result = self.Search(ip[0], domain[0], period)
        else:
            result[4] = result[4] + 1

    def statistics(self, filename=None, limitrequests=0):
        """
        Вывод статистики
        
        filename - Файл для вывода статистики
        limitrequests - Лимит запросов
        """
        if filename:
            outfile = open(filename, "w")
            outfile.write('\n')
            outfile.write("Всего уникальных IP: " + str(len(self.IPs.iplist)) + '\n')
            for ip in self.IPs.iplist:
                outfile.write("IP: " + ip[1] + " обратился " + str(ip[2]) + " раз" + '\n')
            outfile.write('\n')
            outfile.write("Всего уникальных доменов: " + str(len(self.Domains.domainlist)) + '\n')
            for domain in self.Domains.domainlist:
                outfile.write("К домену: " + domain[1] + " обратились " + str(domain[2]) + " раз" + '\n')
            outfile.write('\n')
            for log in self.loglist:
                if limitrequests > 0:
                    if log[4] > limitrequests:
                        outfile.write(
                            "В период " + log[3] + " к домену " + self.Domains.domainlist[log[2]][1] + " с IP " +
                            self.IPs.iplist[log[1]][1] + " обратились " + str(log[4]) + " раз" + '\n')
                else:
                    outfile.write("В период " + log[3] + " к домену " + self.Domains.domainlist[log[2]][1] + " с IP " +
                                  self.IPs.iplist[log[1]][1] + " обратились " + str(log[4]) + " раз" + '\n')
            outfile.close()
        else:
            print
            print("Всего уникальных IP: " + str(len(self.IPs.iplist)))
            for ip in self.IPs.iplist:
                if limitrequests > 0:
                    if ip[2] > limitrequests:
                        print("IP: " + ip[1] + " обратился " + str(ip[2]) + " раз")
                else:
                    print("IP: " + ip[1] + " обратился " + str(ip[2]) + " раз")
            print
            print("Всего уникальных доменов: " + str(len(self.Domains.domainlist)))
            for domain in self.Domains.domainlist:
                if limitrequests > 0:
                    if domain[2] > limitrequests:
                        print("К домену: " + domain[1] + " обратились " + str(domain[2]) + " раз")
                else:
                    print("К домену: " + domain[1] + " обратились " + str(domain[2]) + " раз")
            print
            for log in self.loglist:
                if limitrequests > 0:
                    if log[4] > limitrequests:
                        print("В период " + log[3] + " к домену " + self.Domains.domainlist[log[2]][1] + " с IP " +
                              self.IPs.iplist[log[1]][1] + " обратились " + str(log[4]) + " раз")
                else:
                    print("В период " + log[3] + " к домену " + self.Domains.domainlist[log[2]][1] + " с IP " +
                          self.IPs.iplist[log[1]][1] + " обратились " + str(log[4]) + " раз")
