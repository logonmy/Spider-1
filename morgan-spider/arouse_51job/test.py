#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
import os

import MySQLdb
import time

import datetime

import arouse_utils

reload(sys)
sys.setdefaultencoding("utf-8")


def sel_from_dim_func_type():
    """
    生成所需职能
    :return:
    """

    sql = """
SELECT * from dim_source_function_type WHERE
source_id=2 AND
type_level = 3 AND
parent_type_code in ( '3000', '3100') AND
type_name != '其他';
    """
    conn = MySQLdb.connect('172.16.25.1', 'bi_admin', 'bi_admin#@1mofanghr', 'dim', charset='utf8')
    cur = conn.cursor()

    try:
        cur.execute(sql)
        results = cur.fetchall()
    except:
        pass
    for result in results:
        func_name = result[4]
        func_code = result[3]
        f = open('function_list.txt', 'a')

        date = {
            'function_name': str(func_name),
            'function_code': str(func_code),
            'region_name': '北京',
            'region_code': '010000',
        }
        f.write(json.dumps(date, ensure_ascii=False) + '\n')


# sel_from_dim_func_type()


def test_arouse_by_awake(*args):
    """
    测试唤醒-可以唤醒部分
    :param args:
    :return:
    """
    print '测试唤醒-可以唤醒部分'
    ids = []
    if args:
        for key in args:
            ids.append(key)

    arouse_utils.resumeArouse(ids)


def test_arouse_by_create(*args):
    """
    测试唤醒-唤醒失败部分
    :param args:
    :return:
    """
    print '测试唤醒-唤醒失败部分'
    ids = []
    if args:
        for key in args:
            ids.append(key)

    arouse_utils.resumeArouse(ids)


# from flask import Flask
#
# app = Flask(__name__)
#
#
# @app.route('/arouse-51job/<externalIds>')
# def hello_world(externalIds):
#     ids_split = externalIds.split(',')
#     return arouse_utils.resumeArouse(ids_split)
#
#
# if __name__ == '__main__':
#     # app.debug = True
#     app.run(host='10.0.3.222', port='8888')


# mid = int(time.time() - (time.time() % 86400) + time.timezone +24*60*60)
# print time.ctime(mid)
# arouse_utils.save_history('CREATE')
