#!/usr/bin/env bash

if [ -z $1 ];
then
    echo "Where to install?"
    exit 1
fi

if [ -z $2 ];
then
    echo "Specify user?"
    exit 1
fi

SOURCES=$(pwd)
APPROOT=$1
USER=$2

APPNAME=${USER}
APPCONFIG=${SOURCES}/deploy
DJANGOROOT=${APPROOT}/djangoproj

if [ ! -d ${SOURCES}/deploy ];
then
    echo "Not in sources root?"
    exit 1
fi

echo "Create directories"
mkdir -p ${DJANGOROOT}          # ${APPROOT}/djangoproj
mkdir -p ${APPROOT}/web
mkdir -p ${APPROOT}/logs/uwsgi
mkdir -p ${APPROOT}/logs/web
mkdir -p ${APPROOT}/logs/app
mkdir -p ${APPROOT}/run
mkdir -p ${APPROOT}/db

echo "Cleanup"
rm -rf ${DJANGOROOT}/*
rm -rf ${APPROOT}/web/*

echo "Placing files..."

echo "Deploy Django Project"
cp -r ${SOURCES}/*  ${DJANGOROOT}/
rm -rf ${DJANGOROOT}/deploy

echo "Deploy Django config"
cp -f ${APPCONFIG}/settings.distr.py ${DJANGOROOT}/${APPNAME}/

echo "    create backlinks"
ln -s ${APPROOT}/logs ${DJANGOROOT}/

echo "Setting file righs"
chmod ug=rwX ${APPROOT}
chown -R ${USER}:${USER} ${APPROOT}

cd ${DJANGOROOT}
python2.7 manage.py makemigrations
python2.7 manage.py migrate

echo "DONE Deployment to ${APPROOT} for ${APPNAME} (${USER})"