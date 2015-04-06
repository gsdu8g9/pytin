#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт создания образа сетевой загрузки proxmox
#
# Requirements:
#	Linux, Proxmox ISO образ
#
# Original:
#	http://forum.proxmox.com/threads/8484-Proxmox-installation-via-PXE-solution

URL='https://www.proxmox.com/en/downloads?task=callelement&format=raw&item_id=151&element=f85c494b-2b32-4109-b8c1-083cca2b7db6&method=download&args[0]=1269d87c74d77c52e3c11bae309697fd'

rm -rf ./target

mkdir -p ./work/{download,iso,build/initrd.tmp} ./target

wget -O ./work/download/proxmox.iso ${URL}

mount -o loop ./work/download/proxmox.iso ./work/iso

cp ./work/iso/boot/initrd.img ./work/build/
cp ./work/iso/boot/linux26 ./target

pushd ./work/build

mv initrd.img initrd.org.img
gzip -d -S ".img" ./initrd.org.img

pushd initrd.tmp

cpio -i -d < ../initrd.org
cp ../../download/proxmox.iso ./

find . | cpio -H newc -o > ../initrd

popd

gzip -9 -S ".img" initrd

cp ./initrd.img ../../target/

popd

umount ./work/iso

rm -rf ./work/{download,iso,build}
