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

# Change this parameters
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

# do not change
SCRIPTDIR=$(pwd)
KSFILENAME="centvm.ks"
KSRTFILENAME="vmcurr"

KSTPL="${SCRIPTDIR}/${KSFILENAME}"
KSFILE="${SCRIPTDIR}/${KSRTFILENAME}"

ISOPATH="/var/lib/vz/template/iso"
KSRTFILE="cdrom:/${KSRTFILENAME}"

# update KS
cp -f ${KSTPL} ${KSFILE}
perl -pi -e "s/\|IPADDR\|/${IPADDR}/g" ${KSFILE}
perl -pi -e "s/\|GW\|/${GW}/g" ${KSFILE}
perl -pi -e "s/\|HOSTNAME\|/${VMNAME}/g" ${KSFILE}
perl -pi -e "s/\|NETMASK\|/${NETMASK}/g" ${KSFILE}
perl -pi -e "s/\|DNS1\|/${DNS1}/g" ${KSFILE}
perl -pi -e "s/\|DNS2\|/${DNS2}/g" ${KSFILE}

#create iso
genisoimage -o ksboot.iso ${KSFILE}
mv ksboot.iso ${ISOPATH}/

qm create ${VMID} --args "-append ks=${KSRTFILE} -kernel ${SCRIPTDIR}/vmlinuz -initrd ${SCRIPTDIR}/initrd.img" --ide2 local:iso/ksboot.iso,media=cdrom --name ${VMNAME} --net0 rtl8139,rate=50,bridge=vmbr0 --virtio0 local:${HDDGB},format=qcow2,cache=writeback,mbps_rd=5,mbps_wr=5 --bootdisk virtio0 --ostype l26 --memory ${MEMMB} --onboot yes --cores ${VCPU} --sockets 1
qm start ${VMID}

qm wait ${VMID}

# unmount cd, remove args
qm set ${VMID} --args "" --ide2 none,media=cdrom

qm start ${VMID}
