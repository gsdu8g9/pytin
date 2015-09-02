#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
#   Информация о zpool
#
# Requirements:
#   zpool
#
# wget --no-check-certificate -P /etc/zabbix https://raw.githubusercontent.com/servancho/pytin/master/scripts/zabbix/zbx_zpool.py
#
# File: /etc/sudoers.d/zpoolconf
#   Cmnd_Alias ZPOOL_GETCONFIG = /sbin/zpool status, /sbin/zpool list
#   zabbix ALL=(root) NOPASSWD: ZPOOL_GETCONFIG
#
# zabbix_agentd.conf:
#   Timeout=15

import argparse
import os
import re
import subprocess
import sys
import traceback
import json

dict_re = {'discovery': '^Logical device number ([0-9]+).*$',
    'pdevicesn': '^\s*Serial number\s*:\s*(.*)$'}

cmd_zpool = ''

"""
Решение проблемы с нахождением утилиты
"""
if len(cmd_zpool) == 0:
    o = open('output','a') #open for append
    outinfo = subprocess.Popen(['whereis', 'zpool'], stdout=subprocess.PIPE)
    var1 = outinfo.stdout.readlines()[0].replace("\n", "").split(' ')
    for line in open('/etc/zabbix/zbx_zpool.py'):
       line = line.replace("cmd_zpool = ''", "cmd_zpool = '" + var1[1] + "'")
       o.write(line)
    o.close()
    os.rename('/etc/zabbix/output', '/etc/zabbix/zbx_zpool.py')
    os.chmod('/etc/zabbix/zbx_zpool.py', 0550)

def main():
    parser = argparse.ArgumentParser(description='RAIDZ parser',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--test", dest="test", action='store_true', help="Тестовый режим из файла")
    group1 = parser.add_argument_group('Команды')
    mutex_group1 = group1.add_mutually_exclusive_group(required=True)
    mutex_group1.add_argument("--discovery", dest="discovery", action='store_true', help="Обнаружение")
    mutex_group1.add_argument("--pool", dest="pool", help="Имя пула")
    mutex_group1.add_argument("--status", dest="status", help="Состояние пула")

    args = parser.parse_args()

    outinfo = None
    """
    Обнаружение пулов и дисков
    """
    if args.discovery:
        outinfo = subprocess.Popen(['sudo', cmd_zpool, 'list', '-H'], stdout=subprocess.PIPE)
        pools = []
        """
        Получить список пулов
        """
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            pool = line.split('\s')
            pools.append(pool)
        """
        Получить список дисков на каждом пуле
        """
        for pool in pools:
            pass
        """
        Сформировать пакет данных
        """
        str_jdump = '{"data": ['
        for id_pool,pool in enumerate(pools):
            str_jdump += '{"{#POOLNAME}": "' + pool[0] + '"}'
#                str_jdump += '"{#POOLDEVICE}": "' + device + '"}'
            if id_pool + 1 < len(pools):
                str_jdump += ','
        str_jdump += ']}'
        jdump = json.loads(str_jdump)
        gf = json.dumps(jdump, indent=4)
        print gf
        sys.exit(0)

    if args.test:
        outinfo = subprocess.Popen(['cat', 'test/output_zpool.txt'], stdout=subprocess.PIPE)
    else:
        outinfo = subprocess.Popen(['sudo', cmd_zpool, 'list', '-H'], stdout=subprocess.PIPE)

    lstatus = None
    result = None
    if args.status:
        outinfo = subprocess.Popen(['sudo', cmd_zpool, 'list', '-H', str(args.status)], stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            pool = line.split()
            lstatus = pool[6]
            if len(lstatus) > 0:
                if lstatus == 'ONLINE':
                    result = '1'
                elif lstatus == 'DEGRADED':
                    result = '2'
                elif lstatus == 'FAULTED':
                    result = '3'
                elif lstatus == 'OFFLINE':
                    result = '4'
                elif lstatus == 'UNAVAIL':
                    result = '5'
                elif lstatus == 'REMOVED':
                    result = '6'
                else:
                    result = '0'

    if result:
        if len(result) > 0:
            print str(result[0])
        else:
            print str(result)

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
