#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch
import os

######################################
## НАСТРОЙКИ СКРИПТА
confdir = "/etc/vz/conf/"
rulefile = "/etc/vz/shaper/rules.sh"
bandwidth = "50mbit"
shaper_id_eth0 = 100
shaper_id_venet0 = 100

######################################
## ШАБЛОН СКРИПТА НАСТРОЙКИ ШЕЙПЕРА

fileheader = """#!/bin/bash
# shaper configuration file

##### ЧИСТКА ОТ СТАРЫХ ПРАВИЛ #####
tc qdisc del dev vmbr0 root
tc -s qdisc ls dev vmbr0

tc qdisc del dev venet0 root
tc -s qdisc ls dev venet0
##### ЧИСТКА ОТ СТАРЫХ ПРАВИЛ #####
"""

# vmbr0

eth0header = """
DEV=vmbr0
tc qdisc del dev $DEV root 2>/dev/null
tc qdisc add dev $DEV root handle 1: htb default 1 r2q 3000
tc class add dev $DEV parent 1: classid 1:1 htb rate 1000mbit burst 10mb
"""

eth0template = """
# vzid {VPSID} tarif {BANDWIDTH} ip {IP}
DEV=vmbr0

tc class add dev $DEV parent 1:1 classid 1:{CLASS} htb rate {BANDWIDTH} ceil {BANDWIDTH} burst 1mb
tc qdisc add dev $DEV parent 1:{CLASS} handle {CLASS}: sfq perturb 5 #quantum 5000b
"""

eth0match_ipv4 = """
tc filter add dev $DEV protocol ip parent 1:0 prio 1 u32 match ip src {IPV4} flowid 1:{CLASS}
"""

eth0match_ipv6 = """
tc filter add dev $DEV protocol ipv6 parent 1:0 prio 1 u32 match ip6 src {IPV6} flowid 1:{CLASS}
"""

# venet0

venet0header = """
DEV=venet0
tc qdisc del dev $DEV root 2>/dev/null
tc qdisc add dev $DEV root handle 1: htb default 1 r2q 3000
tc class add dev $DEV parent 1: classid 1:1 htb rate 1000mbit burst 10mb
"""

venet0template = """
# vzid {VPSID} tarif {BANDWIDTH} ip {IP}
DEV=venet0

tc class add dev $DEV parent 1:1 classid 1:{CLASS} htb rate {BANDWIDTH} ceil {BANDWIDTH} burst 1mb
tc qdisc add dev $DEV parent 1:{CLASS} handle {CLASS}: sfq perturb 5 #quantum 5000b
"""

venet0match_ipv4 = """
tc filter add dev $DEV protocol ip parent 1:0 prio 1 u32 match ip dst {IPV4} flowid 1:{CLASS}
"""

venet0match_ipv6 = """
tc filter add dev $DEV protocol ipv6 parent 1:0 prio 1 u32 match ip6 dst {IPV6} flowid 1:{CLASS}
"""

# iface
ifaceHeader = """
# vzid {VPSID} tarif {BANDWIDTH} iface {IFACE}
DEV={IFACE}
"""

ifaceTemplate = """
/sbin/ethtool $DEV | /bin/grep "Link detected: yes" > /dev/null 2>/dev/null
if [ $? == 0 ]
then
	tc qdisc del dev $DEV root
	tc qdisc add dev $DEV root handle 1: htb default 10
	tc class add dev $DEV parent 1: classid 1:1 htb rate {BANDWIDTH} burst 15k
	tc class add dev $DEV parent 1:1 classid 1:{CLASS} htb rate {BANDWIDTH} burst 15k
	tc qdisc add dev $DEV parent 1:{CLASS} handle {CLASS}: sfq perturb 10
fi
"""

## Функция проверки адреса IPv6
def check_ipv6(ip):
    result = False
    if ip.find(':') != -1:
        result = True
    return result


