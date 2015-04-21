import exceptions
import errno

from nginxlib import *
from diradminlib import *


DIRECT_ADMIN_DATA_PATH = '/Users/dmitry/Work/pytin/testdata'
DIRECT_ADMIN_USER_CONF = os.path.join(DIRECT_ADMIN_DATA_PATH, 'users')
DROP_DIR = '/Users/dmitry/Work/pytin/scripts/directadmin/nginx/out'
TPL_FILE = '/Users/dmitry/Work/pytin/scripts/directadmin/nginx/vhost_ssl.conf.tpl'


def safe_create_path(path, mode=0o711):
    if not path:
        raise exceptions.ValueError("path")

    try:
        os.makedirs(path, mode)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise


def main():
    maps_drop_dir = os.path.join(DROP_DIR, 'maps')
    ssl_vhosts_drop_dir = os.path.join(DROP_DIR, 'ssl_vhosts')
    safe_create_path(maps_drop_dir)
    safe_create_path(ssl_vhosts_drop_dir)

    map_users = NginxMap('http_host', 'user')
    map_domains = NginxMap('http_host', 'domain')
    map_subdomains = NginxMap('http_host', 'subdomain')

    for user_name in os.listdir(DIRECT_ADMIN_USER_CONF):
        print "Processing: %s" % user_name

        user_dir = os.path.join(DIRECT_ADMIN_USER_CONF, user_name)

        if os.path.isdir(user_dir):
            da_user_config = DirectAdminUserConfig(user_dir)

            for domain in da_user_config.get_domains():
                map_users.add_item(".%s" % domain.domain_name, '"%s"' % da_user_config.user_name)
                map_domains.add_item(".%s" % domain.domain_name, '"%s"' % domain.domain_name)

                for domain_pointer in domain.get_pointers():
                    map_users.add_item(".%s" % domain_pointer, '"%s"' % da_user_config.user_name)
                    map_domains.add_item(".%s" % domain_pointer, '"%s"' % domain.domain_name)

                for subdomain in domain.get_subdomains():
                    map_subdomains.add_item(".%s.%s" % (subdomain, domain.domain_name), '"%s"' % subdomain)

                config = domain.get_config()
                if config.has_key('SSLCertificateFile') and config.has_key('SSLCertificateKeyFile'):
                    cert_file = config['SSLCertificateFile']
                    key_file = config['SSLCertificateKeyFile']

                    with open(os.path.join(ssl_vhosts_drop_dir, "%s.conf" % domain.domain_name), 'w') as vhost_file:
                        for tpl_line in file(TPL_FILE):
                            tpl_line = tpl_line.replace('{sslkey}', key_file)
                            tpl_line = tpl_line.replace('{sslcrt}', cert_file)
                            vhost_file.write(tpl_line)

    # save all maps
    map_users.save(os.path.join(maps_drop_dir, 'map_users.conf'))
    map_domains.save(os.path.join(maps_drop_dir, 'map_domains.conf'))
    map_subdomains.save(os.path.join(maps_drop_dir, 'map_subdomain.conf'))


if __name__ == "__main__":
    main()
