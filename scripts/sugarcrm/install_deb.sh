apt-get update
apt-get upgrade
apt-get install mysql-server mysql-client
apt-get install apache2 php5

apt-get install php5 php5-cli php5-common php5-curl php5-dev php5-gd php5-imap php5-ldap
apt-get install php5-mhash php5-mysql php5-odbc curl libwww-perl imagemagick

update-rc.d mysql defaults
update-rc.d mysql defaults

# Загруза и распаковка SugarCRMmkdir -p /data/www
mkdir -p /data/www
wget http://garr.dl.sourceforge.net/project/sugarcrm/1%20-%20SugarCRM%206.5.X/SugarCommunityEdition-6.5.X/SugarCE-6.5.20.zip
unzip SugarCE-6.5.20.zip
mv SugarCE-Full-6.5.20 /data/www/sugarcrm
chown -R www-data:www-data /data/www/sugarcrm

# Apache
mkdir /etc/httpd/vhosts
cat <<EOF > /etc/apache2/sites-available/000-default.conf
<VirtualHost *:80>
        ServerAdmin info@domain.ltd
        DocumentRoot "/data/www/sugarcrm"
        ErrorLog ${APACHE_LOG_DIR}/sugarcrm-error.log
        CustomLog ${APACHE_LOG_DIR}/sugarcrm-access.log combined
        AcceptPathInfo On
        <Directory /data/www/sugarcrm>
                AllowOverride All
                Require all granted
        </Directory>
</VirtualHost>
EOF

service apache2 restart

# Генерация паролей
passmysql=`perl -le'print map+(A..Z,a..z,0..9)[rand 62],0..15'`
echo "MySQL password: "${passmysql} > ~/sugarcrm.txt
mysqladmin -u root password ${passmysql}

upload_max_filesize = 16M
/etc/php5/apache2/php.ini
