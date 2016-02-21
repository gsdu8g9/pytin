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

def read_json(filename):
    """
    Считываем данные в формате JSON из файла filename
    """
    result = None
    with open(filename) as json_data:
        result = json.load(json_data)
        json_data.close()
    return result

def write_json(filename, jsondata):
    with open(filename, 'w') as f:
        json.dump(jsondata, f)

dict_re = {'discovery': '^(md[0-9])\s\:\sactive\s(raid[0-9])\s(.*)$',
    'device': '^(sd.[0-9]).*$',
    'state': '^\s*State\ \:\s(\S*)\s*$',
    'level': '^\s*Raid Level\s:\s(\S*)$',
    'rebuild': '^\s*Rebuild Status\s:\s(\d*)\%\s\S*$',
    'sizearray': '^\s*Array Size\s:\s(\d*).*$',
    'devicesRaid': '^\s*Raid Devices\s:\s(\d*)$',
    'devicesTotal': '^\s*Total Devices\s:\s(\d*)$',
    'devicesActive': '^\s*Active Devices\s:\s(\d*)$',
    'devicesWorking': '^\s*Working Devices\s:\s(\d*)$',
    'devicesFailed': '^\s*Failed Devices\s:\s(\d*)$',
    'devicesSpare': '^\s*Spare Devices\s:\s(\d*)$'}

configfile = os.path.dirname(os.path.abspath(__file__)) + '/zbx_config.json'
config = {}
if os.path.isfile(configfile):
    config = read_json(configfile)

"""
Решение проблемы с нахождением утилиты
"""
if not 'mdadm' in config:
    outinfo = subprocess.Popen(['which', 'mdadm'], stdout=subprocess.PIPE)
    var1 = outinfo.stdout.readlines()[0].replace("\n", "").split(' ')
    config['mdadm'] = var1[0]
    write_json(configfile, config)

def main():
    parser = argparse.ArgumentParser(description='MD RAID',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--test", dest="test", action='store_true', help="Тестовый режим из файла")
    group1 = parser.add_argument_group('Команды')
    mutex_group1 = group1.add_mutually_exclusive_group(required=True)
    mutex_group1.add_argument("--discovery", dest="discovery", action='store_true', help="Обнаружение md массивов и устройств")
    mutex_group1.add_argument("--state", dest="state", help="Состояние RAID массива")
    mutex_group1.add_argument("--level", dest="level", help="Уровень RAID массива")
    mutex_group1.add_argument("--rebuild", dest="rebuild", help="Синхронизация массива")
    mutex_group1.add_argument("--devicesRaid", dest="devicesRaid", help="Необходимое количество устройств для RAID массива")
    mutex_group1.add_argument("--devicesTotal", dest="devicesTotal", help="Текущее количество устройств")
    mutex_group1.add_argument("--devicesActive", dest="devicesActive", help="Количество активных устройств")
    mutex_group1.add_argument("--devicesWorking", dest="devicesWorking", help="Количество рабочих устройств")
    mutex_group1.add_argument("--devicesFailed", dest="devicesFailed", help="Количество неисправных устройств")
    mutex_group1.add_argument("--devicesSpare", dest="devicesSpare", help="Количество запасных устройств")

    args = parser.parse_args()

    outinfo = None
    """
    Обнаружение контроллеров и дисков
    """
    if args.discovery:
        cmd = ['cat', '/proc/mdstat']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
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
        result = json.dumps({"data": devices})
        print result
        sys.exit(0)

    if args.test:
        outinfo = subprocess.Popen(['cat', 'test/output.txt'], stdout=subprocess.PIPE)
    else:
        cmd = [config['mdadm'], '--detail']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    lstatus = None
    result = None
    if args.state:
        cmd = [config['mdadm'], '--detail', str(args.state)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
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
                elif lstatus[0] == 'active, degraded, recovering':
                    result = '10'
                elif lstatus[0] == 'clean, degraded, recovering':
                    result = '11'
                elif lstatus[0] == 'clean, degraded, resyncing (DELAYED)':
                    result = '12'
    elif args.level:
        cmd = [config['mdadm'], '--detail', str(args.level)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['level'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.rebuild:
        cmd = [config['mdadm'], '--detail', str(args.rebuild)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['rebuild'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.devicesRaid:
        cmd = [config['mdadm'], '--detail', str(args.devicesRaid)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['devicesRaid'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.devicesTotal:
        cmd = [config['mdadm'], '--detail', str(args.devicesTotal)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['devicesRaid'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.devicesActive:
        cmd = [config['mdadm'], '--detail', str(args.devicesActive)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['devicesRaid'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.devicesWorking:
        cmd = [config['mdadm'], '--detail', str(args.devicesWorking)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['devicesRaid'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.devicesFailed:
        cmd = [config['mdadm'], '--detail', str(args.devicesFailed)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['devicesRaid'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.devicesSpare:
        cmd = [config['mdadm'], '--detail', str(args.devicesSpare)]
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['devicesRaid'], line)
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
