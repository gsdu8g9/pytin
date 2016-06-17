#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт создания образа сетевой загрузки Proxmox VE версии 4
#
# Requirements:
#	Linux, Proxmox ISO образ

# Удаляем все предыдущие сборки
rm -rf ./target ./work

# Создаём структуру
mkdir -p ./work/{iso,build} ./target

mount -o loop ./proxmox.iso ./work/iso

cp ./work/iso/boot/linux26 ./target/

pushd ./work/build

# Распаковка initrd.img
gzip -cd ../iso/boot/initrd.img | cpio -imd --quiet

# Копируем образ
cp ../../proxmox.iso ./

# Патчим скрипт init
cp ./init ./init.orig
patch init.orig -i ../../init.patch -o init

# Упаковка образа initrd.img
find . | cpio --quiet -H newc -o | gzip -9 -n > ../../target/initrd.img

popd

umount ./work/iso

# Удаляем сборочный мусор
rm -rf ./work
