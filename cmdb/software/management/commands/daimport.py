# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import os

from django.core.management.base import BaseCommand

from ipman.models import IPAddress, IPAddressPool, IPNetworkPool
from resources.models import Resource, ResourceOption
from software.models import DirectAdminLicense


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.description = 'Utility used to import DirectAdmin licenses from TSV file.'
        parser.add_argument('licenses-list',
                            help="File with tab separated list of DirectAdmin licenses (da_lic, da_ip, da_target, da_status).")

    def handle(self, *args, **options):
        da_licenses_list_file = options['licenses-list']

        if not os.path.exists(da_licenses_list_file):
            raise Exception("File must exist: %s" % da_licenses_list_file)

        # Read rec from da lic list
        # Check IP from the free DA license
        #    inuse: find new form the same IP pool, print notice
        # Create DA license in DA lic pool in state free/inuse
        # Move IP to DA IP pool (set ipman_pool_id)
        # Set DA lic target system (arch, distrib)
        for da_file_rec in file(da_licenses_list_file):
            print "-------"

            (da_lic, da_ip, da_target, da_status) = da_file_rec.split('\t')
            da_status = da_status.strip()

            print "Check LIC %s, IP %s (%s)" % (da_lic, da_ip, da_status)

            da_license, created = DirectAdminLicense.objects.get_or_create(directadmin_lid=da_lic)
            if not created and da_license.parent:
                continue

            ip_addresses = IPAddress.objects.active(address=da_ip)
            if len(ip_addresses) > 1:
                raise Exception('There are more than 1 IP: %s' % da_ip)
            elif len(ip_addresses) > 0:
                ip_address = ip_addresses[0]
            else:
                ip_pool = self._find_free_pool_for_ip(da_ip)
                if not ip_pool:
                    raise Exception('There is no IP pool for IP %s' % da_ip)

                ip_address, created = IPAddress.objects.get_or_create(
                    address=da_ip,
                    defaults=dict(
                        parent=ip_pool,
                        status=Resource.STATUS_LOCKED
                    ))

            if da_status == 'free':
                if not ip_address.is_free:
                    print '    IP %s is not free but DA license is free, rent new' % da_ip

                    ip_pool = Resource.objects.get(pk=ip_address.get_origin())

                    if ip_pool.usage > 98:
                        print "[!!!] IP pool %s is >98%% full. Find new pool." % ip_pool.id

                        free_ip_pools = IPNetworkPool.objects \
                            .active(parent=ip_pool.parent, status=Resource.STATUS_FREE) \
                            .exclude(pk=ip_pool.id)
                        ip_pool = free_ip_pools[0]

                    ip_address = ip_pool.available().next()
                    ip_address.lock()

                    print '[!]    update IP: %s -> %s' % (da_ip, ip_address)
                else:
                    print '    IP %s free and DA %s free, locking' % (da_ip, da_lic)
                    ip_address.lock()
            else:
                print '    license %s is used' % da_lic
                if ip_address.is_free:
                    print "[???] IP %s is free, but DA license is USED" % da_ip

            # find origin pool of the IP
            ip_pool = Resource.objects.get(pk=ip_address.get_origin())

            # find DA IP pool
            da_ip_pools = Resource.objects.active(parent=ip_pool.parent, daimport=1)
            if not da_ip_pools:
                raise Exception('No DA IP pool for IP %s' % da_ip)
            da_ip_pool = da_ip_pools[0]

            print "    FOUND DA IP POOL %s" % da_ip_pool.id

            # assign unused IPs to DirectAdmin IP Pool
            if not ip_address.is_used:
                ip_address.parent = da_ip_pool

            ip_address.set_origin(da_ip_pool.id)
            ip_address.save()

            # ES 6.0 64
            da_target = da_target.strip()
            print "    setting target %s" % da_target
            da_target_parts = da_target.split(' ')
            if len(da_target_parts) == 2:
                da_target_parts.append(32)

            da_license.set_option('directadmin_target', "%s %s" % (da_target_parts[0], da_target_parts[1]))
            da_license.set_option('directadmin_arch', int(da_target_parts[2]), ResourceOption.FORMAT_INT)

            # Update DA license
            da_license.parent = ip_address
            da_license.save()
            da_license.free() if da_status == 'free' else da_license.use()

            print "DA LIC %s s created with IP %s" % (da_license.lid, ip_address)

    def _find_free_pool_for_ip(self, ip_address):
        assert ip_address

        for ip_pool in Resource.objects.active(type__in=IPAddressPool.ip_pool_types,
                                               status=Resource.STATUS_FREE):
            if ip_pool.can_add(ip_address):
                return ip_pool

        return None
