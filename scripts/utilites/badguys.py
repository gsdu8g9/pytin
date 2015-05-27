#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
#	Скрипт загрузки таблицы чёрного списка заблокированных IP
#
# Requirements:
#	FreeBSD/Linux

import subprocess
import argparse
import traceback
import sys
import os
import datetime
import pygeoip

class IPList:
    def __init__(self):
        self.iplist = []

    def Add(self, IP):
        """
        Добавить IP в БД
        """
        result = self.Search(IP)
        if not result:
            self.Insert(IP)
            result = self.Search(IP)
        return result

    def Insert(self, IP):
        """
        Вставка в отсортированный массив
        """
        min, max = 0, len(self.iplist)
        while max - min > 0:
            m = (min + max) // 2 # Делим отрезок пополам
            if self.iplist[m] > IP:
                max = m
            else:
                min = m + 1
        result = self.iplist[:max] + [IP] + self.iplist[max:]
        self.iplist = result

    def Delete(self, IP):
        """
        Удаление из массива
        """
        item = self.Search(IP)
        if item:
            self.iplist.remove(item)

    def Search(self, IP):
        """
        Бинарный поиск
        """
        i = 0
        j = len(self.iplist)-1
        if j == -1:
            return None
        while i < j:
            m = int((i+j)/2)
            if IP > self.iplist[m]:
                i = m+1
            else:
                j = m
        #тут не важно j или i
        if self.iplist[j] == IP:
            return self.iplist[j]
        else:
            return None

class FW():
    def __init__(self, args):
        """
        Инициализация класса парсера
        """
        self.args = args
        self.iplist = IPList()
        if self.args.verbose:
            t1 = datetime.now()
        if os.path.exists(self.args.filename):
            with open(self.args.filename, 'r') as f:
                for ip in f:
                    ip = ip.replace("\n", "")
                    self.iplist.Add(ip)
        if self.args.verbose:
            print 'Время чтения файла: ' + str(datetime.now() - t1).seconds + ' секунд'

    def save(self):
        if self.args.verbose:
            t1 = datetime.now()
        with open(self.args.filename, 'w+') as f:
            for ip in self.iplist.iplist:
                f.write(ip + "\n")
        if self.args.verbose:
            print 'Время записи в файл: ' + str(datetime.now() - t1).seconds + ' секунд'
        
    def add(self):
        for ip in self.args.addip:
            self.iplist.Add(ip)
        self.refresh()

    def delete(self):
        for ip in self.args.delip:
            self.iplist.Delete(ip)
        self.refresh()

    def infoip(self):
        """
        Получить информацию об IP
        """
        for ip in self.args.infoip:
            gi = pygeoip.GeoIP('/usr/local/share/GeoIP/GeoIP.dat')
            print "Страна: " + gi.country_name_by_addr(ip)
            result = self.iplist.Search(ip)
            if not result:
                print "IP " + ip + " в чёрном списке не найден"
            else:
                print "IP " + ip + " в чёрном списке"

    def flush(self):
        fw_cmd('flush')

    def refresh(self):
        if not self.args.quiet:
            print "Очистка таблицы межсетевого экрана"
        self.fw_cmd('flush')

        if not self.args.quiet:
            print "Загрузка списка IP в таблицу межсетевого экрана"
        if self.args.verbose:
            t1 = datetime.datetime.now()
        for ip in self.iplist.iplist:
            self.fw_cmd('add', ip)
        if self.args.verbose:
            print "Время выполнения: " + str((datetime.datetime.now() - t1).seconds) + " секунд"

    # Показ списка IP адресов
    def showlist(self):
        if self.args.listshow == 'file':
            for ip in self.iplist.iplist:
                print ip
        elif self.args.listshow == 'firewall':
            self.fw_cmd(operation = 'list')

    def fw_cmd(self, operation, IP = None):
        if self.args.firewall == 'ipfw':
            if operation == 'flush':
                cmd = "/sbin/ipfw table " + str(self.args.table) + " flush"
                if self.args.verbose:
                    print cmd
                subprocess.call(cmd, shell=True)
            elif operation == 'add':
                cmd = "/sbin/ipfw table " + str(self.args.table) + " add " + IP
                if self.args.verbose:
                    print cmd
                subprocess.call(cmd, shell=True)
            elif operation == 'del':
                cmd = "/sbin/ipfw table " + str(self.args.table) + " del " + IP
                if self.args.verbose:
                    print cmd
                subprocess.call(cmd, shell=True)
            elif operation == 'list':
                cmd = "/sbin/ipfw table " + str(self.args.table) + " list"
                if self.args.verbose:
                    print cmd
                subprocess.call(cmd, shell=True)
        elif self.args.firewall == 'iptables':
            cmd = 'Правила для iptables'
            if self.args.verbose:
                print cmd
        elif self.args.firewall == 'pf':
            cmd = 'Правила для pf'
            if self.args.verbose:
                print cmd

def main():
    parser = argparse.ArgumentParser(description='Скрипт добавления IP или подсети в блокировку на межсетевом экране',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser._optionals.title = "Необязательные аргументы"

    parser.add_argument("-q", "--quiet", dest="quiet", action='store_true', help="Тихий режим")
    parser.add_argument("-f", "--filename", dest="filename", default="/etc/badguys.list", help="Имя файла")
    parser.add_argument("-t", "--table", dest="table", default=2, help="Номер таблицы")
    parser.add_argument("-v", "--verbose", dest="verbose", action='store_true', help="Отладка")
    parser.add_argument("-fw", "--firewall", dest="firewall", default='ipfw', choices=['ipfw', 'iptables', 'pf'], help="Тип межсетевого экрана")
    group1 = parser.add_argument_group('Команды')
    mutex_group1 = group1.add_mutually_exclusive_group()
    mutex_group1.add_argument("-a", "--add", nargs='+', dest="addip", help="Добавить IP")
    mutex_group1.add_argument("-d", "--delete", nargs='+', dest="delip", help="Удалить IP")
    mutex_group1.add_argument("-c", "--clear", action='store_true', dest="fwclear", help="Очистить правила")
    mutex_group1.add_argument("-i", "--info", nargs='+', dest="infoip", help="Получить информацию об IP")
    mutex_group1.add_argument("-l", "--list", default='none', dest="listshow", choices=['none', 'firewall', 'file'], help="Показать список IP")
    mutex_group1.add_argument("-r", "--reload", action='store_true', dest="refresh", help="Перезагрузить правила")

    args = parser.parse_args()

    fw = FW(args)

    if args.addip:
        fw.add()
    elif args.fwclear:
        fw.flush()
    elif args.delip:
        fw.delete()
    if args.infoip:
        fw.infoip()
    elif args.listshow:
        fw.showlist()
    elif args.refresh:
        fw.refresh()

    fw.save()

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
