#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
# Блокировщик
#
# Requirements:
# CentOS 6

import datetime
import subprocess
import argparse
import traceback
import sys
import os

def blocked(blocklist, logfile='./block.log'):
    """
    Процедура блокировки
    """
    outfile = open(logfile, "a")
    for element in blocklist:
        outfile.write(element['ip'] + ' [' + str(datetime.datetime.now()) + '] [' + str(datetime.datetime.now()) + ']\n')
        print 'ip: ' + element['ip'] + ' count: ' + element['count']
        cmd = "/usr/sbin/iptables -A INPUT -s " + element['ip'] +" -j DROP -m comment --comment 'pytin'"
        subprocess.call(cmd, shell=True)
    outfile.close()

def unblocked():
    """
    Процедура разблокировки
    """
    cmd = "/usr/sbin/iptables -A INPUT -s " + element['ip'] +" -j DROP -m comment --comment 'pytin'"
    subprocess.call(cmd, shell=True)
    for element in blocklist:
        print 'ip: ' + element['ip'] + ' count: ' + element['count']
        cmd = "/usr/sbin/iptables -D INPUT -s " + element['ip'] +" -j DROP -m comment --comment 'pytin'"
        subprocess.call(cmd, shell=True)

def main():
#    blocklist = []

    parser = argparse.ArgumentParser(description='DDoS log parser',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-B", "--block", dest="blockpath", help="Путь для блокировки")

    args = parser.parse_args()

    listvar = globals()
    global listvar
    if os.path.exists("./blocklist.py"):
        execfile("./blocklist.py", listvar)
    
    for element in blocklist:
        print 'ip: ' + element['ip'] + ' count: ' + element['count']

    logfile = args.blockpath + '/block.log'
    blocked(blocklist, logfile)

blocklist = []

if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
