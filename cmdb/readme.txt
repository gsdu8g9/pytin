Resources API
=============

1. Installation
---------------

    Add app to INSTALLED_APPS

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


    Example:

        Search for all resources.
            Resource.objects.filter(status__in=[free, inuse], someopt__contains='value', someopt2='exactval')

        Search ONLY for IPAddress resources
            IPAddress.objects.filter(status__in=[free, inuse], someopt__contains='value', someopt2='exactval')

        All returned objects are of the specific Proxy model types:
            result = Resource.objects.filter(status__in=[free, inuse])
            The result may contain: [IPAddress, Resource, ResourcePool,...]


3. IP address pools
-------------------

    IPAddressPool
        List of IP addresses. Addresses can be from different networks. This type of pool is used to
        group some well known IPs, to not use them out there.

    IPAddressRangePool
        Pool formed from IP range, such as 192.168.1.1-192.168.1.10. Can only contain IPs from this range.

    IPNetworkPool
        Pool formed from IP network, such as 192.168.1.1/23. Can only contain IPs from this network.

    Extra parameters
        netmask: network mask for the IPs in the pool
        prefixlen: CIDR prefix (can be omitted)
        gateway: gateway for the IPs in the pool

    IP address is hard linked to its pool by using option field ipman_pool_id. Parent_id is used to
    store the hierarchy of the resources.


4. Assets
---------

    RegionResource
    PortConnection
    SwitchPort
    ServerPort
    Switch
    GatewaySwitch

    InventoryResource
        Physical resource, that have serial number to track it.
        Such is server, rack, network card, etc.

    Server
    VirtualServer

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
    python manage.py cmdbimport fromfile --arpdump /path/to/file/arp-table.txt
