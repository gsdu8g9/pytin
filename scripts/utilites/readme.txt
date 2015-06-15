# RemiZOffAlex

mkdir /etc/blocks

Парсинг
./log_parser.py -l access.log-mini -t nginx --limit 10 -B "/etc/blocks"

В крон
Блокировка
* *   *   *   *   * /bin/bash /etc/blocks/block_*
Разблокировка
* *   *   *   *   * /bin/bash /etc/blocks/unblock_*
