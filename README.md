pytin
=======

Pytin is the collection of a datacenter management utils, used internally in justhost.ru.

We just started to publish our sources. Several projects will be rewritten in Python (such as tasks,
port them to Celery), so the publishing process is not fast ;) 

Bash scripts are need to be refactored and documented to be useful outside justhost.ru.  


Repository structure
--------

### /cmdb ###

Content management database (CMDB)

Written in Python, easy to install and maintain. Used to track infrastructure resources like hardware,
IP addresses, network ports. Dynamic resources like connections and virtual servers.

CMDB is capable of tracking IP address usage by SNMP-monitoring, export hosts to Zabbix, generate complex
graph screens in Zabbix based on CMDB data.

Our CMDB provides CLI interface and RESTful API for the integration with our billing system.

Documentation will be available in Wiki, very soon.


### /scripts/directadmin ###

Scripts used to automate and extend DirectAdmin functionality.


### /scripts/incremental ###

There are scripts to create and handle incremental backups.

backup_in.sh is a wrapper for the gtar. Used to create incremental backups.

Notice the parameters ITERATIONS (default: 15) and KEEP_SEQUENCES (default: 1). This parameters are
used to define how increments are stored.

ITERATIONS used to define how often the full backup should be created. KEEP_SEQUENCES defines how
many full backups to keep in addition to full backup from the current backup sequence.

Example with ITERATIONS=5 and KEEP_SEQUENCES=1 (numbers are the increment indexes):
    
    1-full  2 3 4 5
    
    6-full  7 8 9 10
    
    11-full (1-5 removed) 12 13 14 15   
    
    16-full (6-10 removed) 17 18 19 20   
    
    21-full (11-15 removed) 22 23 24 25   
    
    26-full (16-20 removed) 27
                
    ------------------------------------> t

With this parameters we always have ITERATIONS * KEEP_SEQUENCES backups + number of backups
from the current backup sequence.

backup_files.sh wraps backup_inc.sh to backup all users from /home. It is recommended
to run this script on a backup node.

#### To create user backups ####

1. Incremental backups are stored here /backups/incremental

1. Add the following command to the daily Cron:
   /path/to/script/backup_users.sh /home /backups/incremental
   
1. Update exclude.list to ignore unnecessary files

For example, backups of the user user1 appears here: /backups/incremental/user1


#### To extract user backups ####

Open extract_user.sh script and change BACKUPS_ROOT and INCREMENT_COUNT for your specific installation.

Assume that we need the 10 days ago backup.

List all available increments and look up creation dates:

    $ ls -l /backups/incremental/user1/
    
You get output similar to this (with dates, sizes etc):

    $ user1-1.tar.gz
    $ user1-2.tar.gz
    $ user1-3.tar.gz
    $ user1-4.tar.gz
    $ user1-5.tar.gz
    $ user1-6.tar.gz
    $ user1-7.tar.gz
    
Notice the index of file for required date and execute:

    $ ./extract_user.sh -n user1 -t /home/user1.from.backup -c 5

All extracted files are available here: /home/user1.from.backup
