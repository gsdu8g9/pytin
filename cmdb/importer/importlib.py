from __future__ import unicode_literals

from assets.models import SwitchPort, PortConnection, ServerPort, Server, VirtualServer, VirtualServerPort
from cmdb.settings import logger
from ipman.models import IPAddress, IPAddressPool
from resources.models import Resource


class CmdbImporter(object):
    def __init__(self):
        self.available_ip_pools = IPAddressPool.get_all_pools()

    def import_switch(self, switch_cmdb_id, l3switch):
        """
        Import data from layer 3 switch
        :param l3switch: L3Switch
        """
        hypervisor_server = None
        source_switch = Resource.objects.get(pk=switch_cmdb_id)
        for l3port in l3switch.ports:

            if l3port.is_local:
                switch_local_port, created = SwitchPort.objects.active().get_or_create(
                    number=l3port.number,
                    parent=source_switch
                )
                if created:
                    logger.info("Added switch port: %s:%s (cmdbid:%s)" % (
                        source_switch.id, l3port.number, switch_local_port.id))
                elif switch_local_port.uplink:
                    logger.info("Port %s marked as UPLINK, purge port connections" % switch_local_port)
                    PortConnection.objects.active(parent=switch_local_port).delete()
                    return

                if len(l3port.macs) > 0:
                    switch_local_port.use()
                    logger.debug("Switch port %s marked used" % switch_local_port)
                else:
                    logger.debug("Switch port %s marked free" % switch_local_port)
                    switch_local_port.free()

                # hvisor
                hypervisor_server = self._find_hypervisor(l3port)

            for connected_mac in l3port.macs:
                server, server_port = self._add_server_and_port(connected_mac)

                if l3port.is_local:
                    port_connection, created = PortConnection.objects.active().get_or_create(
                        parent=switch_local_port,
                        linked_port_id=server_port.id
                    )
                    if created:
                        logger.info("Added %d Mbit connection: %d <-> %d" % (
                            port_connection.link_speed_mbit, switch_local_port.id, server_port.id))
                    else:
                        port_connection.touch()

                    port_connection.use()

                    # existing VPS port on local switch port and with existing physical server
                    # then update parent of the VPS (link to physical server)
                    if hypervisor_server and hypervisor_server.id != server_port.parent.id:
                        if not server_port.parent.parent:
                            server_port.parent.parent = hypervisor_server
                            logger.info("Vps i-%s linked to parent metal server i-%s" % (
                                server_port.parent.id, hypervisor_server.id))
                        elif server_port.parent.parent.id != hypervisor_server.id:
                            old_parent_id = server_port.parent.parent.id
                            server_port.parent.parent = hypervisor_server
                            logger.info("Vps i-%s moved from i-%s to parent metal server i-%s" % (
                                server_port.parent.id, old_parent_id, hypervisor_server.id))

                        # update server type
                        server_port.parent.cast_type(VirtualServer)
                        server_port.parent.save()

                        # update server port type
                        server_port.cast_type(VirtualServerPort)

                # adding IP
                for ip_address in l3port.switch.get_mac_ips(str(connected_mac)):
                    self._add_ip(ip_address, parent=server_port)

    def _add_server_and_port(self, connected_mac):
        assert connected_mac

        logger.debug("Add mac: %s" % connected_mac)

        server_port, created = Resource.objects.active().get_or_create(
            mac=connected_mac.interface,
            type__in=[ServerPort.__name__, VirtualServerPort.__name__],
            defaults={
                'mac': connected_mac.interface,
                'type': "assets.%s" % (ServerPort.__name__ if connected_mac.vendor else VirtualServerPort.__name__)
            }
        )
        if created:
            logger.info("Added server port %s (%s)" % (server_port.id, connected_mac.interface))

            if server_port.__class__ == VirtualServerPort:
                server = VirtualServer.objects.create(label='VPS')
                logger.info("Added VPS i-%d %s (%s)" % (server.id, server, connected_mac))
            else:
                server = Server.objects.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
                logger.info("Added metal server i-%d %s (%s)" % (server.id, server, connected_mac))

            # set parent for the port
            server_port.parent = server
            server_port.save()
        else:
            if connected_mac.vendor and server_port.parent:
                if server_port.parent.name == 'Server':
                    # update standard server name to platform name
                    server_port.parent.name = connected_mac.vendor
                    server_port.parent.save()

            server_port.touch()
            server_port.parent.touch()

            if server_port.parent.__class__ == VirtualServer:
                server_port = server_port.cast_type(VirtualServerPort)

        return server_port.parent.as_leaf_class(), server_port

    def _find_hypervisor(self, l3port):
        assert l3port

        if len(l3port.macs) <= 0:
            return None

        # search for known guessed_role hypervisors
        for connected_mac in l3port.macs:
            for port in ServerPort.objects.active(mac=str(connected_mac)):
                if port.parent and port.parent.get_option_value('guessed_role') == 'hypervisor':
                    return port.parent

        # Try to identify hypervisor by mac:
        # one phyz server and many VPS - phyz server is a hypervisor
        # many phyz - possibly aggregated port, no hypervisors
        # one phyz and one mac in list - not a hypervisor
        phyz_server_list = []
        for connected_mac in l3port.macs:

            if connected_mac.vendor:
                phyz_server, server_port = self._add_server_and_port(connected_mac)
                phyz_server_list.append(phyz_server)

        phyz_server = None
        if len(phyz_server_list) > 1:
            logger.warning("Possibly UPLINK port: %s (phyz servers %s, MAC count on port %s)" % (
                l3port.number, len(phyz_server_list), len(l3port.macs)))
        elif len(phyz_server_list) == 1 and len(l3port.macs) > 1:
            # one phyz and many VPS on port - hypervisor detected
            phyz_server = phyz_server_list[0]
            logger.info('* Hypervisor detected: %s' % phyz_server)

            # set role
            phyz_server.set_option('guessed_role', 'hypervisor')

        return phyz_server

    def _add_ip(self, ip_address, parent=None):
        assert ip_address, "ip_address must be defined."

        added = False
        for ip_pool in self.available_ip_pools:
            if ip_pool.can_add(ip_address):
                added_ip, created = IPAddress.objects.active().get_or_create(address__exact=ip_address,
                                                                    defaults=dict(address=ip_address, parent=ip_pool))
                added_ip.use()

                if created:
                    logger.info("Added %s to %s" % (ip_address, ip_pool))
                else:
                    added_ip.touch()

                if parent:
                    if added_ip.parent and added_ip.parent.id != parent.id:
                        logger.info("IP %s moved from %s to %s" % (ip_address, added_ip.parent.as_leaf_class(), parent))

                    added_ip.parent = parent
                    added_ip.save()

                added = True
                break

        if not added:
            logger.warning("%s is not added. IP pool is not available." % ip_address)
