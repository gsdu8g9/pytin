#!/usr/bin/env bash

VMID=
TEMPLATE=centos-6-x86_64-minimal
USER_ID=

IP_ADDRS=(ip1 ip2)
HDD_GB=
RAM_MB=
VCPU_NUM=
ROOT_PASS=


pvectl create ${VMID} /var/lib/vz/template/cache/${TEMPLATE}.tar.gz -disk ${HDD_GB}
vzctl set ${VMID} --hostname u${USER_ID}.users.justhost.ru --save

for IP in ${IP_ADDRS[*]}
do
    vzctl set ${VMID} --ipadd ${IP} --save
done

vzctl set ${VMID} --swap 0 --ram ${RAM_MB}M --save
vzctl set ${VMID} --nameserver 46.17.40.200 --nameserver 46.17.46.200 --searchdomain justhost.ru --save
vzctl set ${VMID} --onboot yes --save
vzctl set ${VMID} --cpus ${VCPU_NUM} --save
vzctl start ${VMID}
vzctl set ${VMID} --userpasswd root:${ROOT_PASS} --save

pveum roleadd PVE_KVM_User -privs "VM.PowerMgmt VM.Audit VM.Console VM.Snapshot VM.Backup"
pveum useradd u${USER_ID}@pve -comment 'User u${USER_ID}'
pveum aclmod /vms/${VMID} -users u${USER_ID}@pve -roles PVE_KVM_User

echo "Root is: " ${ROOT_PASS}
pveum passwd u${USER_ID}@pve
