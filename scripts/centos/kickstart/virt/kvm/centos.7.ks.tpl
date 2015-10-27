#version=RHEL7
logging --host=log.justhost.ru

# System authorization information
auth --enableshadow --passalgo=sha512

# Use network installation
url --url=http://mirror.yandex.ru/centos/7/os/x86_64

# Use graphical install
graphical

# Run the Setup Agent on first boot
firstboot --enable
ignoredisk --only-use=vda

# Keyboard layouts and system language
lang en_US.UTF-8
keyboard us
timezone --utc Europe/Moscow

# Network information
network --onboot yes --bootproto static --ip |IPADDR| --netmask |NETMASK| --gateway |GW| --noipv6 --nameserver |DNS1| --hostname=|HOSTNAME|

# Root password
rootpw  --iscrypted $6$e9LAvaKhsKpVFL1U$ummLp..ULwzXADdwSjEahp67NI1lDjwe6Xs0d2s4fUGFQF7/Cfri3EM3cXRPH0Ys5N7cOK9xrx6EjnkCV5a8q1

# System bootloader configuration
bootloader --append=" crashkernel=auto" --location=mbr --boot-drive=vda
autopart --type=lvm

# Partition clearing information
clearpart --none --initlabel

# System settings
selinux --disabled
firewall --service=ssh
services --enabled=NetworkManager,sshd
eula --agreed

poweroff


%packages
@core
nano
wget
mc
net-tools
%end

%pre --log=/root/install-pre.log
echo "CentOS 7.x box by Justhost.ru. Created `/bin/date`" > /etc/motd

echo "nameserver |DNS1|" > /etc/resolv.conf
echo "nameserver |DNS2|" >> /etc/resolv.conf
%end

%post --log=/root/install-post.log
exec < /dev/tty6 > /dev/tty6
chvt 6

PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH

bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)

%end
