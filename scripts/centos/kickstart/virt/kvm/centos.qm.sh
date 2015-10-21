#!/bin/bash

# Copyright (C) 2015 JustHost.ru, Dmitry Shilyaev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Description:
#   Create KVM virtual machine with kickstarter file from the command line.
#
# Requirements:
#   genisoimage, qemu
#

# CentOS version
CENT_OS_VER=7  # 6 or 7

# Change this parameters
USER_ID=<user_id>
VMID=<id_of_the_vm>
VMNAME=<name_of_the_vm>

# HDD size in Gb
HDDGB=5

# RAM size in Gb
MEMMB=1024

# CPU cores
VCPU=1

IPADDR=<ip_of_the_vm>
GW=<gateway_of_the_vm>
NETMASK=<netmask_of_the_vm>
DNS1=<dns1_of_the_vm>
DNS2=<dns2_of_the_vm>

################## do not change #################
SCRIPTDIR=$(pwd)
WORKDIR=${SCRIPTDIR}/${VMID}-$(date +"%S")

mkdir -p ${WORKDIR}
cd ${WORKDIR}

if [ ! -e initrd.img ]
then
    wget http://mirror.yandex.ru/centos/${CENT_OS_VER}/os/x86_64/images/pxeboot/initrd.img
fi

if [ ! -e vmlinuz ]
then
    wget http://mirror.yandex.ru/centos/${CENT_OS_VER}/os/x86_64/images/pxeboot/vmlinuz
fi

echo "Update KS file:"
KICKSTART_TEMPLATE_NAME="centos.${CENT_OS_VER}.ks.tpl"
wget https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/kickstart/virt/kvm/${KICKSTART_TEMPLATE_NAME}

KICKSTART_FILE_NAME="centos.ks"

KICKSTART_TEMPLATE="${WORKDIR}/${KICKSTART_TEMPLATE_NAME}"
KICKSTART_FILE="${WORKDIR}/${KICKSTART_FILE_NAME}"

ISOPATH="/var/lib/vz/template/iso"

# update KS
cp -f ${KICKSTART_TEMPLATE} ${KICKSTART_FILE}
perl -pi -e "s/\|IPADDR\|/${IPADDR}/g" ${KICKSTART_FILE}
perl -pi -e "s/\|GW\|/${GW}/g" ${KICKSTART_FILE}
perl -pi -e "s/\|HOSTNAME\|/${VMNAME}/g" ${KICKSTART_FILE}
perl -pi -e "s/\|NETMASK\|/${NETMASK}/g" ${KICKSTART_FILE}
perl -pi -e "s/\|DNS1\|/${DNS1}/g" ${KICKSTART_FILE}
perl -pi -e "s/\|DNS2\|/${DNS2}/g" ${KICKSTART_FILE}

#create iso
genisoimage -o ksboot.iso ${KICKSTART_FILE}
mv ksboot.iso ${ISOPATH}/

if [ ${CENT_OS_VER} == 7 ]
then
qm create ${VMID} --args "-append 'root=live:http://mirror.yandex.ru/centos/7/os/x86_64/LiveOS/squashfs.img ks=cdrom:/dev/cdrom:/${KICKSTART_FILE_NAME}' -kernel ${WORKDIR}/vmlinuz -initrd ${WORKDIR}/initrd.img" --ide2 local:iso/ksboot.iso,media=cdrom --name ${VMNAME} --net0 rtl8139,rate=50,bridge=vmbr0 --virtio0 local:${HDDGB},format=qcow2,cache=writeback,mbps_rd=5,mbps_wr=5 --bootdisk virtio0 --ostype l26 --memory ${MEMMB} --onboot yes --cores ${VCPU} --sockets 1
else
qm create ${VMID} --args "-append ks=cdrom:/${KICKSTART_FILE_NAME} -kernel ${WORKDIR}/vmlinuz -initrd ${WORKDIR}/initrd.img" --ide2 local:iso/ksboot.iso,media=cdrom --name ${VMNAME} --net0 rtl8139,rate=50,bridge=vmbr0 --virtio0 local:${HDDGB},format=qcow2,cache=writeback,mbps_rd=5,mbps_wr=5 --bootdisk virtio0 --ostype l26 --memory ${MEMMB} --onboot yes --cores ${VCPU} --sockets 1
fi
qm start ${VMID}

qm wait ${VMID}

# unmount cd, remove args
qm set ${VMID} --args "" --ide2 none,media=cdrom
qm set ${VMID} -delete args

qm start ${VMID}


pveum roleadd PVE_KVM_User -privs "VM.PowerMgmt VM.Audit VM.Console VM.Snapshot VM.Backup"
pveum useradd u${USER_ID}@pve -comment 'User u${USER_ID}'
pveum aclmod /vms/${VMID} -users u${USER_ID}@pve -roles PVE_KVM_User

pveum passwd u${USER_ID}@pve
