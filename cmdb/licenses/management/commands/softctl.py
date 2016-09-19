from __future__ import unicode_literals

from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from cmdb.settings import logger
from ipman.models import GlobalIPManager, IPAddressPoolFactory, IPAddressGeneric
from licenses.models import DirectAdminLicense
from resources.models import Resource


class Command(BaseCommand):
    registered_handlers = {}

    def add_arguments(self, parser):
        """
        Add custom arguments and subcommands
        """
        subparsers = parser.add_subparsers(title="IP management commands",
                                           help="Commands help",
                                           dest='manager_name',
                                           parser_class=ArgumentParser)

        # IP address commands
        da_import_parser = subparsers.add_parser('daimport', help='Import legacy DA licenses.')

        da_import_parser.add_argument('tsv-file',
                                      help="Path to the file with DirectAdmin license data (lic-ip-status).")
        da_import_parser.add_argument('cid', type=int, help="Client ID.")
        self._register_handler('daimport', self._handle_daimport)

        da_add_parser = subparsers.add_parser('daadd', help='Add DA license.')
        da_add_parser.add_argument('cid', type=int, help="Client ID.")
        da_add_parser.add_argument('lid', type=int, help="License ID.")
        da_add_parser.add_argument('ip', help="Linked IP address.")
        self._register_handler('daadd', self._handle_daadd)

    def handle(self, *args, **options):
        subcommand = options['manager_name']

        # call handler
        self.registered_handlers[subcommand](*args, **options)

    def _handle_daadd(self, *args, **options):
        cid = options['cid']
        lid = options['lid']
        ip = options['ip']

        license = DirectAdminLicense.register_license(cid=cid, lid=int(lid), ip_address=ip)
        logger.info(license)

    def _handle_daimport(self, *args, **options):
        cid = options['cid']

        da_pool = IPAddressPoolFactory.from_name(name="Imported DirectAdmin")

        with open(options['tsv-file']) as tsv_file:
            for line in tsv_file:
                line = line.strip()
                if line == '':
                    continue

                (lid_id, ipaddr, lic_status) = line.decode('utf-8').split(None, 3)
                logger.info("> Processing: %s %s %s" % (lid_id, ipaddr, lic_status))

                try:
                    ip_obj = GlobalIPManager.get_ip(ipaddr)
                except:
                    # TODO: refactor IP creation
                    ip_obj, created = IPAddressGeneric.objects.update_or_create(address=ipaddr, pool=da_pool)

                if lic_status == Resource.STATUS_FREE:
                    if ip_obj.status == Resource.STATUS_FREE:
                        license = DirectAdminLicense.register_license(pool=da_pool, cid=cid, lid=int(lid_id),
                                                                      ip_address=ip_obj)
                        license.free()
                        logger.info("LIC %s (%s). Added as FREE" % (lid_id, ipaddr))
                    else:
                        logger.warning("(!!) LIC %s (%s). You must change IP." % (lid_id, ipaddr))
                else:
                    if ip_obj.status == Resource.STATUS_FREE:
                        license = DirectAdminLicense.register_license(pool=da_pool, cid=cid, lid=int(lid_id),
                                                                      ip_address=ip_obj)
                        license.free()
                        logger.warning(
                            "(!) LIC %s (%s). Added as FREE (changed License status to FREE)" % (lid_id, ipaddr))
                    else:
                        license = DirectAdminLicense.register_license(pool=da_pool, cid=cid, lid=int(lid_id),
                                                                      ip_address=ip_obj)
                        license.use()
                        logger.info("LIC %s (%s). Added as USED." % (lid_id, ipaddr))

    def _register_handler(self, command_name, handler):
        assert command_name, "command_name must be defined."
        assert handler, "handler must be defined."

        self.registered_handlers[command_name] = handler
