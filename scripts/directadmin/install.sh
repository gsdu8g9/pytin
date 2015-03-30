bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/default.sh)

yum -y install nano wget openssh-clients gcc gcc-c++ flex bison make bind bind-libs bind-utils openssl openssl-devel perl perl-CPAN quota libaio libcom_err-devel libcurl-devel gd zlib-devel zip unzip libcap-devel cronie bzip2 cyrus-sasl-devel perl-ExtUtils-Embed autoconf automake libtool which patch db4-devel

bash <(curl http://www.directadmin.com/setup.sh)

cat <<EOF > /etc/sysconfig/iptables
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 20 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 21 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 25 -j ACCEPT
-A INPUT -p tcp --dport 53 -j ACCEPT
-A INPUT -p udp --dport 53 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 110 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 143 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 465 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 587 -j ACCEPT
-A INPUT -p tcp --dport 953 -j ACCEPT
-A INPUT -p udp --dport 953 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 993 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 995 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 2222 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
COMMIT
EOF

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

htpasswd -c /etc/httpd/conf/secret/passwd info
