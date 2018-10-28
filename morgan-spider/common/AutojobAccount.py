#! /usr/bin/env python
# coding=utf8

"""
@version: python2.7
@author: huangyee
@contact: 1173842904@qq.com
@software: PyCharm
@file: AutojobAccount.py
@time: 2017/10/8 20:59
"""
import traceback
import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import requests


# MYSQL_HOST=rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com
# MYSQL_PORT=3306
# MYSQL_USER=spider_admin
# MYSQL_PASSWD=n4UZknFH6F
# MYSQL_DB=spider

mysql_pool = None

def get_mysql_client():
    global mysql_pool
    if not mysql_pool:
        mysql_pool = PersistentDB(MySQLdb, host='rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com', user='spider_admin',
                                  passwd='n4UZknFH6F', db='autojob',
                                  port=3306, charset='utf8')
    conn = mysql_pool.connection()
    cur = conn.cursor()
    return conn, cur


def query_by_sql():
    conn, cur = get_mysql_client()
    try:
        sql = 'SELECT account_name,password_,qiancheng_name,company_name,channel_ FROM t_account '
        results = cur.execute(sql)
        if results:
            result = cur.fetchall()
            return result
    except Exception as e:
        return None
    return None


def process():
    result = query_by_sql()
    for r in result:
        source = ''
        if 'ZHILIAN' in r[4]:
            source = 'ZHI_LIAN'
        else:
            source = 'FIVE_ONE'
        url = 'http://localhost:8007/acc/add.json?source=%s&username=%s&password=%s&accountName=%s&companyName=%s&status=1' % (
            source, r[0], r[1], r[2], r[3])
        content = requests.get(url=url).content
        print content
        # @RequestParam Source source,
        # @RequestParam String username,
        # @RequestParam String password,
        # @RequestParam String accountName,
        # @RequestParam String companyName,
        # @RequestParam Integer status,


if __name__ == '__main__':
    process()
