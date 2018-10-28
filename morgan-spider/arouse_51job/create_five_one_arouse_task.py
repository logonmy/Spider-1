#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import sys
import uuid
import time
import datetime
import settings
reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
import utils
"""
@version: python2.7
@author: 王增帅
@contact: 549409587@qq.com
@software: PyCharm
@file: create_five_one_arouse_task.py
@time: 2017/5/5 8:58
"""
# logger = None


def make_task_list():
    """
    从任务列表和帐号列表读取数据拼接成excutePartam 落地task.txt
    :return:
    """
    account_names = open('account_list').readlines()
    function_list = open('function_list.txt').readlines()

    for account_name in account_names:
        for i in xrange(5):
            try:
                function = function_list.pop()
            except:
                return
            function = json.loads(function)
            account_name = account_name.replace('\n', '')
            function['userName'] = account_name
            function['page_num'] = 25
            f = open('task_list', 'a')
            f.write(json.dumps(function, ensure_ascii=False) + '\n')


def create_task():
    #  从指定文件读取任务列表 发送至调度
    params = open('task_list').readlines()
    for param in params:
        deadline = datetime.datetime.now() + datetime.timedelta(hours=6)
        deadline = int(time.mktime(deadline.timetuple())) * 1000
        data = {
            'traceID': str(uuid.uuid1()),
            'callSystemID': 'morgan-51job-arouse-1',
            'taskType': 'RESUME_FETCH',
            'source': 'FIVE_ONE',
            'executeParam': param,
            'deadline': deadline
        }
        utils.add_task(data)


def main():
    # make_task_list()
    create_task()


if __name__ == '__main__':
    # global logger
    # logger = utils.get_logger()

    main()
