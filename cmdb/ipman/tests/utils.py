from __future__ import unicode_literals

from ipman.models import IPAddressGeneric


def fill_ip_pool(ip_pool, c_size=25, d_size=100, prefix='46.17.'):
    for class_c in range(1, c_size):
        for class_d in range(1, d_size):
            ipv4 = "%s%s.%s" % (prefix, class_c, class_d)
            IPAddressGeneric.objects.update_or_create(
                address=ipv4,
                pool=ip_pool)
