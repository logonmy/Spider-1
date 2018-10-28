#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue@mofanghr.com
@software: PyCharm
@file: invalid_cookies.py
@create at: 2017-10-31 15:37

这一行开始写关于本文件的说明与解释
"""

# 该脚本已停用

from __future__ import print_function

import pymysql
import requests
import traceback

import time

# 数据库权限描述： 测试库读取spider
MYSQL_CONF = {
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'host': 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'super_reader',
    'password': 'nMGZKQIXr4PE8aR2',
    'db': 'autojob'
}


def load_account():
    conn = pymysql.Connect(**MYSQL_CONF)
    cur = conn.cursor()
    try:
        print("开始加载人才啊帐号！")
        sql = '''
        SELECT username, password
        FROM `morgan-manager`.account
        WHERE source = 'REN_CAI' AND valid = 1;
        '''
        cur.execute(sql)
        res = cur.fetchall()
        print("加载完成：总计%s个帐号" % len(res))
        return res

    except Exception as e:
        traceback.print_exc(e)
    finally:
        cur.close()
        conn.close()


def invalid(username, password):
    try:
        url = "http://172.16.25.41:8002/acc/invalidCookie.json?" \
              "userName=%s&password=%s&source=%s" % (username, password,
                                                     "REN_CAI")
        res = requests.get(url)
        if res.json().get('code') == 200:
            print("帐号失效成功: %s %s" % (username, password))
        else:
            print("帐号失效失败： %s " % res.json())
    except Exception as e:
        traceback.print_exc(e)
        time.sleep(60)
        print("帐号失效异常： %s" % e)


def update_fresh_score(username, password):
    try:
        url = "http://172.16.25.41:8002/acc/updateUser.json?" \
              "userName=%s&password=%s&source=%s" % (username, password,
                                                     "REN_CAI")
        data = {
            'freshScore': 200
        }
        res = requests.post(url, data=data)
        if res.json().get('code') == 200:
            print("更新freshScore成功: %s %s" % (username, password))
        else:
            print("更新freshScore失败： %s " % res.json())
    except Exception as e:
        traceback.print_exc(e)
        time.sleep(60)
        print("更新freshScore异常： %s" % e)


def main():
    try:
        accounts = load_account()

        for item in accounts:
            username = item.get('username').encode('utf-8')
            password = item.get('password').encode('utf-8')
            update_fresh_score(username, password)
            invalid(username, password)

    except Exception as e:
        traceback.print_exc(e)


if __name__ == '__main__':
    main()
