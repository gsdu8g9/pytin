from assets.models import SwitchPort, PortConnection, ServerPort, Server, VirtualServer
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
            print "ERROR: duplicate objects %s for the query: %s" % (klass.__name__, query)

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
            print "Added switch port: %s:%s (cmdbid:%s)" % (
                source_switch.id, l3port.number, switch_local_port.id)
        elif switch_local_port.uplink:
            print "Port %s marked as UPLINK, purge port connections" % switch_local_port
            PortConnection.objects.active(parent=switch_local_port).delete(purge=True)

        hypervisor_server = self._find_hypervisor(l3port.macs)

        for connected_mac in l3port.macs:
            server_port, created = _get_or_create_object(ServerPort, dict(mac=connected_mac.interface))
            if created:
                print "Added server port %s (%s)" % (server_port.id, connected_mac.interface)

                if not connected_mac.vendor or hypervisor_server:
                    server = VirtualServer.create(label='VPS', parent=hypervisor_server)
                    print "Added VPS i-%d %s (%s) on local port %s" % (
                        server.id, server, connected_mac, l3port.number)
                    if hypervisor_server:
                        print "    with parent hypervisor i-%s" % hypervisor_server.id
                else:
                    server = Server.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
                    print "Added metal server i-%d %s (%s) on local port %s" % (
                        server.id, server, connected_mac, l3port.number)

                # set parent for the port
                server_port.parent = server
                server_port.save()
            else:
                # existing VPS port on local switch port and with existing physical server
                # then update parent of the VPS (link to physical server)
                if hypervisor_server and hypervisor_server.id != server_port.parent.id:
                    if not server_port.parent.parent:
                        server_port.parent.parent = hypervisor_server
                        print "Vps i-%s linked to parent metal server i-%s" % (
                            server_port.parent.id, hypervisor_server.id)
                    elif server_port.parent.parent.id != hypervisor_server.id:
                        old_parent_id = server_port.parent.parent.id
                        server_port.parent.parent = hypervisor_server
                        print "Vps i-%s moved from i-%s to parent metal server i-%s" % (
                            server_port.parent.id, old_parent_id, hypervisor_server.id)

                    # set role
                    hypervisor_server.set_option('guessed_role', 'hypervisor')

                    # update server type
                    server_port.parent.type = VirtualServer.__class__.__name__
                    server_port.parent.save()
                elif connected_mac.vendor and server_port.parent:
                    if server_port.parent.name == 'Server':
                        # update standard server name to platform name
                        server_port.parent.name = connected_mac.vendor
                        server_port.parent.save()

                server_port.touch()

            # add PortConnection only to local ports
            port_connection, created = _get_or_create_object(PortConnection,
                                                             dict(parent=switch_local_port,
                                                                  linked_port_id=server_port.id))
            if created:
                print "Added %d Mbit connection: %d <-> %d" % (
                    port_connection.link_speed_mbit, switch_local_port.id, server_port.id)

                if self._detect_uplink_local_port(switch_local_port):
                    print "NOTE: Possibly UPLINK port: %s" % switch_local_port
            else:
                port_connection.touch()

            port_connection.use()

            # adding IP
            for ip_address in l3port.switch.get_mac_ips(str(connected_mac)):
                self._add_ip(ip_address, parent=server_port)

    def _detect_uplink_local_port(self, switch_local_port):
        assert switch_local_port

        connections = PortConnection.objects.active(parent=switch_local_port)
        if len(connections) > 2:
            phyz = 0
            for connection in connections:
                server_port = ServerPort.objects.get(pk=connection.linked_port_id)
                if server_port.parent.type == Server.__name__:
                    phyz += 1

            if phyz > 1:
                return True

        return False

    def _import_switch_aggregate_port(self, source_switch, l3port):
        assert l3port
        assert source_switch

        for connected_mac in l3port.macs:
            server_port, created = _get_or_create_object(ServerPort, dict(mac=connected_mac.interface))
            if created:
                print "Added server port %s (%s)" % (server_port.id, connected_mac.interface)

                if not connected_mac.vendor:
                    server = VirtualServer.create(label='VPS')
                    print "Added VPS i-%d %s (%s)" % (server.id, server, connected_mac)
                else:
                    server = Server.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
                    print "Added metal server i-%d %s (%s)" % (server.id, server, connected_mac)

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

            # adding IP
            for ip_address in l3port.switch.get_mac_ips(str(connected_mac)):
                self._add_ip(ip_address, parent=server_port)

    def _find_hypervisor(self, mac_list):
        if len(mac_list) <= 0:
            return None

        # search for known guessed_role
        for connected_mac in mac_list:
            for port in ServerPort.objects.active(mac=str(connected_mac)):
                if port.parent and port.parent.get_option_value('guessed_role') == 'hypervisor':
                    return port.parent

        # try to identify hypervisor by mac
        phyz_server = None
        for connected_mac in mac_list:
            if connected_mac.vendor:
                if phyz_server:
                    # if more then one physical server on port, return None
                    # possibly L2 switching
                    return None

                server_port, created = _get_or_create_object(ServerPort, dict(mac=connected_mac.interface))

                if created:
                    phyz_server = Server.create(label=connected_mac.vendor, vendor=connected_mac.vendor)
                    server_port.parent = phyz_server
                    server_port.save()
                else:
                    phyz_server = server_port.parent

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
                    print "Added %s to %s" % (ip_address, ip_pool)
                else:
                    added_ip.touch()

                if parent:
                    if added_ip.parent and added_ip.parent.id != parent.id:
                        print "IP %s moved from %s to %s" % (ip_address, added_ip.parent.as_leaf_class(), parent)

                    added_ip.parent = parent
                    added_ip.save()

                added = True
                break

        if not added:
            print "WARNING: %s is not added. IP pool is not available." % ip_address
