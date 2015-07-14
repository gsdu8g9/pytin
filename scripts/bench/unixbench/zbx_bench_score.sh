#!/usr/bin/env bash

#
# Run unix bench test and return UnixBench Score
#

ub_path=/usr/local/unixbench

cd ${ub_path}

./Run > results.txt

SCORE=$(perl -lne '/System Benchmarks Index Score[ ]+([\d\.]+)/ and print $1' results.txt)

zabbix_sender -z zabbix.justhost.ru -s $(hostname) -k unixbench.score -o ${SCORE}
