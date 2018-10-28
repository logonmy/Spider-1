#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: invalid_cookies.py
@create at: 2018-04-10 17:33

这一行开始写关于本文件的说明与解释
"""

from __future__ import print_function

import json
import pymysql
import requests
import traceback
import sys
import time

# 数据库权限描述： 读取autojob
MYSQL_CONF = {
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'host': 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'super_reader',
    'password': 'nMGZKQIXr4PE8aR2',
    'db': 'autojob'
}


def load_account(source):
    conn = pymysql.Connect(**MYSQL_CONF)
    cur = conn.cursor()
    try:
        print("开始加载%s帐号！" % source)
        sql = "select username, password from " \
              "`morgan-manager`.account WHERE " \
              "source='%s' and valid=1" % source
        cur.execute(sql)
        res = cur.fetchall()
        print("加载完成：总计%s个帐号" % len(res))
        return res

    except Exception as e:
        traceback.print_exc(e)
    finally:
        cur.close()
        conn.close()


def invalid(username, password, source):
    try:
        url = "http://172.16.25.41:8002/acc/invalidCookie.json?" \
              "userName=%s&password=%s&source=%s" % (username, password,
                                                     source)
        res = requests.get(url)
        if res.json().get('code') == 200:
            print("帐号失效成功: %s %s" % (username, password))
        else:
            print("帐号失效失败： %s "
                  % json.dumps(res.json(), ensure_ascii=False).encode('utf-8'))
    except Exception as e:
        traceback.print_exc(e)
        time.sleep(60)
        print("帐号失效异常： %s" % e)


def main(source):
    try:
        accounts = load_account(source)

        for item in accounts:
            username = item.get('username').encode('utf-8')
            password = item.get('password').encode('utf-8')
            invalid(username, password, source)

    except Exception as e:
        traceback.print_exc(e)


if __name__ == '__main__':
    try:
        main(source=sys.argv[1])
    except IndexError:
        print('Usage: python invalid_cookies.py [source]\n')
        sys.exit(1)
