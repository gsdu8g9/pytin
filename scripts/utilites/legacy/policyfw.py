#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

def main():
    parser = argparse.ArgumentParser(description='Скрипт добавления IP или подсети в блокировку на межсетевом экране',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-D", "--database", dest="database", help="Файл базы данных")


if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
