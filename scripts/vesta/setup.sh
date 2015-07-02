#!/bin/sh

# RemiZOffAlex
#
# Description:
#   Скрипт установки Vesta и минимальной настройки
#
# Usage:
#   Debian/Ubuntu
#       wget https://raw.githubusercontent.com/servancho/pytin/master/scripts/vesta/setup.sh
#       bash setup.sh
#
#   CentOS
#       bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/vesta/setup.sh)

# Detect OS
case $(head -n1 /etc/issue | cut -f 1 -d ' ') in
Debian)

wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/debian/default.sh
bash default.sh
wget http://vestacp.com/pub/vst-install.sh
bash vst-install.sh

;;
Ubuntu)

wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/debian/default.sh
bash default.sh
wget http://vestacp.com/pub/vst-install.sh
bash vst-install.sh

;;

*)

bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/default.sh)
bash <(curl http://vestacp.com/pub/vst-install.sh)

;;
esac

# APF
perl -pi -e 's/IG_TCP_CPORTS="[^\"]*"/IG_TCP_CPORTS="21,22,25,80,110,143,443,465,587,953,993,995,2525,8080,8083,8443"/g' /etc/apf/conf.apf
perl -pi -e 's/IG_UDP_CPORTS="[^\"]*"/IG_UDP_CPORTS="53,953"/g' /etc/apf/conf.apf

# Проблемы с лимитом на открытые файлы
echo "*               soft    nofile          8192" >> /etc/security/limits.conf 
echo "*               hard    nofile          8192" >> /etc/security/limits.conf 
