JustHost.ru CMDB
================

Configuration management database (CMDB)

Written in Python, easy to install and maintain. Used to track infrastructure resources like hardware,
IP addresses, network ports. Dynamic resources like connections and virtual servers.

Features
* Tracking of IP addresses usage (using SNMP, MAC and ARP table dumps)
* Discover IPs used by servers and ability to query this info (find server and switch port by IP)
* Hypervisors discovery and keep track of VPSs form them
* Export CMDB data to Zabbix, generate complex and graph screens
* Provides CLI interface and RESTful API for the integration


1. Installation
---------------

    Run under root user:
    $ bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/cmdb/deploy/init.sh)

2. Overview
-----------

    Resources organized as a tree and have options (ResourceOptions) of the following formats:
        FORMAT_DICT = 'dict'        # Dictionary key-value pairs
        FORMAT_INT = 'int'          # Integer value
        FORMAT_FLOAT = 'float'      # Float value
        FORMAT_STRING = 'string'    # String value

    Resources have the following statuses:
        STATUS_FREE = 'free'
        STATUS_INUSE = 'inuse'
        STATUS_FAILED = 'failed'
        STATUS_LOCKED = 'locked'
        STATUS_DELETED = 'deleted'

    Basic resources API:
        Resource.set_option()
        Resource.get_option()
        Resource.get_options()
        Resource.has_option()

    Resource.can_add(resource)
        Method is overrided in a relative classes to check is specific resource can be added as a child.

2.1. Query resources
--------------------

    Resource.objects.filter(**kwargs)

    It supports all field lookups and methods, as described here:
    https://docs.djangoproject.com/en/1.7/ref/models/querysets/

    Resource.objects manager also supports search by options. Resource options can be specified in
    Resource.objects.filter() as a regular Resource fields. Field lookups are also supported.

    Resource.objects manager supports the shortcut Resource.objects.active(), that is equivalent for filter()
    but it ignores status=deleted resources.

    Standard query fields:
        parent, name, type, status, created_at, updated_at

    Example:

        Search for all resources.
            Resource.objects.filter(status__in=[free, inuse], someopt__contains='value', someopt2='exactval')

        Search ONLY for IPAddress resources
            IPAddress.objects.filter(status__in=[free, inuse], someopt__contains='value', someopt2='exactval')

        All returned objects are of the specific Proxy model types:
            result = Resource.objects.filter(status__in=[free, inuse])
            The result may contain: [IPAddress, Resource, ResourcePool,...]


3. IP address
-------------------

    Supported by module: ipman

    IPAddress
        query: address, version

    IPAddressPool
        List of IP addresses. Addresses can be from different networks. This type of pool is used to
        group some well known IPs, to not use them out there.

    IPAddressRangePool
        Pool formed from IP range, such as 192.168.1.1-192.168.1.10. Can only contain IPs from this range.
        query: range_from, range_to, version

    IPNetworkPool
        Pool formed from IP network, such as 192.168.1.1/23. Can only contain IPs from this network.
        query: network, version

        Extra query parameters
            netmask: network mask for the IPs in the pool
            prefixlen: CIDR prefix (can be omitted)
            gateway: gateway for the IPs in the pool

    IP address is hard linked to its pool by using option field ipman_pool_id. Parent_id is used to
    store the hierarchy of the resources.


    # List free IP pools
    $ cmdbctl list type=IPNetworkPool status=free

    # Get next available IPs from pools 3 and 4 (2 IPs from each pool)
    $ ipmanctl pool get 3 4 -c 2
    $ cmdbctl set <list_of_ids> --use


4. Assets
---------

    Supported by module: assets

    RegionResource
        query:

    PortConnection
        Connection between two ports. One port in parent, and the other in linked_port_id.
        query: link_speed_mbit, linked_port_id

    SwitchPort
        query: number

    ServerPort
        query: number, mac

    Switch
        query: label, serial

    GatewaySwitch
        query: label, serial

    InventoryResource
        Physical resource, that have serial number to track it.
        Such is server, rack, network card, etc.
        query: label, serial

    Server
        query: label, serial

    VirtualServer
        query: label, serial


5. CMDB init script (example)
-----------------------------

    ### Adding region structure

    python manage.py cmdbctl add --type=assets.RegionResource name=Datacenter1
    python manage.py cmdbctl add --type=assets.RegionResource name=Datacenter2


    ### Create IP address pools

    # Datacenter1
    python manage.py ipmanctl pool addcidr 46.17.40.0/23
    python manage.py ipmanctl pool addcidr 2a00:b700::/48

    # equivalent usage, but with ability to specify additional fields on create
    # python manage.py cmdbctl add --type=ipman.IPNetworkPool network=46.17.40.0/23 parent_id=19

    # Datacenter2
    python manage.py ipmanctl pool addcidr 46.17.46.0/23
    python manage.py ipmanctl pool addcidr 2a00:b700:1::/48

    # Assign parent values
    python manage.py cmdbctl set 1 2 3 4 5 6 7 8 -n=parent_id -v=<datacenter2_id>
    python manage.py cmdbctl set 9 10 11 12 13 14 15 -n=parent_id -v=<datacenter2_id>


    # Import ARP table data
    # python manage.py cmdbimport fromfile --arpdump /path/to/file/arp-table.txt <gateway_id> QSW8300.arp
    python manage.py cmdbimport snmp <gateway_id> QSW8300.arp <IP> <community string>

