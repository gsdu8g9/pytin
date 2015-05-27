#!/usr/bin/env bash

#-------------------------------
# Usage:
#   bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/cmdb/deploy/init.sh)
#-------------------------------

SOURCES=/root/cmdbdistr
echo "Prepare the sources in ${SOURCES}"
rm -rf ${SOURCES}
git clone https://github.com/servancho/pytin.git ${SOURCES}


# here must be loop on all registered apps

echo "*** Deploying targets ***"
APPNAME=cmdb
USERNAME=${APPNAME}
APPROOT=/apps/${APPNAME}
APP_SOURCES=${SOURCES}/${APPNAME}

echo "[${APPNAME}]"

if [ ! -d ${APP_SOURCES}/deploy ];
then
    echo "Missing config for app ${APPNAME} in ${APP_SOURCES}/deploy"
    exit 1
fi

echo "Install to: ${APPROOT} for user ${USERNAME}"
if [ ! -d ${APPROOT} ];
then
    mkdir -p ${APPROOT}
fi

OLD_ROOT=$(pwd)

echo "*** Run install script ***"
cd ${APP_SOURCES}
bash ./deploy/install.sh ${APPROOT} ${USERNAME}
echo "*** Done ***"

cd ${OLD_ROOT}

rm -rf ${SOURCES}

exit 0
