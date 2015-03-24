#!/bin/sh -

# RemiZOffAlex
#
# Description:
#	Скрипт загрузки таблицы чёрного списка заблокированных IP
#
# Requirements:
#	FreeBSD

PATH=/etc:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/home/user

silent=1
if [ ${silent} != 1 ]
then
	echo "Скрипт интерактивного добавления IP или подсети в бан лист файервола"

	echo "Установка переменных"
fi
table=${table:="2"}
filename=${filename:="/etc/badguys.list"}
tmpfile=`mktemp /tmp/badguys.XXX`
tmpdialog=`mktemp /tmp/dialog.XXX`
DIALOG=${DIALOG:=/usr/bin/dialog}

reload() {
	if [ ${silent} != 1 ]
	then
		echo
		echo "Очистка таблицы файервола"
	fi
	ipfw table ${table} flush

sort_list

	echo "Загрузка списка IP в таблицу файервола"
	for i1 in `cat ${filename}`;
	do
		ipfw table ${table} add $i1
	done
}

# Сортировка списка IP адресов
sort_list() {
	echo "Сортировка списка IP адресов"
	sort -n ${filename} > ${tmpfile}
	uniq ${tmpfile} ${filename}
}

# Показ списка IP адресов
print_list() {
	if [ -n "$2" ]; then
		less ${filename}
	else
		grep $2 ${filename}
	fi
}

print_help() {
	echo
	case $2 in
	add)
		echo "Без параметров вызывает диалоговое окно добавления"
		echo "Параметр после add добавляется в файл и таблица перезагружается"
	;;
	*)
		echo "add - добавление нового IP"
		echo "delete - удаление файла"
		echo "clear - очистка таблицы"
		echo "help - помощь"
		echo "list - показать бан лист"
		echo "sort - сортировка списка"
	;;
	esac
}

case $1 in
add)
	isip=`echo $2 | grep -E -o '[0-9]{1,3}(\.[0-9]{1,3}){3}'`
	if [ ${isip} != "" ]
	then
		echo ${isip} >> ${filename}
		reload
	else
		${DIALOG} --inputbox "Добавить новый IP или подсеть" 10 40 2> ${tmpdialog}
		ip=`cat ${tmpdialog}`
		echo ${ip} >> ${filename}
		reload
	fi
;;
check)
	isip=`echo $2 | grep -E -o '[0-9]{1,3}(\.[0-9]{1,3}){3}'`
	if [ ${isip} != "" ]
	then
		geoiplookup ${isip}
	else
		while read LINE
		do
			isip=`echo $LINE | grep -E -o '[0-9]{1,3}(\.[0-9]{1,3}){3}'`
			if [ ${isip} != "" ]
			then
				echo ${LINE}" is "`geoiplookup ${isip}`
			fi
		done
	fi
;;
clear)
	ipfw table ${table} flush
;;
delete)
	rm -rf ${filename}
;;
help)
	print_help $2
;;
list)
	print_list
;;
sort)
	sort_list
;;
*)
	reload
	print_help
;;
esac

rm -rf ${tmpdialog}
rm -rf ${tmpfile}
