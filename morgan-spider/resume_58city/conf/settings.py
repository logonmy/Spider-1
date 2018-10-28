#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: IntelliJ IDEA
@file: settings.py
@create at: 2018-08-30 18:27

这一行开始写关于本文件的说明与解释
"""

from MySQLdb import cursors


MYSQL_CONF = {
    'charset': 'utf8',
    'cursorclass': cursors.DictCursor,
    'host': 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'spider_admin',
    'passwd': 'n4UZknFH6F',
    'db': 'spider'
}

MYSQL_CONF_TEST = {
    'charset': 'utf8',
    'cursorclass': cursors.DictCursor,
    'host': '10.0.3.52',
    'port': 3306,
    'user': 'bi_admin',
    'passwd': 'bi_admin#@1mofanghr',
    'db': 'spider_search'
}

REDIS_CONF = {
    'host': '172.16.25.36',
    'port': '6379',
    'db': 0,
    'password': ''
}

