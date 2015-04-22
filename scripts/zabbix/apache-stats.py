#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# RemiZOffAlex
#
# Description:
#	Скрипт получения информации server-status из Apache
#
# Requirements:
#	Python 3

import urllib.request as url
import os, sys

urladdress=sys.argv[1] + '?auto'
username = 'USERNAME'
password = 'PASSWORD'
realm = 'REALM'

auth_handler = url.HTTPBasicAuthHandler()
auth_handler.add_password(realm=realm,
	uri=urladdress,
	user=username,
	passwd=password)
opener = url.build_opener(auth_handler)
url.install_opener(opener)

#'http://localhost:8080/server-status?auto'

def GetValue():
	result=''
	with url.urlopen(urladdress) as urlstream:
		html=urlstream.read()
	for line in html.decode('utf-8').split("\n"):
		value = line.split(":")
		if sys.argv[2] == "Scoreboard":
			if value[0] == "Scoreboard":
				result = len(value[1].strip())
				return result
		else:
			if value[0] == sys.argv[2]:
				result=value[1].strip()
				return result

print(GetValue())
