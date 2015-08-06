#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт обновления свежеустановленной ОС Debian или Ubuntu
#	и настройки для быстрого поиска по истории команд
#
# Requirements:
#	Debian/Ubuntu
#
# Usage:
#   Debian:
#       wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/debian/default.sh
#       bash default.sh

# Detect OS
case $(head -n1 /etc/issue | cut -f 1 -d ' ') in
Debian)
    case $(head -n1 /etc/issue | grep -o '7') in
    7)
        apt-get -y install debian-keyring debian-archive-keyring
    ;;
    *)
    ;;
    esac
;;
Ubuntu)
    case $(head -n1 /etc/issue | grep -o '14.04') in
    14.04)
        sudo apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 40976EAF437D05B5
        sudo apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 3B4FE6ACC0B21F32
    ;;
    esac
;;
*)
    typeos="rhel"
;;
esac

apt-get -y update
apt-get -y upgrade
apt-get -y install wget nano ntpdate ntp mc

ntpdate -d ntp1.vniiftri.ru

sed -i 's/.*history-search-backward$/"\\e[A": history-search-backward/g' /etc/inputrc
sed -i 's/.*history-search-forward$/"\\e[B": history-search-forward/g' /etc/inputrc

### Begin: Not install security for OpenVZ
ip link | grep venet
if [ $? -ne 0 ];
then

### Install BFD and APF
mkdir secdistr && cd secdistr

mkdir apf && cd apf
wget http://www.rfxn.com/downloads/apf-current.tar.gz
tar --strip-components=1 -xzf apf-current.tar.gz
./install.sh
cd ..

cp /etc/apf/conf.apf /etc/apf/conf.apf.bkp
perl -pi -e 's/DEVEL_MODE="1"/DEVEL_MODE="0"/g' /etc/apf/conf.apf

# For OpenVZ
ip link | grep venet
if [ $? -eq 0 ];
then
    perl -pi -e 's/IFACE_IN="eth0"/IFACE_IN="venet0"/g' /etc/apf/conf.apf
    perl -pi -e 's/IFACE_OUT="eth0"/IFACE_OUT="venet0"/g' /etc/apf/conf.apf
    perl -pi -e 's/SET_MONOKERN="0"/SET_MONOKERN="1"/g' /etc/apf/conf.apf
fi

echo "10.0.0.0/24" >> /etc/apf/allow_hosts.rules


mkdir bfd && cd bfd
wget http://www.rfxn.com/downloads/bfd-current.tar.gz
tar --strip-components=1 -xzf bfd-current.tar.gz
./install.sh
cd ..

fi
