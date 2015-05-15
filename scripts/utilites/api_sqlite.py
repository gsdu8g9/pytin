#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# RemiZOffAlex
#
# Description:
# API SQLite

import sys
import traceback
import os
import sqlite3
import datetime

class DDoSSQLite:
    def __init__(self, filename):
        """
        Инициализация класса API для SQLite
        """
        self.filename = filename
        if os.path.exists(self.filename):
            os.remove(self.filename)
        self.connection = sqlite3.connect(self.filename)
        self.cursor = self.connection.cursor()
        self.cursor.execute('PRAGMA foreign_keys = ON;')
        self.cursor.execute('DROP TABLE IF EXISTS ip;')
        self.cursor.execute("""CREATE TABLE `ip` (
                `id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `ip`    TEXT NOT NULL UNIQUE
            );""")
        self.cursor.execute('DROP TABLE IF EXISTS domains;')
        self.cursor.execute("""CREATE TABLE `domains` (
                `id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `domain`    TEXT NOT NULL UNIQUE
            );""")
        self.cursor.execute('DROP TABLE IF EXISTS logs;')
        self.cursor.execute("""CREATE TABLE `logs` (
                `id`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `ip`    INTEGER NOT NULL,
                `domain`    INTEGER NOT NULL,
                `period`    TEXT NOT NULL,
                `count`     INTEGER,
                FOREIGN KEY(ip) REFERENCES ip(id),
                FOREIGN KEY(domain) REFERENCES domains(id)
            );""")

    def addIP(self, IP):
        """
        Добавить IP в БД
        """
        self.cursor.execute("SELECT * FROM ip WHERE ip = '" + IP + "';")
        if not self.cursor.fetchall():
            self.cursor.execute("INSERT INTO ip (id, ip) VALUES ( NULL, '" + IP + "' );")
            self.connection.commit()

    def addDomain(self, Domain):
        """
        Добавить домен в БД
        """
        self.cursor.execute("SELECT * FROM domains WHERE domain = '" + Domain + "';")
        if not self.cursor.fetchall():
            self.cursor.execute("INSERT INTO domains (id, domain) VALUES ( NULL, ? );", (Domain,) )
            self.connection.commit()

    def addLogLine(self, logdate, IP, Domain):
        """
        Добавить строку лога
        """
        self.addIP(IP)
        self.cursor.execute("SELECT * FROM ip WHERE ip = '" + IP + "';")
        ip = self.cursor.fetchone()
        self.addDomain(Domain)
        self.cursor.execute("SELECT * FROM domains WHERE domain = '" + Domain + "';")
        domain = self.cursor.fetchone()
        period = str(logdate.year) + " " + str(logdate.month) + " " + str(logdate.day) + " " + str(logdate.hour) + " " + str(logdate.minute-logdate.minute%10)
        self.cursor.execute("SELECT id, count FROM logs WHERE domain = " + str(domain[0]) + " AND ip = " + str(ip[0]) + " AND period = '" + period + "';")
        row = self.cursor.fetchone()
#        print row
        datetime.datetime.strptime(period, '%Y %m %d %H %M')
        if not row:
            self.cursor.execute("INSERT INTO logs (id, ip, domain, period, count) VALUES ( NULL, " + str(ip[0]) + ", " + str(domain[0]) + ", '" + period + "', 1 );")
        else:
            self.cursor.execute("UPDATE logs SET count = " + str(row[1]+1) + " WHERE id = " + str(row[0]) + ";")
        self.connection.commit()

    def __exit__(self):
        self.connection.close()
