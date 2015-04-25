#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
#	Парсинг журналов Apache и вывод статистики
#
# Requirements:
#	CentOS 6

import datetime, re, sys

if len(sys.argv) <= 1:
	print 'Использование:'
	print '\t[--nginx] - парсинг Nginx файла журналирования'
	sys.exit("Необходимы аргументы")

# Описание переменных
# Имя файла
logfile = ''
# Режим парсера
modeParse = 'apache'
# Паттерны парсера
patterns = ''
# Список исключённых IP
excludeip = ''

iplist = []
hostlist = []

"""
Аргументы командной строки
"""
if sys.argv[1] == '--nginx':
	modeParse = 'nginx'
	logfile = sys.argv[2]
else:
	logfile = sys.argv[1]

"""
Паттерны для парсинга
"""
if modeParse == 'apache':
	patterns = ['^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)', # IP remote
	'^\-', # -
	'^(\S+|"\S*")', # Remote user
	'^\[\S*\s\S*\]', # Dateime
	'^\"\S+[^\"]*\"', # , # Request
	'^(\S+|"\S*")', # Status
	'^(\d*|\S+|"\S*")', # URL
	'^\".[^\"]*\"'] # '"$http_user_agent"
elif modeParse == 'nginx':
	patterns = ['^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)', # IP remote
	'^\-', # -
	'^(\S+|"\S*")', # Remote user
	'^\[\S*\s\S*\]', # Dateime
	'^\"\S+[^\"]*\"', # Request
	'^(\S+|"\S*")', # Status
	'^(\S+|"\S*")', # Body bytes sent
	'^\"\S*"', # URL
	'^\".[^\"]*\"', # '"$http_user_agent"
	'^\"(-|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|:?(?:[0-9a-f]{1,4}:)*:?(?::?[0-9a-f]{1,4})*)\"'] # X-Forwarded-For

"""
Проверка на совпадение с RFC
"""
def isRFC(ip):
	result = False
	if ip == "127.0.0.1":
		result = True
	patterns = ["192\.168\.\d{1,3}\.\d{1,3}", "10\.\d{1,3}\.\d{1,3}\.\d{1,3}","172\.(3[01]|2[0-9]|1[6-9])"]
	for pattern in patterns:
		match = re.findall(pattern, ip)
		if match:
			result = True
	return result

"""
Прогресс бар
"""
def cli_progress_test(cur, max, bar_length=60):
	percent = cur / max
	hashes = '#' * int(round(percent * bar_length))
	spaces = ' ' * (bar_length - len(hashes))
	sys.stdout.write("\rСостояние: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
	sys.stdout.flush()

"""
Парсинг строки на элементы
"""
def get_log_value(line):
	result = []
	oldline = line
	for pattern in patterns:
		match = re.findall(pattern, line)
		if match:
			if type(match[0]) is str:
				line = line[len(match[0]):].strip()
				result.append(match[0])
			else:
				line = line[len(match[0][0]):].strip()
				result.append(match[0][0])
		else:
			# Вывод отладочной информации по ошибке
			print "Ошибка:"
			print oldline
			print line
			print pattern
	return result

"""
Получить штамп времени записи из лога
"""
def get_date(line):
	result = False
	match = re.findall('(\d+)\/([A-Za-z]+)\/(\d+)\:(\d+)\:(\d+)\:(\d+)', line)
	if match:
		result=datetime.datetime.strptime(str(match[0][2])+" "+match[0][1]+" "+str(match[0][0])+" "+str(match[0][3])+" "+str(match[0][4]), '%Y %b %d %H %M')
	return result

"""
Получить разницу во времени
"""
def get_time_diff(time1, time2):
	result = time1 - time2
	return result

"""
Вывод статистики
"""
def statistics():
	print()
	print("Всего уникальных IP: " + str(len(iplist)))
	for ip in iplist:
		print("IP: " + ip[0] + " обратился " + str(ip[1]) + " раз")

with open(logfile, 'r') as f:
	result = []
	i=0
	max=10000
	for line in f:
		line = line.replace("\n", "")
		stamp = get_date(line)
#		controltime = datetime.datetime.now()
#		if get_time_diff(controltime, stamp) < datetime.timedelta(minutes=60):
#			for pattern in patterns:
#				result.append(get_log_value(line))
		for pattern in patterns:
			ip=get_log_value(line)
			if not isRFC(ip):
				result.append(ip)
		if not stamp:
			sys.exit(0)
#		result.append(get_log_value(line))
		i = i + 1
		cli_progress_test(i, max)
		if i >= max:
			i=0
	# Подсчёт уникальных IP
	print()
	print("Stage II")
	i=0
	for line in result:
		flag = False
		for ip in iplist:
			if line[0] == ip[0]:
				ip[1] += 1
				flag = True
		if not flag:
			iplist.append([line[0], 1])
		i = i + 1
		cli_progress_test(i, max)
		if i >= max:
			i=0
	# Сортировка
	iplist.sort(key=lambda tup: tup[1])

statistics()
