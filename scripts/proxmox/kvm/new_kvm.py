#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import time

from proxmoxer import ProxmoxAPI

userID=''
vmid=100
hvname='node1'

nodes={'node1': {'name': 'IPorHOSTNAME', 'password': 'PASSWORD'},
       'node2': {'name': 'IPorHOSTNAME', 'password': 'PASSWORD'}}

ostemplates=['local:vztmpl/debian-7.0-x86.tar.gz',
    'local:vztmpl/ubuntu-14.04-x86.tar.gz',
    'local:vztmpl/ubuntu-14.04-x86_64.tar.gz',
    'local:vztmpl/centos-6-x86.tar.gz',
    'local:vztmpl/centos-6-x86_64.tar.gz',
    'local:vztmpl/centos-7-x86_64.tar.gz']

proxmox = ProxmoxAPI(nodes[hvname]['name'], user='root@pam',
                     password=nodes[hvname]['password'],
                     verify_ssl=False)

def isUserExist(proxmox, user):
    result = False
    for item in proxmox.access.users.get():
        if item['userid'] == user:
            result = True
    return result

if not isUserExist(proxmox, 'u' + userID + '@pve'):
    proxmox.access.users.create(userid='u' + userID + '@pve', password='PASSWORD')

node = proxmox.nodes(hvname)
node.qemu.create(vmid=vmid,
                   ostype='l26',
                   name=userID + '.users.justhost.ru',
                   storage='local',
                   memory=512,
                   sockets=1,
                   cores=1,
                   net0='rtl8139,rate=50,bridge=vmbr0',
                   virtio0='local:' + str(vmid) + '/vm-' + str(vmid) + '-disk-1.qcow2,cache=writeback,format=qcow2,size=5G',
                   cdrom='none')

# Время на распаковку архива контейнера
time.sleep(10)

node.qemu(vmid).config.set(onboot=1)

# ACL
proxmox.access.acl.set(path='/vms/' + str(vmid), roles=['PVEVMUser'], users=['u' + userID + '@pve'])

# Start
node.qemu(vmid).status.start.post()
