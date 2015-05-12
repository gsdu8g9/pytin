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
    Resource.has_option()


Resource.can_add(resource)
    Method is overrided in a relative classes to check is specific resource can be added as a child.

