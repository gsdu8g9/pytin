#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# Description:
#   Информация от Adaptec
#
# Requirements:
#   Adaptec
#
# wget --no-check-certificate -P /etc/zabbix https://raw.githubusercontent.com/servancho/pytin/master/scripts/zabbix/zbx_adaptec.py
#
# File: /etc/sudoers.d/arcconf
#   Cmnd_Alias ARCCONF_GETCONFIG = /sbin/arcconf getconfig *, /sbin/arcconf getversion
#   zabbix ALL=(root) NOPASSWD: ARCCONF_GETCONFIG
#
# zabbix_agetnd.conf:
#   Timeout=15

__author__ = 'RemiZOffAlex'
__copyright__ = '(c) RemiZOffAlex'
__license__ = 'MIT'
__email__ = 'remizoffalex@mail.ru'

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

dict_re = {'logdevnum': '^Logical device number ([0-9]+).*$',
    'status': '^\s*Status of logical device\s*:\s*(.*)$',
    'temperature': '^\s*Temperature\s*:\s*([0-9]+).*$',
    'level': '^\s*RAID level\s*:\s*([0-9]+).*$',
    'model': '^\s*Controller Model\s*:\s*(.*)$',
    'controller': '^Controller \#([0-9]+)$',
    'pdevice': '^\s*Device \#([0-9]+)$',
    'pdevicestate': '^\s*State\s*:\s*(.*)$',
    'pdevicesn': '^\s*Serial number\s*:\s*(.*)$'}

configfile = os.path.dirname(os.path.abspath(__file__)) + '/zbx_config.json'
config = {}
if os.path.isfile(configfile):
    config = read_json(configfile)

"""
Решение проблемы с нахождением утилиты
"""
if not 'arcconf' in config:
    outinfo = subprocess.Popen(['which', 'arcconf'], stdout=subprocess.PIPE)
    var1 = outinfo.stdout.readlines()[0].replace("\n", "").split(' ')
    config['arcconf'] = var1[0]
    write_json(os.path.dirname(os.path.abspath(__file__)) + '/zbx_config.json', config)

def main():
    parser = argparse.ArgumentParser(description='Adaptec parser',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--test", dest="test", action='store_true', help="Тестовый режим из файла")
    group1 = parser.add_argument_group('Команды')
    mutex_group1 = group1.add_mutually_exclusive_group(required=True)
    mutex_group1.add_argument("--discovery", dest="discovery", action='store_true', help="Обнаружение")
    mutex_group1.add_argument("--model", dest="model", type=int, help="Модель контроллера")
    mutex_group1.add_argument("--status", dest="status", type=int, help="Статус логического устройства")
    mutex_group1.add_argument("--temperature", dest="temperature", type=int, help="Температура контроллера")
    mutex_group1.add_argument("--level", dest="level", type=int, help="Уровень RAID")
    mutex_group1.add_argument("--drivestate", dest="drivestate", nargs=2, type=int, metavar = ('Controller', 'Drive'), help="Состояние диска")
    mutex_group1.add_argument("--drivesn", dest="drivesn", nargs=2, type=int, metavar = ('Controller', 'Drive'), help="Серийный номер диска")

    args = parser.parse_args()

    outinfo = None
    """
    Обнаружение контроллеров и дисков
    """
    if args.discovery:
        cmd = [config['arcconf'], 'getversion']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen([config['arcconf'], 'getversion'], stdout=subprocess.PIPE)
        controllers = []
        """
        Получить список контроллеров
        """
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            result = re.findall(dict_re['controller'], line)
            if len(result)>0:
                controllers.append( [str(result[0]), []] )
        """
        Получить список дисков на каждом контроллере
        """
        for id_controller,controller in enumerate(controllers):
            cmd = [config['arcconf'], 'getconfig', controller[0], 'pd']
            if os.geteuid() != 0:
                cmd = ['sudo'] + cmd
            outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            for line in outinfo.stdout.readlines():
                line = line.replace("\n", "")
                result = re.findall(dict_re['pdevice'], line)
                if len(result)>0:
                    controller[1].append(result[0])
        """
        Сформировать пакет данных
        """
        devices = []
        for id_controller,controller in enumerate(controllers):
            for id_device,device in enumerate(controller[1]):
                devices.append({"{#CONTROLLER}": controller[0], "{#PDEVICE}": device})
        result = json.dumps({"data": devices})
        print result
        sys.exit(0)

    if args.test:
        outinfo = subprocess.Popen(['cat', 'test/output.txt'], stdout=subprocess.PIPE)
    else:
        cmd = [config['arcconf'], 'getconfig', str(args.model), 'al']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    lstatus = None
    result = None
    if args.model:
        cmd = [config['arcconf'], 'getconfig', str(args.model), 'al']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['model'], line)
            if len(lstatus) > 0:
                result = lstatus
    elif args.status:
        cmd = [config['arcconf'], 'getconfig', str(args.status), 'al']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['status'], line)
            if len(lstatus) > 0:
                if lstatus[0] == 'Optimal':
                    result = '1'
                elif lstatus[0] == 'Failed':
                    result = '2'
                elif lstatus[0] == 'Degraded':
                    result = '3'
                elif lstatus[0] == 'Degraded, Rebuilding':
                    result = '4'
                else:
                    result = '0'
    elif args.temperature:
        cmd = [config['arcconf'], 'getconfig', str(args.temperature), 'al']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['temperature'], line)
            if len(lstatus) > 0:
                result = lstatus
    elif args.level:
        cmd = [config['arcconf'], 'getconfig', str(args.level), 'al']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in outinfo.stdout.readlines():
            line = line.replace("\n", "")
            lstatus = re.findall(dict_re['level'], line)
            if len(lstatus)>0:
                result = lstatus
    elif args.drivestate:
        cmd = [config['arcconf'], 'getconfig', str(args.drivestate[0]), 'pd']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        outtext = outinfo.stdout.readlines()
        for id_device,line in enumerate(outtext):
            line = line.replace("\n", "")
            device = re.findall(dict_re['pdevice'], line)
            if len(device)>0:
                if device[0] == str(args.drivestate[1]):
                    for deviceline in outtext[id_device+2:id_device+25]:
                        line = deviceline.replace("\n", "")
                        devicestate = re.findall(dict_re['pdevicestate'], line)
                        if len(devicestate):
                            if devicestate[0] == 'Online':
                                result = '1'
                            elif devicestate[0] == 'Rebuilding':
                                result = '2'
                            else:
                                result = '0'

    elif args.drivesn:
        cmd = [config['arcconf'], 'getconfig', str(args.drivesn[0]), 'pd']
        if os.geteuid() != 0:
            cmd = ['sudo'] + cmd
        outinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        outtext = outinfo.stdout.readlines()
        for id_device,line in enumerate(outtext):
            line = line.replace("\n", "")
            device = re.findall(dict_re['pdevice'], line)
            if len(device)>0:
                if device[0] == str(args.drivesn[1]):
                    for deviceline in outtext[id_device+2:id_device+25]:
                        line = deviceline.replace("\n", "")
                        devicestate = re.findall(dict_re['pdevicesn'], line)
                        if len(devicestate):
                            result = devicestate

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
