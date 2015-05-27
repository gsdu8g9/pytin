The Pytin Project
=================

Pytin is the collection of a datacenter management utils, used internally in justhost.ru.

We just started to publish our sources. Several projects will be rewritten in Python (such as tasks,
port them to Celery), so the publishing process is not fast ;) 

Bash scripts are need to be refactored and documented to be useful outside justhost.ru.  


Repository structure
--------------------

### /cmdb ###

Configuration management database (CMDB)

Written in Python, easy to install and maintain. Used to track infrastructure resources like hardware,
IP addresses, network ports. Dynamic resources like connections and virtual servers.

#### Features ####

* Track of IP addresses usage (SNMP, MAC and ARP table dumps)
* Discover IPs used by servers and ability to query this info (find server and switch port by IP)
* Hypervisors discovery and add discovered VPS servers to it
* Export CMDB data to Zabbix, generate complex and graph screens
* Provides CLI interface and RESTful API for the integration

### /scripts ###

Various useful scripts and subsystems, used and maintained by our team. Part of it is used in our task
automation process.
