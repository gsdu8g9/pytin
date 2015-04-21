import os


def uniq_list(list_obj):
    ptr_map = {pointer: pointer for pointer in list_obj}
    return sorted(ptr_map.keys())


class DirectAdminUserDomain:
    def __init__(self, user_config, domain_name):
        assert user_config, "DirectAdmin directory object must be specified"
        assert domain_name, "Domain name must be specified"

        self.user_config = user_config
        self.domain_name = domain_name
        self.config = {}
        self.pointers = []
        self.subdomains = []
        self.ips = []

        self._load_subdomains()
        self._load_pointers()
        self._load_ips()
        self._load_config()

    def _load_config(self):
        domain_config_file = os.path.join(self.user_config.user_dir, 'domains', "%s.conf" % self.domain_name)
        if os.path.exists(domain_config_file):
            for domain_config in file(domain_config_file):
                domain_config = domain_config.strip()
                conf_key, conf_value = domain_config.split('=')

                self.config[conf_key] = conf_value

    def _load_pointers(self):
        pointers_file = os.path.join(self.user_config.user_dir, 'domains', "%s.pointers" % self.domain_name)
        if os.path.exists(pointers_file):
            new_pointers = []
            for domain_pointer_info in file(pointers_file):
                domain_pointer_info = domain_pointer_info.strip()
                domain_pointer, point_type = domain_pointer_info.split('=')
                new_pointers.append(domain_pointer)

            self.pointers = uniq_list(self.pointers + new_pointers)

    def _load_subdomains(self):
        subdomains_file = os.path.join(self.user_config.user_dir, 'domains', "%s.subdomains" % self.domain_name)
        if os.path.exists(subdomains_file):
            new_subdomains = []
            for subdomain in file(subdomains_file):
                subdomain = subdomain.strip()
                new_subdomains.append(subdomain)

            self.subdomains = uniq_list(self.subdomains + new_subdomains)

    def _load_ips(self):
        ips_file = os.path.join(self.user_config.user_dir, 'domains', "%s.ip_list" % self.domain_name)
        if os.path.exists(ips_file):
            new_ips = []
            for newip in file(ips_file):
                newip = newip.strip()
                new_ips.append(newip)

            self.ips = uniq_list(self.ips + new_ips)

    def get_pointers(self):
        return self.pointers

    def get_subdomains(self):
        return self.subdomains

    def get_ips(self):
        return self.ips

    def get_config(self):
        return self.config


class DirectAdminUserConfig:
    def __init__(self, user_dir):
        assert user_dir, "User dir must be specified"
        assert os.path.exists(user_dir), "User dir does not exists"

        self.user_dir = user_dir
        self.domains = {}
        self.user_name = os.path.basename(user_dir)

        self._load()

    def _load(self):
        domains_list = os.path.join(self.user_dir, 'domains.list')
        if os.path.exists(domains_list):
            for domain in file(domains_list):
                domain = domain.strip()
                self.domains[domain] = DirectAdminUserDomain(self, domain)

    def get_domains(self):
        return self.domains.values()