from assets.models import SwitchPort, PortConnection, ServerPort, Server, VirtualServer
from ipman.models import IPAddress, IPAddressPool


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

    def add_arp_record(self, source_switch, record):
        # add port and server
        self.add_mac_record(source_switch, record)

        # find port
        server_port, created = _get_or_create_object(ServerPort, dict(mac=record.mac))

        # add or update ip and assign it to port
        self.add_ip(record.ip, server_port)

    def add_mac_record(self, source_switch, record):
        assert source_switch, "source_switch must be defined."

        # create server port and server itself
        server_port, created = _get_or_create_object(ServerPort, dict(mac=record.mac))
        if not server_port.parent:
            # create server and port
            if record.vendor:
                server = Server.create(label='Server', vendor=record.vendor)
            else:
                server = VirtualServer.create(label='VPS')

            server_port.parent = server
            server_port.use()

        if not created:
            server_port.parent.touch()
            server_port.touch()

        # try add switch port and connection object
        try:
            # switch port
            if not record.port:
                raise ValueError()

            port_number = int(record.port)

            switch_port, created = _get_or_create_object(SwitchPort,
                                                         dict(number=port_number, parent=source_switch),
                                                         dict(number=port_number, parent=source_switch,
                                                              server_name=str(server_port.parent.as_leaf_class())))
            switch_port.use()

            if created:
                print "Added switch port: %d:%d" % (source_switch.id, port_number)

            if record.vendor:
                port_connection, created = _get_or_create_object(PortConnection,
                                                                 dict(port1=switch_port.id, port2=server_port.id),
                                                                 dict(port1=switch_port.id, port2=server_port.id,
                                                                      link_speed_mbit=1000,
                                                                      port1_device=str(source_switch),
                                                                      port2_device=str(server_port.parent)))
                port_connection.use()

                if created:
                    print "Added %d Mbit connection %d <-> %d" % (
                        port_connection.link_speed_mbit, switch_port.id, server_port.id)
                else:
                    port_connection.touch()

        except ValueError:
            print "Port %s has no direct connection to the device %d. Port: %s." % (
                record.mac, source_switch.id, record.port)

    def add_ip(self, ip_address, parent=None):
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
                    added_ip.parent = parent
                    added_ip.save()

                added = True
                break

        if not added:
            print "!!! IP %s is not added" % ip_address
