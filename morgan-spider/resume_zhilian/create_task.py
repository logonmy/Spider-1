#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: create_task.py.py
@create at: 2018-02-28 16:24

这一行开始写关于本文件的说明与解释
"""

from __future__ import print_function
import json
import random
import time
import datetime
from mf_utils.core import InitCore

# 从settings.py中加载配置文件
# from conf import settings

# 从consul k-v中加载配置文件
from mf_utils.common import dict2obj
from mf_utils.load_settings import LoadSettingsFromConsul

settings = dict2obj(LoadSettingsFromConsul.get_settings(
    key='no_scrapy/resume_zhilian', host='172.16.25.36'), change_dict=False)


class CreateTask(InitCore):
    def __init__(self):
        super(CreateTask, self).__init__(
            local_setting={
                'TASK_TYPE': 'RESUME_FETCH',
                'SOURCE': 'ZHI_LIAN'
            },
            # 测试环境配置
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )
        self.mysql_handler = self.init_mysql()

    # def get_city_order(self):
    #     sql = """
    #     select cityName from spider.city_entrence WHERE source='ZHI_LIAN' and
    #     valid=1
    #     """
    #     res = self.mysql_handler.query_by_sql(sql)
    #     city_order = [item[0] for item in res]
    #     self.logger.info('city_order 初始化完成: %s' % '/'.join(
    #         city_order).encode('utf-8'))
    #     return city_order

    def create_task_from_mysql(self, use_keywords=False):
        self.logger.info("开始推送任务.")
        # city_order = self.get_city_order()
        # cities = self.mysql_handler.query_by_sql(
        #     'select * from spider.city_entrence where source="ZHI_LIAN" '
        #     'and valid=1 and resourceType="RESUME_SEARCH"')
        cities = settings.city_mapping
        # functions = self.mysql_handler.query_by_sql(
        #     'select * from spider.function_entrence where '
        #     'source="ZHI_LIAN" and resourceType="RESUME_SEARCH"'
        #     'and valid=1')
        functions = settings.function_mapping
        self.logger.info('共加载城市： %s个 职能： %s个' % (
            len(cities), len(functions)))
        if not cities or not functions:
            self.logger.info('城市/职能加载失败.')
            return

        today = datetime.datetime.today()
        next_datetime = datetime.datetime(today.year, today.month, today.day,
                                          0, 0, 0) + datetime.timedelta(days=1)
        deadline = int(time.mktime(
            time.strptime(next_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                          '%Y-%m-%d %H:%M:%S'))) * 1000

        city_result = []
        # use_keyword = '0' if datetime.datetime.now().hour < 12 else '1'

        # if cities:
        #     city_dict = {i[1]: i for i in cities}
        #     for i in city_order:
        #         if i in city_dict:
        #             city_result.append(city_dict[i])
        #             city_dict.pop(i)
        #     city_result = city_result + city_dict.values()
        city_result = cities
        random.shuffle(city_result)
        random.shuffle(functions)
        for city in city_result:
            city = city.decode('utf-8')
            for func in functions:
                func = func.decode('utf-8')
                param = json.dumps({
                    'keywords': func,
                    'city': city,
                    'degree': 5,
                    'use_keywords': use_keywords
                }, ensure_ascii=False)
                res = self.add_task(param, deadline=deadline)
                if res.json().get('code') != 200:
                    self.logger.warning('任务推送失败： %s|%s'
                                        % (city.encode('utf-8'),
                                           func.encode('utf-8')))

                self.logger.info('任务推送成功： %s|%s'
                                 % (city.encode('utf-8'),
                                    func.encode('utf-8')))

        self.logger.info('执行完毕.')


if __name__ == '__main__':
    runner = CreateTask()
    runner.preview_settings()
    runner.create_task_from_mysql(use_keywords=True)
