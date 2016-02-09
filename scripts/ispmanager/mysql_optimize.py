#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# Скрипт оптимизации всех таблиц для сервера с ПУ ISPManager

__author__ = 'RemiZOffAlex'
__copyright__ = '(c) RemiZOffAlex'
__license__ = 'MIT'
__email__ = 'remizoffalex@mail.ru'

import re
import traceback
import subprocess

dict_re = {'username': 'username=(\S*)',
    'password': 'password=(\S*)'}

config = {}

cmd = '/usr/local/mgr5/sbin/mgrctl -m ispmgr db.server'
outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
for line in outinfo.stdout.readlines():
    line = line.replace("\n", "")
    result = re.findall(dict_re['username'], line)
    if len(result)>0:
        config['username'] = result[0]
    result = re.findall(dict_re['password'], line)
    if len(result)>0:
        config['password'] = result[0]

cmd = ''.join(['mysqlcheck --user=',
    config['username'],
    ' --password=',
    config['password'],
    ' --optimize --all-databases'])

try:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    print out
except:
    print 'Ошибка оптимизации'
    print cmd
