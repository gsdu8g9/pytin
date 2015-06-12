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
apt-get -y install wget nano ntpdate ntp

ntpdate -d ntp1.vniiftri.ru

sed -i 's/.*history-search-backward$/"\\e[A": history-search-backward/g' /etc/inputrc
sed -i 's/.*history-search-forward$/"\\e[B": history-search-forward/g' /etc/inputrc
