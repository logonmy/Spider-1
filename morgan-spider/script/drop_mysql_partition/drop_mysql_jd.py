#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue@mofanghr.com
@software: PyCharm
@file: dingding_robot.py
@create at: 2017-10-24 10:57

这一行开始写关于本文件的说明与解释
"""
import json
import traceback

import requests
import MySQLdb
import datetime
from mf_utils.extend.dingding_robot import DingDingRobot


def main(table_name):
    print '======================================================='
    print 'start main', table_name, str(datetime.datetime.now())

    # MYSQL_HOST = '172.16.25.1'
    # MYSQL_PORT = 3306
    # MYSQL_USER = 'bi_admin'
    # MYSQL_PASSWD = 'bi_admin#@1mofanghr'
    # MYSQL_DB = 'spider'

    MYSQL_HOST = 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com'
    MYSQL_PORT = 3306
    MYSQL_USER = 'spider_admin'
    MYSQL_PASSWD = 'n4UZknFH6F'
    MYSQL_DB = 'spider'

    mysql_conn = MySQLdb.connect(host=MYSQL_HOST, port=MYSQL_PORT,
                                 user=MYSQL_USER, passwd=MYSQL_PASSWD,
                                 db=MYSQL_DB)
    mysql_cursor = mysql_conn.cursor()

    partition_number = mysql_cursor.execute(
        "SELECT PARTITION_NAME,TABLE_ROWS FROM INFORMATION_SCHEMA.PARTITIONS WHERE TABLE_NAME = '%s'" % table_name)
    if not partition_number:
        print 'there has no partitions in mysql, quiting!!!'
        return []
    partitions = mysql_cursor.fetchall()
    date_now = datetime.datetime.now()
    drop_partition_list = []
    for i in partitions:
        try:
            partition_data = i[0].split('_')[1]
            if len(partition_data) < 8:
                raise Exception
        except Exception as e:
            print 'get error when split partition name', i
            continue
        date_create = datetime.datetime(int(partition_data[:4]),
                                        int(partition_data[4:6]),
                                        int(partition_data[6:8]))
        check_days = 1
        if table_name == 'jd_raw':
            check_days = 1
        elif table_name in ['jd_parsed', 'jd_normal']:
            check_days = 3
        else:
            check_days = 1
        if (date_now - date_create).days >= check_days:
            mysql_cursor.execute(
                'alter table %s drop partition %s;' % (table_name, i[0]))
            mysql_conn.commit()
            print 'alter table %s drop partition %s;' % (table_name, i[0])
            print 'finish drop partition', i
            drop_partition_list.append(i[0])
    mysql_cursor.close()
    mysql_conn.close()
    print 'done!!!'
    return drop_partition_list


def test():
    robot_object = DingDingRobot(
        'eb749abfe9080a69da6524b77f589b8f6ddbcc182c7a41bf095b095336edb0a1')
    robot_object.send_text(u'测试')


if __name__ == '__main__':
    # test()
    robot_object = DingDingRobot(
        'eb749abfe9080a69da6524b77f589b8f6ddbcc182c7a41bf095b095336edb0a1')
    partition_dict = {}
    message = ''
    for table_name in ['jd_raw', 'jd_parsed', 'jd_normal']:
        partition_dict[table_name] = main(table_name)
    if not reduce(lambda x, y: x + len(y), [0, ] + partition_dict.values()):
        message = '[drop_mysql_partition] there has no partitions to drop in all tables'
        # send_sms(message)
    else:
        message = '[drop_mysql_partition]:\n'
        for i in partition_dict:
            if partition_dict[i]:
                message = message + 'has drop partitions:%s in table %s\n' % (
                ', '.join(partition_dict[i]), i)
                # send_sms(message)
    # print message
    robot_object.send_text(message)
