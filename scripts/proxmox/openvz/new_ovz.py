#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

from proxmoxer import ProxmoxAPI

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


proxmox.access.users.create(userid='uID@pve', password='PASSWORD')

node = proxmox.nodes(hvname)
node.openvz.create(vmid=100,
                   ostemplate=ostemplates[4],
                   hostname='ID.users.justhost.ru',
                   storage='local',
                   memory=512,
                   swap=0,
                   cpus=1,
                   disk=5,
                   password='PASSWORD',
                   ip_address='IP',
                   nameserver='46.17.40.200 46.17.46.200')

node.openvz(100).config.set(onboot=1, searchdomain='justhost.ru')

# ACL
proxmox.access.acl.set(path='/vms/100', roles=['PVEVMUser'], users=['uID@pve'])

# Start
node.openvz(100).status.start.post()
