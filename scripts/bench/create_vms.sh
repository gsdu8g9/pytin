#!/bin/bash

#
# Create many VMs to test hypervisor nodes.
#
# Usage: <VM_ID> <count>
#   VM_ID: ID of the VM used as template (usually instance with UnixBench)
#   count: how many VMs to create
#

echo "Creating VMs. Usage: <Template VM ID> <count>"

TPL_VM_ID=$1
VM_COUNT=$2
CURRENT_COUNT=$(qm list | grep 14 |  wc -l)

echo "Clone standard VM: ${TPL_VM_ID}"

START_ID=$(( CURRENT_COUNT + 1000000 )) # do not interfere with existing IDs
END_ID=$(( START_ID + VM_COUNT ))

for (( vmid=${START_ID}; vmid<${END_ID}; vmid++ ))
do
   echo "Creating ${vmid}"
   qm clone ${TPL_VM_ID} ${vmid} -full
   qm start ${vmid}
done
