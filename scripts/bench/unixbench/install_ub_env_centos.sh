#!/usr/bin/env bash

#
# Install UnixBench environment on CentOS 6.x
#

TARGET=/usr/local/unixbench
rm -rf ${TARGET}

cd ~

echo "* Init CentOS"
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/default.sh)

echo "* Install UnixBench"
yum -y install gcc gcc-c++ make libXext-devel
yum -y groupinstall "Development Tools"
yum -y install libX11-devel mesa-libGL-devel perl
rpm -i http://pkgs.repoforge.org/perl-Time-HiRes/perl-Time-HiRes-1.9724-1.el6.rfx.x86_64.rpm

wget -c http://byte-unixbench.googlecode.com/files/unixbench-5.1.3.tgz
tar xvzf unixbench-5.1.3.tgz
cp -r unixbench-5.1.3 ${TARGET}
cd ${TARGET}
make

echo "* Install Zabbix Agent"
rpm -Uvh http://repo.zabbix.com/zabbix/2.2/rhel/6/x86_64/zabbix-release-2.2-1.el6.noarch.rpm
yum -y install zabbix-agent
chkconfig zabbix-agent on
service zabbix-agent restart

perl -pi -e 's/Server=127.0.0.1/Server=zabbix.justhost.ru/g' /etc/zabbix/zabbix_agent.conf
perl -pi -e 's/Server=127.0.0.1/Server=zabbix.justhost.ru/g' /etc/zabbix/zabbix_agentd.conf

zbx_host=$(hostname)
echo "Set zabbix hostname: ${zbx_host}"
perl -pi -e 's/Hostname=Zabbix server/Hostname=${zbx_host}/g' /etc/zabbix/zabbix_agentd.conf

# add user parameter
echo "* Add to cron"
echo "15 */3 * * * root /usr/local/unixbench/zbx_bench_score.sh" > /etc/cron.d/unixbench.score
echo "" >> /etc/cron.d/unixbench.score
/etc/init.d/crond restart

echo "* Install bench score script"
cd ${TARGET}
wget https://raw.githubusercontent.com/servancho/pytin/master/scripts/bench/unixbench/zbx_bench_score.sh
chmod +x zbx_bench_score.sh

echo "UnixBench is installed in ${TARGET}. Issue ./Run to see the results."
