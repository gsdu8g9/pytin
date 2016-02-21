# coding=utf-8
from __future__ import unicode_literals

from assets.analyzers import CmdbAnalyzer
from assets.models import SwitchPort, PortConnection, ServerPort, Server, VirtualServer, VirtualServerPort
from cmdb.settings import logger
from ipman.models import IPAddress, IPAddressPool
from resources.models import Resource


class GenericCmdbImporter(object):
    def __init__(self):
        self.available_ip_pools = IPAddressPool.get_all_pools()

    def import_switch(self, switch_cmdb_id, l3switch):
        """
        Import data from layer 3 switch
        :param l3switch: L3Switch
        """
        source_switch = Resource.active.get(pk=switch_cmdb_id)
        for l3port in l3switch.ports:
            if l3port.is_local:
                self._add_local_port(source_switch, l3port)
            else:
                self._add_foreign_port(l3port)

            # Import IP addresses
            for connected_mac in l3port.macs:
                server, server_port = self._add_server_and_port(connected_mac)

                for ip_address in l3port.switch.get_mac_ips(unicode(connected_mac)):
                    self._add_ip(ip_address, parent=server_port)

        # There is only one connection from the single server port.
        logger.info("Clean extra PortConnections from server ports")
        for server_port in ServerPort.active.filter():
            port_connections = PortConnection.active.filter(linked_port_id=server_port.id).order_by('-last_seen')

            if len(port_connections) > 1:
                logger.warning("Server port %s have >1 PortConnection" % server_port)
                deleted_poconn = 0
                for port_connection in port_connections[1:]:
                    logger.warning("    remove PortConnection %s" % port_connection)
                    port_connection.delete()
                    deleted_poconn += 1

                logger.warning("    deleted %s connections" % deleted_poconn)

    def process_virtual_servers(self, link_unresolved_to=None):
        """
        Find and link unresolved virtual servers to special group
        :return:
        """
        for vps_server in VirtualServer.active.all():
            if link_unresolved_to and not vps_server.parent:
                vps_server.parent = link_unresolved_to
                vps_server.save()
                logger.info("Virtual server %s linked to unresolveds group: %s" % (vps_server, vps_server.parent_id))

    def process_servers(self, link_unresolved_to=None):
        """
        Analyze server connections and automatically set server parent the same as linked switch parent,
        if server parent is None
        :return:
        """
        for server in Server.active.all():
            for server_port in ServerPort.active.filter(parent=server):
                switch_port = server_port.switch_port
                if not switch_port:
                    continue

                switch = switch_port.typed_parent
                rack = switch.typed_parent

                if switch.is_mounted:
                    server_parent_id = server.parent_id

                    if server.parent and server.parent.id != rack.id:
                        # clean parent unresolved group, to try to relink
                        server.parent = None

                    if not server.parent:
                        logger.info("Update server %s parent %s->%s" % (server, server_parent_id, switch.parent_id))

                        server.mount_to(rack)

            if link_unresolved_to and not server.parent:
                server.parent = link_unresolved_to
                server.save()
                logger.info("Server %s linked to unresolveds group: %s" % (server, server.parent_id))

    def process_hypervisors(self, switch_port):
        """
        Searching for the switch ports, where one physical and many VPS servers. If hypervisor found on port,
        then set its role and link VPS servers.
        :param switch_port:
        :param dry_run: If True, then role is set for guessed hypervisor (when 1 physical + many VMs).
        :return:
        """
        assert switch_port
        assert isinstance(switch_port, SwitchPort)

        result, pysical_srv, virtual_srv = CmdbAnalyzer.guess_hypervisor(switch_port)

        if result:
            logger.info("Found hypervisor: %s" % pysical_srv)
            pysical_srv.set_option('role', 'hypervisor')
            for virtual_server in virtual_srv:
                virtual_server.parent = pysical_srv
                virtual_server.save()
                logger.info("    virtual server %s is auto-linked to it" % virtual_server)
        else:
            logger.info("Switch port: %s" % switch_port)
            logger.info("  physicals: %s, virtuals: %s." % (len(pysical_srv), len(virtual_srv)))

            logger.info("Physical servers:")
            for server in pysical_srv:
                logger.info(unicode(server))

            logger.info("Virtual servers:")
            for vserver in virtual_srv:
                logger.info(unicode(vserver))

    def _add_foreign_port(self, l3port):
        """
        Add port and server from the foreign switch. It is possible that server is not directly connected to the
        switch and don't have local port.
        :param l3port: L3 port of the switch
        :return: None
        """
        assert l3port

        for connected_mac in l3port.macs:
            self._add_server_and_port(connected_mac)

    def _add_local_port(self, source_switch, l3port):
        """
        Add port and server from the local switch. Add switch port, server port, server and connection between
        switch port and server port.
        :param source_switch: Resource switch, which port is being added.
        :param l3port: L3 port of the switch
        :return: None
        """
        assert source_switch
        assert l3port

        switch_local_port, created = SwitchPort.active.get_or_create(
            number=l3port.number,
            parent=source_switch,
            defaults=dict(name=l3port.number, status=Resource.STATUS_INUSE)
        )
        if created:
            logger.info("Added switch port: %s:%s (cmdbid:%s)" % (
                source_switch.id, l3port.number, switch_local_port.id))
        elif switch_local_port.uplink:
            logger.info("Port %s marked as UPLINK, purge port connections" % switch_local_port)
            PortConnection.active.filter(parent=switch_local_port).delete()
            return switch_local_port

        if len(l3port.macs) > 0:
            switch_local_port.use()
            logger.info("Switch port %s marked used" % switch_local_port)
        else:
            switch_local_port.free()
            logger.info("Switch port %s marked free" % switch_local_port)

        for connected_mac in l3port.macs:
            server, server_port = self._add_server_and_port(connected_mac)

            port_connection, created = PortConnection.active.get_or_create(
                parent=switch_local_port,
                linked_port_id=server_port.id
            )
            if created:
                logger.info("Added %s" % port_connection)
            else:
                port_connection.touch()

            port_connection.use()

        return switch_local_port

    def _add_server_and_port(self, connected_mac):
        """
        Add or get server with port. Selecting bare metal or Virtual based on Vendor code of MAC.
        :param connected_mac:
        :return:
        """
        assert connected_mac

        logger.debug("Found mac: %s" % connected_mac)

        server_port, created = Resource.active.get_or_create(
            mac=connected_mac.interface,
            type__in=[ServerPort.__name__, VirtualServerPort.__name__],
            defaults=dict(
                mac=connected_mac.interface,
                type="assets.%s" % (ServerPort.__name__ if connected_mac.vendor else VirtualServerPort.__name__),
                status=Resource.STATUS_INUSE
            )
        )
        if created:
            logger.info("Added server port %s (%s)" % (server_port.id, connected_mac.interface))

            if server_port.__class__ == VirtualServerPort:
                server = VirtualServer.objects.create(label='VPS')
                logger.info("Added VPS %s (%s)" % (server, connected_mac))
            else:
                server = Server.objects.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
                logger.info("Added metal server %s (%s)" % (server, connected_mac))

            # set parent for the port
            server_port.parent = server
            server_port.save()
        else:
            server_port.use()
            server_port.touch()
            server_port.parent.touch()

        return server_port.typed_parent, server_port

    def _add_ip(self, ip_address, parent=None):
        assert ip_address, "ip_address must be defined."

        added = False
        for ip_pool in self.available_ip_pools:
            if ip_pool.can_add(ip_address):
                added_ip, created = IPAddress.active.get_or_create(address__exact=ip_address,
                                                                   defaults=dict(address=ip_address,
                                                                                 parent=ip_pool))
                added_ip.use(cascade=True)

                if created:
                    logger.info("Added %s to %s" % (ip_address, ip_pool))
                else:
                    added_ip.touch(cascade=True)

                if parent:
                    if added_ip.parent and added_ip.parent.id != parent.id:
                        logger.info("IP %s moved from %s to %s" % (ip_address, added_ip.typed_parent, parent))

                    added_ip.parent = parent
                    added_ip.save()

                added = True
                break

        if not added:
            logger.error("%s is not added. IP pool is not available." % ip_address)
