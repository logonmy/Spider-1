#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
current_file_name = os.path.basename(__file__)
"""
@version: python2.7
@author: liuxiaodong
@contact: 754089893@qq.com
@software: PyCharm
@file: mns_test.py
@time: 2018/4/12 下午1:52
"""
from gevent import monkey

monkey.patch_all()
import gevent
import logging
import traceback
from logging.handlers import RotatingFileHandler
import json
from mf_utils.mns import MnsHandle

logger = logging.getLogger()


def main():
    num = 100
    client = MnsHandle('http://1315265288610488.mns.cn-beijing.aliyuncs.com/', 'LTAIf2I0xlEogGx5',
                       '14EJ0FhqZL5czEdw5E54pAjyVkdtbI', '', 'spark-test')
    data = {
        "name": "resume.noMobile",
        "params": [
            # 根据简历更新时间算
            {"name": "day", "value": "2018-05-22", "paramScore": 2 ** 0},  # 日
            {"name": "week", "value": "2018-W18", "paramScore": 2 ** 1},  # 周
            {"name": "month", "value": "2018-04", "paramScore": 2 ** 2},  # 月
            {"name": "quarter", "value": "2018-02", "paramScore": 2 ** 3},  # 季
            {"name": "year", "value": "2018", "paramScore": 2 ** 4},  # 年

            {"name": "city", "value": "8631", "paramScore": 2 ** 5},  # 城市
            {"name": "source", "value": "6", "paramScore": 2 ** 6},  # 渠道：智联、前程、省钱招
            {"name": "collectType", "value": "BUY", "paramScore": 2 ** 7},  # 获取方式：SPIDER、AWAKE、BUY、SUBMIT
            {"name": "newResume", "value": "1", "paramScore": 2 ** 8},  # 是否净增：是、否
            {"name": "rpoResume", "value": "1", "paramScore": 2 ** 9},  # 是否有效RPO：YES、NO
        ],
        "value": "18200154568"
    }
    for index in xrange(0, num):
        print 11
        client.save(json.dumps(data, ensure_ascii=False))


def start_thread():
    gevent.joinall([
        gevent.spawn(main) for i in xrange(5)
    ])


if __name__ == '__main__':
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s %(threadName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('/data/logs', 'mns_test'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)

    main()
