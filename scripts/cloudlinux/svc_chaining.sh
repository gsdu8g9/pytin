#!/bin/bash

start_priority=30
shutdown_priority=90
initd_script_order=(nfs netfs lve lve_namespaces lvectl lvestats cagefs)

function update_prio() {
    if [ -z $1 ]
    then
        echo "Svc name?"
        exit 1
    fi

    if [ -z $2 ]
    then
        echo "Startup prio?"
        exit 1
    fi

    if [ -z $3 ]
    then
        echo "Shutdown prio?"
        exit 1
    fi

	initd_script=/etc/init.d/$1
	if [ ! -f ${initd_script} ]
	then
	    echo ${initd_script} "not found"
	    exit 1
	fi

    echo "* " ${initd_script}
	echo "set start priority: " $2
	echo "set shutdown priority: " $3

    perl -pi -e 's/#\s+chkconfig:\s+([\d-]+)\s+(\d+)\s*(\d*)/# chkconfig: $1 '$2' '$3'/g' ${initd_script}
    chkconfig $1 resetpriorities
}

# predefined
update_prio 'network' 10 90
update_prio 'apf' 11 90


# dynamic
new_start_priority=${start_priority}
new_shutdown_priority=${shutdown_priority}
for item in ${initd_script_order[*]}
do

	new_start_priority=$(( ++new_start_priority ))
	new_shutdown_priority=$(( --new_shutdown_priority ))

	cp -f ${initd_script} /root/initdbkp.$(date +"%s")
	update_prio ${item} ${new_start_priority} ${new_shutdown_priority}
done
