#!/bin/sh

# RemiZOffAlex
#
# Description:
#   Скрипт установки Vesta и минимальной настройки
#
# Usage:
#   Debian/Ubuntu
#       wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/vesta/setup.sh
#       bash setup.sh
#
#   CentOS
#       bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/vesta/setup.sh)

function set_conf {
    ### Begin: Not install security for OpenVZ
    ip link | grep venet
    if [ $? -ne 0 ];
    then

        # APF
        perl -pi -e 's/IG_TCP_CPORTS="[^\"]*"/IG_TCP_CPORTS="21,22,25,80,110,143,443,465,587,953,993,995,2525,8080,8083,8443,12000_12100"/g' /etc/apf/conf.apf
        perl -pi -e 's/IG_UDP_CPORTS="[^\"]*"/IG_UDP_CPORTS="53,953"/g' /etc/apf/conf.apf

    fi

    # Проблемы с лимитом на открытые файлы
    # ulimit -n
    echo "*               soft    nofile          8192" >> /etc/security/limits.conf
    echo "*               hard    nofile          8192" >> /etc/security/limits.conf
    echo "root            soft    nofile          8192" >> /etc/security/limits.conf
    echo "root            hard    nofile          8192" >> /etc/security/limits.conf
}

# Detect OS
case $(head -n1 /etc/issue | cut -f 1 -d ' ') in
Debian|Ubuntu)
    wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/debian/default.sh
    wget http://vestacp.com/pub/vst-install.sh -O /root/vst-install.sh
    bash default.sh
    set_conf
    ;;
CentOS)
    bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)
    curl -o /root/vst-install.sh http://vestacp.com/pub/vst-install.sh
    set_conf
    ;;
    *)
    ;;
esac

bash /root/vst-install.sh --force --lang ru
