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

%include /tmp/part-include

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

# KVM
if [ -b /dev/vda ] ; then
    echo "bootloader --location=mbr --driveorder=vda --append=\"nomodeset crashkernel=auto rhgb quiet\"" > /tmp/part-include

    # Очистка диска
    echo "clearpart --all --drives=vda --initlabel" >> /tmp/part-include

    # Разбивка диска LVM
    echo "part /boot --size=512 --ondisk=vda --asprimary --fstype=ext4" >> /tmp/part-include
    echo "part pv.01 --size=1 --grow --ondisk=vda" >> /tmp/part-include
    echo "volgroup vg_jh pv.01" >> /tmp/part-include
    echo "logvol / --vgname=vg_jh --size=1 --grow --name=lv_root" >> /tmp/part-include

# Физический сервер
elif [ -b /dev/sda ] ; then

    hds=""
    mymedia=""

    for file in /sys/block/sd*; do
    hds="$hds $(basename $file)"
    done

    set $hds
    numhd=$(echo $#)

    drive1=$(echo $hds | cut -d' ' -f1)
    drive2=$(echo $hds | cut -d' ' -f2)


    if [ $numhd == "2" ]  ; then
        echo "# Автоматическая разбивка RAID I, генерируемая %pre для 2 дисков" > /tmp/part-include
        echo "bootloader --location=mbr --timeout=0 --driveorder=sda,sdb --append=\"crashkernel=auto rhgb quiet\"" >> /tmp/diskinfo

        # Очистка диска
        echo "clearpart --all" >> /tmp/part-include
        # /boot 512MB
        echo "part raid.01 --ondisk=sda --asprimary --size=512" >> /tmp/part-include
        echo "part raid.02 --ondisk=sdb --asprimary --size=512" >> /tmp/part-include
        echo "raid /boot --fstype=ext4 --level=1 --device=md0 raid.01 raid.02" >> /tmp/part-include
        # / 10GB = 10240
        echo "part raid.11 --ondisk=sda --size=10240" >> /tmp/part-include
        echo "part raid.12 --ondisk=sdb --size=10240" >> /tmp/part-include
        raid /      --fstype=ext4 --level=1 --device=md1 raid.11 raid.12
        # /tmp 5GB = 5120
        echo "part raid.21 --ondisk=sda --size=5120" >> /tmp/part-include
        echo "part raid.22 --ondisk=sdb --size=5120" >> /tmp/part-include
        echo "raid /tmp   --fstype=ext4 --level=1 --device=md2 raid.21 raid.22" >> /tmp/part-include
        # swap 8GB = 8192
        echo "part raid.31 --ondisk=sda --size=8192" >> /tmp/part-include
        echo "part raid.32 --ondisk=sdb --size=8192" >> /tmp/part-include
        echo "raid swap  --fstype=swap --level=1 --device=md3 raid.31 raid.32" >> /tmp/part-include
        # /usr 10GB = 10240
        echo "part raid.41 --ondisk=sda --size=10240" >> /tmp/part-include
        echo "part raid.42 --ondisk=sdb --size=10240" >> /tmp/part-include
        echo "raid /tmp   --fstype=ext4 --level=1 --device=md4 raid.41 raid.42" >> /tmp/part-include
        # /var 60 = 61440
        echo "part raid.51 --ondisk=sda --size=61440" >> /tmp/part-include
        echo "part raid.52 --ondisk=sdb --size=61440" >> /tmp/part-include
        echo "raid /tmp   --fstype=ext4 --level=1 --device=md5 raid.51 raid.52" >> /tmp/part-include
        # /home Всё доступное пространство
        echo "part raid.61 --ondisk=sda --size=1024 --grow" >> /tmp/part-include
        echo "part raid.62 --ondisk=sdb --size=1024 --grow" >> /tmp/part-include
        echo "raid /home   --fstype=ext4 --level=1 --device=md6 raid.61 raid.62" >> /tmp/part-include

    else
        echo "#partitioning scheme generated in %pre for 1 drive" > /tmp/part-include
        echo "bootloader --location=mbr --timeout=0 --driveorder=sda --append=\"crashkernel=auto rhgb quiet\"" >> /tmp/diskinfo

        # Очистка диска
        echo "clearpart --all" >> /tmp/part-include
        echo "part /boot --fstype ext4  --asprimary --size 512" >> /tmp/part-include
        echo "part / --fstype ext4 --size 10240" >> /tmp/part-include
        echo "part /tmp --fstype ext4 --size 5120" >> /tmp/part-include
        # echo "part swap --fstype=swap --size 5120" >> /tmp/part-include
        echo "part /usr --fstype ext4 --size 10240" >> /tmp/part-include
        echo "part /var --fstype ext4 --size 61440" >> /tmp/part-include
        echo "part /home --fstype ext4 --size 1024 --grow" >> /tmp/part-include
    fi

fi

%end

%post --log=/root/install-post.log
exec < /dev/tty6 > /dev/tty6
chvt 6

PATH=/bin:/sbin:/usr/bin:/usr/sbin
export PATH

bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)

%end
