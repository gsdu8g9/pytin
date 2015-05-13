Resources API
=============

1. Installation

    Add resources to INSTALLED_APPS

2. Overview

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


3. IP address pools

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

