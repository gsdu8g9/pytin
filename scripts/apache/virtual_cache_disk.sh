#!/bin/sh

# RemiZOffAlex
#
# Description:
#	Скрипт настройки кеширования
#
# Usage:
#   Debian/Ubuntu
#       wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/apache/virtual_cache_disk.sh
#       bash setup.sh
#
#   CentOS
#       bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/apache/virtual_cache_disk.sh)

# Detect OS
case $(head -n1 /etc/issue | cut -f 1 -d ' ') in
Debian|Ubuntu)
cat <<EOF > /etc/apache2/conf.d/httpd-cache.conf
#   Cache Configuration

LoadModule cache_module /usr/lib/apache2/modules/mod_dav.so/mod_cache.so

<IfModule mod_cache.c>
LoadModule disk_cache_module /usr/lib/apache2/modules/mod_dav.so/mod_disk_cache.so
<IfModule mod_disk_cache.c>
CacheRoot /data/www/cacheroot
CacheEnable disk /
CacheDirLevels 5
CacheDirLength 3
CacheMaxFileSize 8192000
</IfModule> 
</IfModule>
EOF

echo 'tmpfs /data/www/cacheroot tmpfs defaults,nodev,nosuid,size=1G 0 0' >> /etc/fstab

mkdir -p /data/www/cacheroot
mount /data/www/cacheroot
service apache2 restart

;;
*)

cat <<EOF > /etc/httpd/conf.d/httpd-cache.conf
#   Cache Configuration

LoadModule cache_module modules/mod_cache.so

<IfModule mod_cache.c>
LoadModule disk_cache_module modules/mod_disk_cache.so
<IfModule mod_disk_cache.c>
CacheRoot /data/www/cacheroot
CacheEnable disk /
CacheDirLevels 5
CacheDirLength 3
CacheMaxFileSize 8192000
</IfModule> 
</IfModule>
EOF

echo 'tmpfs /data/www/cacheroot tmpfs defaults,nodev,nosuid,size=1G 0 0' >> /etc/fstab

mkdir -p /data/www/cacheroot
mount /data/www/cacheroot
service httpd restart

;;
esac
