#version=DEVEL
install

logging --host=log.justhost.ru

url --url=http://mirror.yandex.ru/centos/6/os/x86_64
lang en_US.UTF-8
keyboard us
network --onboot yes --bootproto static --ip |IPADDR| --netmask |NETMASK| --gateway |GW| --noipv6 --nameserver |DNS1| --hostname=|HOSTNAME|
rootpw  --iscrypted $6$e9LAvaKhsKpVFL1U$ummLp..ULwzXADdwSjEahp67NI1lDjwe6Xs0d2s4fUGFQF7/Cfri3EM3cXRPH0Ys5N7cOK9xrx6EjnkCV5a8q1
firewall --service=ssh
authconfig --enableshadow --passalgo=sha512
selinux --disabled
timezone --utc Europe/Moscow
bootloader --location=mbr --driveorder=vda --append="nomodeset crashkernel=auto rhgb quiet"
# The following is the partition information you requested
# Note that any partitions you deleted are not expressed
# here so unless you clear all partitions first, this is
# not guaranteed to work
clearpart --all --drives=vda

autopart

repo --name="CentOS"  --baseurl=http://mirror.yandex.ru/centos/6/os/x86_64 --cost=100

poweroff

%packages
@core
nano
wget
mc
%end

%pre --log=/root/install-pre.log
echo "Linux box by Justhost.ru. Created `/bin/date`" > /etc/motd

echo "nameserver |DNS1|" > /etc/resolv.conf
echo "nameserver |DNS2|" >> /etc/resolv.conf

dd if=/dev/zero of=/dev/vda bs=512 count=100
parted -s /dev/vda mklabel msdos
%end

%post --log=/root/install-post.log
exec < /dev/tty6 > /dev/tty6
chvt 6

PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH

bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)

%end
