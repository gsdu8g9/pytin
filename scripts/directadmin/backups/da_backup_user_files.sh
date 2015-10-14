#!/bin/bash

# Incremental backup of DirectAdmin user files.
# Used scripts from /backup/incremental.
#

# Global config
USERDATA_PATH=

function usage {
	echo "Usage: da_backup_user_files.sh path_with_users path_with_backups"
	echo "       da_backup_user_files.sh /home /share/user_backups_incremental"
}

if [ -z $1 ]
then
    usage
    exit 1
fi

if [ -z $2 ]
then
    usage
    exit 1
fi

LOCK_FILE=/tmp/da_backup.lock
if [[ -f ${LOCK_FILE} ]]
then
    echo "! archive is in progress"
    exit 100
fi

trap "{ echo '!!! Clean up'; rm -f ${LOCK_FILE} ; exit 0; }" EXIT
echo "progress" > ${LOCK_FILE}


# target dir containing all the backups
USERDATA_PATH=$1
TARGET_BACKUPS_DIR=$2
SCRIPT_DIR=`dirname "$0"`
EXCLUDE_FILES=${SCRIPT_DIR}/exclude.list

echo "Data"
echo "	  script dir: ${SCRIPT_DIR}"
echo "    source: ${USERDATA_PATH}"
echo "    target: ${TARGET_BACKUPS_DIR}"
echo "	  exclude: ${EXCLUDE_FILES}"

PRE_PATH=`pwd`

cd ${SCRIPT_DIR}

for user in `ls ${USERDATA_PATH}`; do
{
	SOURCE_DIR=${USERDATA_PATH}/${user}

	mkdir -p ${TARGET_BACKUPS_DIR}/${user}
	./backup_inc.sh -i 15 -k 1 -x ${EXCLUDE_FILES} -t ${TARGET_BACKUPS_DIR}/${user} -n ${user} ${SOURCE_DIR}
}
done

cd ${PRE_PATH}
