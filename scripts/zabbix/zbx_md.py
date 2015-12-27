#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
#   Информация от Adaptec
#
# Requirements:
#   Adaptec

import argparse
import os
import re
import subprocess
import sys
import traceback
import json

dict_re = {'discovery': '^(md[0-9])\s\:\sactive\s(raid[0-9])\s(.*)$',
    'device': '^(sd.[0-9]).*$',
    'state': '^\s*State\ \:\s(\S*)\s*$'}

cmd_mdadm = '/sbin/mdadm'

"""
Решение проблемы с нахождением утилиты
"""
if len(cmd_mdadm) == 0:
    o = open('output','a') #open for append
    outinfo = subprocess.Popen(['whereis', 'mdadm'], stdout=subprocess.PIPE)
    var1 = outinfo.stdout.readlines()[0].replace("\n", "").split(' ')
    for line in open('/etc/zabbix/zbx_md.py'):
       line = line.replace("cmd_mdadm = '/sbin/mdadm'", "cmd_mdadm = '" + var1[1] + "'")
       o.write(line)
    o.close()
    os.rename('/etc/zabbix/output', '/etc/zabbix/zbx_md.py')
    os.chmod('/etc/zabbix/zbx_md.py', 0550)

def main():
    parser = argparse.ArgumentParser(description='MD RAID',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--test", dest="test", action='store_true', help="Тестовый режим из файла")
    group1 = parser.add_argument_group('Команды')
    mutex_group1 = group1.add_mutually_exclusive_group(required=True)
    mutex_group1.add_argument("--discovery", dest="discovery", action='store_true', help="Обнаружение")
    mutex_group1.add_argument("--state", dest="state", help="Состояние устройства")
    mutex_group1.add_argument("--level", dest="level", type=int, help="Уровень RAID")

    args = parser.parse_args()

    outinfo = None
    """
    Обнаружение контроллеров и дисков
    """
    if args.discovery:
        outinfo = subprocess.Popen(['sudo', 'cat', '/proc/mdstat'], stdout=subprocess.PIPE)
        controllers = []
        """
        Получить список контроллеров
        """
        controllers = []
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            result = re.findall(dict_re['discovery'], line)
            if len(result)>0:
                for item in result[0][2].split(" "):
                    device = re.findall(dict_re['device'], item)
                    controllers.append(['/dev/' + result[0][0], '/dev/' + device[0]])
        """
        Сформировать пакет данных
        """
        devices = []
        for id,controller in enumerate(controllers):
            devices.append({"{#MD_RAID}": controller[0],
                "{#MD_DEVICE}": controller[1]})
        jdump = json.loads(str_jdump)
        result = json.dumps({"data": devices})
        print result
        sys.exit(0)

    if args.test:
        outinfo = subprocess.Popen(['cat', 'test/output.txt'], stdout=subprocess.PIPE)
    else:
        pass
#        outinfo = subprocess.Popen(['sudo', cmd_mdadm, '--detail'], stdout=subprocess.PIPE)

    lstatus = None
    result = None
    if args.state:
        outinfo = subprocess.Popen(['sudo', cmd_mdadm, '--detail', str(args.state)], stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['state'], line)
            if len(lstatus) > 0:
                if lstatus[0] == 'clear':
                    result = '1'
                elif lstatus[0] == 'inactive':
                    result = '2'
                elif lstatus[0] == 'suspended':
                    result = '3'
                elif lstatus[0] == 'readonly':
                    result = '4'
                elif lstatus[0] == 'read-auto':
                    result = '5'
                elif lstatus[0] == 'clean':
                    result = '6'
                elif lstatus[0] == 'active':
                    result = '7'
                elif lstatus[0] == 'write-pending':
                    result = '8'
                elif lstatus[0] == 'active-idle':
                    result = '9'
    elif args.level:
        outinfo = subprocess.Popen(['sudo', cmd_mdadm, '--detail', str(args.level)], stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['level'], line)
            if len(lstatus)>0:
                result = lstatus

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
