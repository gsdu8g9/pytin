#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт установки DirectAdmin и минимальной настройки
#
# Requirements:
#	CentOS 6
#
# bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/directadmin/setup_da.sh)
#

yum -y install nano wget openssh-clients gcc gcc-c++ flex bison make bind bind-libs bind-utils openssl openssl-devel perl perl-CPAN quota libaio libcom_err-devel libcurl-devel gd zlib-devel zip unzip libcap-devel cronie bzip2 cyrus-sasl-devel perl-ExtUtils-Embed autoconf automake libtool which patch db4-devel

bash <(curl http://www.directadmin.com/setup.sh)

### Замена proftpd на pureftpd
cd /usr/local/directadmin/custombuild
./build set proftpd no
./build set pureftpd yes
./build pureftpd

### Begin: Not install security for OpenVZ
ip link | grep venet
if [ $? -ne 0 ];
then

# /etc/sysconfig/iptables-config
# IPTABLES_MODULES="ip_conntrack_ftp"

### Configure BFD and APF

cp /etc/apf/conf.apf /etc/apf/conf.apf.bkp
# ingress tcp
perl -pi -e 's/IG_TCP_CPORTS="[^\"]*"/IG_TCP_CPORTS="20,21,22,25,53,80,110,143,443,465,587,953,993,995,2222,30000_35000"/g' /etc/apf/conf.apf
perl -pi -e 's/IG_UDP_CPORTS="[^\"]*"/IG_UDP_CPORTS="53,953"/g' /etc/apf/conf.apf

# egress tcp
perl -pi -e 's/EG_TCP_CPORTS="[^\"]*"/EG_TCP_CPORTS="21,25,80,443,43,30000_35000"/g' /etc/apf/conf.apf

perl -pi -e 's/DEVEL_MODE="1"/DEVEL_MODE="0"/g' /etc/apf/conf.apf

apf -r
fi
### End: Not install security for OpenVZ

/etc/init.d/crond restart


cat <<EOF > /etc/httpd/conf/extra/httpd-info.conf
<Location /server-status>
    SetHandler server-status
    AuthType Basic
    AuthName Stat
    AuthGroupFile /dev/null
    AuthUserFile /etc/httpd/conf/secret/passwd
    require valid-user
    Order deny,allow
    Deny from all
    Allow from all
</Location>

ExtendedStatus On

<Location /server-info>
    SetHandler server-info
    Order deny,allow
    Deny from all
    Allow from .example.com
</Location>
EOF

mkdir -p /etc/httpd/conf/secret

### Генерация пароля для server-status (info)
passhtstatus=`perl -le'print map+(A..Z,a..z,0..9)[rand 62],0..15'`
echo "Password for Apache server-status user: "${passhtstatus} >> ~/server-status.txt
echo "Password for Apache server-status user: "${passhtstatus}
htpasswd -b -c /etc/httpd/conf/secret/passwd info ${passhtstatus}
