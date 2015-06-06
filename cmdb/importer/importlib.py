from assets.models import SwitchPort, PortConnection, ServerPort, Server, VirtualServer
from cmdb.settings import logger
from ipman.models import IPAddress, IPAddressPool
from resources.models import Resource


def _get_or_create_object(klass, query, creational=None):
    """
    Find or return object using query for search, then create object with creational attributes
    :param klass:
    :param kwargs:
    :param creational:
    :return:
    """

    if not creational:
        creational = query

    created = False
    found_objects = klass.objects.active(**query)
    if len(found_objects) <= 0:
        ret_object = klass.create(**creational)
        created = True
    else:
        ret_object = found_objects[0]
        ret_object.touch()  # update last_seen date

        if len(found_objects) > 1:
            logger.error("Duplicate objects %s for the query: %s" % (klass.__name__, query))

    return ret_object, created


class CmdbImporter(object):
    def __init__(self):
        self.available_ip_pools = IPAddressPool.get_all_pools()

    def import_switch(self, switch_cmdb_id, l3switch):
        """
        Import data from layer 3 switch
        :param l3switch: L3Switch
        """

        source_switch = Resource.objects.get(pk=switch_cmdb_id)
        for l3port in l3switch.ports:
            if l3port.is_local:
                self._import_switch_local_port(source_switch, l3port)
            else:
                self._import_switch_aggregate_port(source_switch, l3port)

    def _import_switch_local_port(self, source_switch, l3port):
        assert l3port
        assert source_switch

        switch_local_port, created = _get_or_create_object(SwitchPort,
                                                           dict(number=l3port.number, parent=source_switch))
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

        hypervisor_server = self._find_hypervisor(l3port)

        for connected_mac in l3port.macs:
            server_port, created = _get_or_create_object(ServerPort, dict(mac=connected_mac.interface))
            if created:
                logger.info("Added server port %s (%s)" % (server_port.id, connected_mac.interface))

                if not connected_mac.vendor or hypervisor_server:
                    server = VirtualServer.create(label='VPS', parent=hypervisor_server)
                    logger.info("Added VPS i-%d %s (%s) on local port %s" % (
                        server.id, server, connected_mac, l3port.number))
                    if hypervisor_server:
                        logger.info("    with parent hypervisor i-%s" % hypervisor_server.id)
                else:
                    server = Server.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
                    logger.info("Added metal server i-%d %s (%s) on local port %s" % (
                        server.id, server, connected_mac, l3port.number))

                # set parent for the port
                server_port.parent = server
                server_port.save()
            else:
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

                    # set role
                    hypervisor_server.set_option('guessed_role', 'hypervisor')

                    # update server type
                    server_port.parent.type = VirtualServer.__class__.__name__
                    server_port.parent.save()

                if not hypervisor_server:
                    if isinstance(server_port.parent.as_leaf_class(), Server):
                        server_port.parent.parent = None
                        server_port.parent.as_leaf_class().save()
                        logger.warning("Parent of server %s was cleared." % server_port.parent.as_leaf_class())

                if connected_mac.vendor and server_port.parent:
                    if server_port.parent.name == 'Server':
                        # update standard server name to platform name
                        server_port.parent.name = connected_mac.vendor
                        server_port.parent.save()

                server_port.touch()
                server_port.parent.touch()

            # add PortConnection only to local ports
            port_connection, created = _get_or_create_object(PortConnection,
                                                             dict(parent=switch_local_port,
                                                                  linked_port_id=server_port.id))
            if created:
                logger.info("Added %d Mbit connection: %d <-> %d" % (
                    port_connection.link_speed_mbit, switch_local_port.id, server_port.id))
            else:
                port_connection.touch()

            port_connection.use()

            # adding IP
            for ip_address in l3port.switch.get_mac_ips(str(connected_mac)):
                self._add_ip(ip_address, parent=server_port)

    def _import_switch_aggregate_port(self, source_switch, l3port):
        assert l3port
        assert source_switch

        for connected_mac in l3port.macs:
            server_port, created = _get_or_create_object(ServerPort, dict(mac=connected_mac.interface))
            if created:
                logger.info("Added server port %s (%s)" % (server_port.id, connected_mac.interface))

                if not connected_mac.vendor:
                    server = VirtualServer.create(label='VPS')
                    logger.info("Added VPS i-%d %s (%s)" % (server.id, server, connected_mac))
                else:
                    server = Server.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
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

            # adding IP
            for ip_address in l3port.switch.get_mac_ips(str(connected_mac)):
                self._add_ip(ip_address, parent=server_port)

    def _find_hypervisor(self, l3port):
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
                server_port, created = _get_or_create_object(ServerPort, dict(mac=connected_mac.interface))
                if created:
                    phyz_server = Server.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
                    server_port.parent = phyz_server
                    server_port.save()
                    phyz_server_list.append(phyz_server)
                else:
                    phyz_server_list.append(server_port.parent)

        phyz_server = None
        if len(phyz_server_list) > 1:
            logger.warning("Possibly UPLINK port: %s (phyz servers %s, MAC count on port %s)" % (
                l3port.number, len(phyz_server_list), len(l3port.macs)))
        elif len(phyz_server_list) == 1 and len(l3port.macs) > 1:
            # one phyz and many VPS on port - hypervisor detected
            phyz_server = phyz_server_list[0]
            logger.info('Possible Hypervisor detected: %s' % phyz_server)

        return phyz_server

    def _add_ip(self, ip_address, parent=None):
        assert ip_address, "ip_address must be defined."

        added = False
        for ip_pool in self.available_ip_pools:
            if ip_pool.can_add(ip_address):
                added_ip, created = _get_or_create_object(IPAddress,
                                                          dict(address__exact=ip_address),
                                                          dict(address=ip_address, parent=ip_pool))
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
