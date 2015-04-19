#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт установки DirectAdmin и минимальной настройки
#
# Requirements:
#	CentOS 6

bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/default.sh)

yum -y install nano wget openssh-clients gcc gcc-c++ flex bison make bind bind-libs bind-utils openssl openssl-devel perl perl-CPAN quota libaio libcom_err-devel libcurl-devel gd zlib-devel zip unzip libcap-devel cronie bzip2 cyrus-sasl-devel perl-ExtUtils-Embed autoconf automake libtool which patch db4-devel

bash <(curl http://www.directadmin.com/setup.sh)


### Install BFD and APF

mkdir secdistr && cd secdistr

mkdir bfd && cd bfd
wget http://www.rfxn.com/downloads/bfd-current.tar.gz
tar --strip-components=1 -xzf bfd-current.tar.gz
./install.sh
cd ..

mkdir apf && cd apf
wget http://www.rfxn.com/downloads/apf-current.tar.gz
tar --strip-components=1 -xzf apf-current.tar.gz
./install.sh
cd ..

cp /etc/apf/conf.apf /etc/apf/conf.apf.bkp
perl -pi -e 's/IG_TCP_CPORTS="22"/IG_TCP_CPORTS="20,21,22,25,53,80,110,143,443,465,587,953,993,995,2222"/g' /etc/apf/conf.apf
perl -pi -e 's/IG_UDP_CPORTS=""/IG_UDP_CPORTS="53,953"/g' /etc/apf/conf.apf
perl -pi -e 's/DEVEL_MODE="1"/DEVEL_MODE="0"/g' /etc/apf/conf.apf

apf -r
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

# Генерация паролей
passhtstatus=`perl -le'print map+(A..Z,a..z,0..9)[rand 62],0..15'`
echo "Password for Apache server-status user: "${passhtstatus} >> ~/da.txt
echo "Password for Apache server-status user: "${passhtstatus}
htpasswd -b -c /etc/httpd/conf/secret/passwd info ${passhtstatus}
