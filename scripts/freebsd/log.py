#!/usr/bin/env python3.4
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
# Скрипт парсинга логов на предмет брутфорса: SSH, Nginx, Exim
#
# Requirements:
# FreeBSD: python3.4

import re
# import pygeoip

# GeoIP
# geoip = pygeoip.GeoIP('/usr/local/share/GeoIP/GeoIP.dat')

# pattern = '\d{,4}\-\d{,2}\-\d{,2}\s\d{,2}\:\d{,2}\:\d{,2}\slogin authenticator failed for\s'
patterns = ['login authenticator failed for']
ippattern = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

listip = []
# Белый список
whiteip = []
blackip = []

def isRFC(ip):
    """
    Проверка на совпадение с RFC
    """
    result = False
    if ip == "127.0.0.1":
        result = True
    patterns = ["192\.168\.\d{1,3}\.\d{1,3}", "10\.\d{1,3}\.\d{1,3}\.\d{1,3}"]
    for pattern in patterns:
        match = re.search(pattern, ip)
        if match:
            result = True
    return result


def downloadList(fileName):
    """
    Загрузить список
    """
    result = []
    with open(fileName, 'r') as f:
        for line in f:
            line = line.replace("\n", "")
            result.append(line)
    return result


def inList(ip, list):
    """
    Проверить есть ли IP в белом списке
    """
    result = True
    if ip not in list:
        result = False
    return result


def getListIP(fileName, patterns):
    result = []
    f = open(fileName, 'r')
    for line in f:
        line = line.replace("\n", "")
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                match = re.search(ippattern, line)
                if match:
                    item = match.group()
                    if item not in result:
                        if not isRFC(item):
                            if not inList(item, whiteip):
                                if not inList(item, blackip):
                                    result.append(item)
    f.close()
    return result


def isAlredyInFile(ip, fileName):
    """
    Проверить есть ли указанный IP в списке файла
    """
    result = False
    f = open(fileName, 'r')
    for line in f:
        line = line.replace("\n", "")
        if ip in line:
            result = True
            break
    f.close()
    return result

# Загрузить белый список
whiteip = downloadList('/etc/whitelist.list')
# Загрузить чёрный список
blackip = downloadList('/etc/badguys.list')

# Страна


# Exim
# patterns = ['login authenticator failed for']
# listip = getListIP('/var/log/exim/mainlog', patterns)

# SSH
# print('# SSH')
patterns = ['error\: PAM\: authentication error for \w* from', 'Invalid user \w* from', 'Received disconnect from']
listip = listip + getListIP('/var/log/auth.log', patterns)

# Nginx
# patterns = ['/"GET //administrator//index.php/?']
# patterns = ['"GET /administrator(\/|\w|\s)"']
# patterns = ['"GET\s(.+)admin(.+)\s\w+/.+"\s401']
# listip = listip + getListIP('/var/log/nginx/access-example.org.log', patterns)

for line in listip:
    print(line)
#    print(geoip.country_code_by_addr(line))


class statIP:
    def __init__(self):
        ip = ''
        count = 0

