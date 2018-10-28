#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
"""
@version: python2.7
@author: 王增帅
@contact: 549409587@qq.com
@software: PyCharm
@file: create_five_one_inbox_task.py
@time: 2017/5/5 8:58
"""
import utils

logger = None


def create_task():
    for user_name in settings.account_list:
        deadline = int(time.time() - (time.time() % 86400) + time.timezone + 24 * 60 * 60) * 1000
        data = {
            'traceID': str(uuid.uuid1()),
            'callSystemID': 'morgan-51job-inbox-1',
            'taskType': 'RESUME_INBOX',
            'source': 'FIVE_ONE',
            'executeParam': user_name,
            'deadline': deadline
        }
        utils.add_task(data)


def main():
    create_task()


if __name__ == '__main__':
    global logger
    logger = utils.get_logger()

    main()
