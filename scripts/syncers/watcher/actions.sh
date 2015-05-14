#!/bin/bash

# Check runlevel if necessary
# RUNLEVEL=$(/sbin/runlevel)
# if [[ "$RUNLEVEL" == "N 0" ]] # system shutdown
# then
#     echo "Skip proxy"
#     exit 100
# fi

# Define some actions to run
WORK_DIR=$(pwd)
LOG_FILE=${WORK_DIR}/proxy-cmd.log

function logAction {
    echo $(date +"%d.%m.%Y %H:%M:%S") $1 >> ${LOG_FILE}
}


### Define actions here ###
logAction 'Running cmd'
