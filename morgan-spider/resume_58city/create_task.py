#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: IntelliJ IDEA
@file: create_task.py
@create at: 2018-09-04 09:58

这一行开始写关于本文件的说明与解释
"""

# 从settings.py中加载配置文件
# from conf import settings

# 从consul k-v中加载配置文件
import datetime
import json
import random
import time

from mf_utils.core import InitCore
from mf_utils.common import dict2obj
from mf_utils.load_settings import LoadSettingsFromConsul

settings = dict2obj(LoadSettingsFromConsul.get_settings(
    key='no_scrapy/resume_58city', host='172.16.25.36'), change_dict=False)

city_mapping = settings.CITY_MAPPING

func_mapping = settings.FUNC_MAPPING


class CreateTask(InitCore):
    def __init__(self):
        super(CreateTask, self).__init__(
            local_setting={
                'TASK_TYPE': 'RESUME_FETCH',
                'SOURCE': 'FIVE_EIGHT'
            },
            # 测试环境配置
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )

    def create_task(self):
        if not city_mapping or not func_mapping:
            self.logger.warning(
                'please make sure city_mapping or func_mapping is not None')

        self.logger.info('start push task ...')

        random.shuffle(city_mapping)
        random.shuffle(func_mapping)

        for city in city_mapping:
            city_url, city_name = city.split('|')
            for func in func_mapping:
                param = json.dumps({
                    'city_url': city_url,
                    'city_name': city_name.decode('utf-8'),
                    'keyword': func.decode('utf-8'),
                    'degree': '4'   # 大专
                }, ensure_ascii=False)

                param1 = json.dumps({
                    'city_url': city_url,
                    'city_name': city_name.decode('utf-8'),
                    'keyword': func.decode('utf-8'),
                    'degree': '5'   # 本科
                }, ensure_ascii=False)
                # 时间戳
                deadline = int(time.mktime(
                    (datetime.datetime.now() + datetime.timedelta(days=1)
                     ).timetuple()) * 1000)

                res = self.add_task(param, deadline=deadline)
                res = self.add_task(param1, deadline=deadline)
                if res.json().get('code') != 200:
                    self.logger.warning(
                        '任务推送失败： %s|%s, %s' % (
                            city_name, func, json.dumps(
                                res.json(),
                                ensure_ascii=False).encode('utf-8')))
                    continue

                self.logger.info('任务推送成功： %s|%s' % (city_name, func))


if __name__ == '__main__':
    runner = CreateTask()
    runner.preview_settings()
    runner.create_task()
