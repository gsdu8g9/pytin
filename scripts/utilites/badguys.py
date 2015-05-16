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

    def add(self):
        if os.path.exists(self.args.filename):
            with open(self.args.filename, 'r') as f:
                for ip in f:
                    ip = ip.replace("\n", "")
                    self.iplist.Add(ip)
        for ip in self.args.addip:
            self.iplist.Add(ip)
        with open(self.args.filename, 'w+') as f:
            for ip in self.iplist.iplist:
                f.write(ip + "\n")
        self.reload()

    def delete(self):
        if os.path.exists(self.args.filename):
            with open(self.args.filename, 'r') as f:
                for ip in f:
                    ip = ip.replace("\n", "")
                    self.iplist.Add(ip)
        for ip in self.args.delip:
            self.iplist.Delete(ip)
        with open(self.args.filename, 'w+') as f:
            for ip in self.iplist.iplist:
                f.write(ip + "\n")
        self.reload()

    def flush(self):
        fw_cmd()

    def reload(self):
        if not self.args.quiet:
            print "Очистка таблицы межсетевого экрана"
#        subprocess.call("ipfw table " + str(self.args.table) + " flush")
        self.fw_cmd(fwclear = True)

        if not self.args.quiet:
            print "Загрузка списка IP в таблицу межсетевого экрана"
        if os.path.exists(self.args.filename):
            with open(self.args.filename, 'r') as f:
                for ip in f:
                    ip = ip.replace("\n", "")
#                    subprocess.call("ipfw table " + str(self.args.table) + " add " + line)
                    if self.args.verbose:
                        self.fw_cmd(ip)

    # Показ списка IP адресов
    def showlist(self):
        with open(args.filename, 'r') as f:
            for ip in f:
                fw_cmd()

    def fw_cmd(self, IP = None, fwclear = False):
        if self.args.firewall == 'ipfw':
            if self.args.fwclear or fwclear:
                cmd = "ipfw table " + str(self.args.table) + " flush"
                if self.args.verbose:
                    print cmd
            elif self.args.addip:
                cmd = "ipfw table " + str(self.args.table) + " add " + IP
                if self.args.verbose:
                    print cmd
            elif self.args.delip:
                cmd = "ipfw table " + str(self.args.table) + " del " + IP
                if self.args.verbose:
                    print cmd
            elif self.args.listshow:
                cmd = "ipfw table " + str(self.args.table) + " list"
                if self.args.verbose:
                    print cmd
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
    mutex_group1.add_argument("-l", "--list", action='store_true', dest="listshow", help="Показать список IP")
    mutex_group1.add_argument("-r", "--reload", action='store_true', dest="reload", help="Перезагрузить правила")

    args = parser.parse_args()

    fw = FW(args)

    if args.addip:
        fw.add()
    elif args.fwclear:
        fw.flush()
    elif args.delip:
        fw.delete()
    elif args.listshow:
        fw.showlist()
    elif args.reload:
        fw.reload()

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
