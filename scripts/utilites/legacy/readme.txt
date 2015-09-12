# RemiZOffAlex

mkdir /etc/blocks

Использование: log_parser.py [-h] [-o OUTFILE] [-p pid-file] [-B BLOCKPATH] -l
                     LOG_FILE -t {apache,nginx} [-D DATABASE]
                     [--limit LIMITREQUESTS] [-S]

Парсинг
./log_parser.py -l access.log-mini -t nginx --limit 10 -B "/etc/blocks"

В крон
Блокировка
* *   *   *   *   * /bin/bash /etc/blocks/block_*
Разблокировка
* *   *   *   *   * /bin/bash /etc/blocks/unblock_*