######################################
## КОД СКРИПТА IP_ADDRESS
# получает список и настройки виртуалок из папки конфигов OpenVZ
def getvz(file):
    # берем список конфигов
    vzid = file.split(".", 1)[0]
    vztarif = None
    vzip = None
    vziface = None

    # открываем файл, узнаем список IP адресов или сетевых интерфейсов
    with open(confdir + file) as f:
        for line in f:
            if line[0] == "#":
                continue

            ar = line.split("=", 1)

            if ar[0] == "IP_ADDRESS":
                vzip = ar[1].replace('"', '').strip().split(" ")
                for ip in vzip:
                    if ip == '':
                        vzip.remove(ip)
                if len(vzip):
                    genconfIP((vzid, bandwidth, vzip))
                continue

            # Пример: NETIF="ifname=eth0,mac=E6:AF:EC:24:82:DD,host_ifname=veth13777.0,host_mac=4A:7E:CC:C1:E0:7B,bridge=vmbr0"
            if ar[0] == "NETIF":
                vzifaces = []
                if ar[1].find('host_ifname') != -1:
                    for netline in ar[1].replace('"', '').split(","):
                        vziface = netline.split("=")
                        if vziface[0] == "host_ifname":
                            vzifaces.append(vziface[1])
                if len(vzifaces):
                    genconfIFACE((vzid, bandwidth, vzifaces))
                continue


# записывает команды настройки шейпера в sh файл
def genconfIP(vz):
    global shaper_id_eth0, shaper_id_venet0
    with open(rulefile, "a") as f:

        # eth0 rules
        f.write(eth0template
                .replace("{VPSID}", vz[0])
                .replace("{CLASS}", str(shaper_id_eth0))
                .replace("{BANDWIDTH}", vz[1])
                .replace("{IP}", str(vz[2])))
        for ip in vz[2]:
            if check_ipv6(ip):
                f.write(eth0match_ipv6
                        .replace("{VPSID}", vz[0])
                        .replace("{CLASS}", str(shaper_id_eth0))
                        .replace("{IPV6}", ip))
            else:
                f.write(eth0match_ipv4
                        .replace("{VPSID}", vz[0])
                        .replace("{CLASS}", str(shaper_id_eth0))
                        .replace("{IPV4}", ip))
            shaper_id_eth0 += 1

        # venet0 rules
        f.write(venet0template
                .replace("{VPSID}", vz[0])
                .replace("{CLASS}", str(shaper_id_venet0))
                .replace("{BANDWIDTH}", vz[1])
                .replace("{IP}", str(vz[2])))
        for ip in vz[2]:
            if check_ipv6(ip):
                f.write(venet0match_ipv6
                        .replace("{VPSID}", vz[0])
                        .replace("{CLASS}", str(shaper_id_venet0))
                        .replace("{IPV6}", ip))
            else:
                f.write(venet0match_ipv4
                        .replace("{VPSID}", vz[0])
                        .replace("{CLASS}", str(shaper_id_venet0))
                        .replace("{IPV4}", ip))
        shaper_id_venet0 += 1


# записывает команды настройки шейпера в sh файл
def genconfIFACE(vz):
    with open(rulefile, "a") as f:
        shaper_id = 100
        for iface in vz[2]:
            f.write(ifaceHeader
                    .replace("{VPSID}", vz[0])
                    .replace("{CLASS}", str(shaper_id))
                    .replace("{BANDWIDTH}", vz[1])
                    .replace("{IFACE}", iface))
            f.write(ifaceTemplate
                    .replace("{VPSID}", vz[0])
                    .replace("{CLASS}", str(shaper_id))
                    .replace("{BANDWIDTH}", vz[1])
                    .replace("{IFACE}", iface))
            shaper_id += 1


# Заголовок файла
def writeheader():
    with open(rulefile, "w") as f:
        # file header
        f.write(fileheader)

        # eth0 rules
        f.write(eth0header)

        # venet0 rules
        f.write(venet0header)

# Заголовок файла
writeheader()

# Получаем список VPSок
for file in os.listdir(confdir):
    if fnmatch.fnmatch(file, '*.conf') and file != "0.conf":
        getvz(file)

# Сделать файл исполнимым
os.chmod(rulefile, 0755)

# применили правила
os.system(rulefile)