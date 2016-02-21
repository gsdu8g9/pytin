#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# Скрипт оптимизации всех таблиц для сервера с ПУ DirectAdmin

__author__ = 'RemiZOffAlex'
__copyright__ = '(c) RemiZOffAlex'
__license__ = 'MIT'
__email__ = 'remizoffalex@mail.ru'

import re
import traceback
import subprocess

dict_re = {'user': 'user=(\S*)',
    'password': 'password=(\S*)'}

config = {}

for line in open('/usr/local/directadmin/conf/my.cnf'):
    line = line.replace("\n", "")
    result = re.findall(dict_re['user'], line)
    if len(result)>0:
        config['user'] = result[0]
    result = re.findall(dict_re['password'], line)
    if len(result)>0:
        config['password'] = result[0]

cmd = ''.join(['mysqlcheck --user=',
    config['user'],
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
