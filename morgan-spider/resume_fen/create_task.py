#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: create_task.py
@create at: 2018-04-08 15:27

这一行开始写关于本文件的说明与解释
"""

from __future__ import print_function
import json
import time
import datetime
from mf_utils.core import InitCore


class CreateTask(InitCore):
    def __init__(self):
        super(CreateTask, self).__init__(
            local_setting={
                'TASK_TYPE': 'RESUME_FETCH',
                'SOURCE': 'RESUME_FEN'
            },
            # TEST
            # 测试环境配置
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )
        self.mysql_handler = self.init_mysql()

    def get_city_order(self):
        sql = """
        select cityName from spider.city_entrence WHERE source='%s' and
        valid=1
        """ % self.common_settings.SOURCE
        res = self.mysql_handler.query_by_sql(sql)
        city_order = [item[0] for item in res]
        self.logger.info('city_order 初始化完成: %s' % '/'.join(
            city_order).encode('utf-8'))
        return city_order

    def create_task_from_mysql(self, use_keywords=False):
        self.logger.info("开始推送任务.")
        city_order = self.get_city_order()
        cities = self.mysql_handler.query_by_sql(
            """select * from spider.city_entrence where source='%s' 
            and valid=1 and resourceType='RESUME_FETCH'""" %
            self.common_settings.SOURCE)
        # cities = city_mapping
        functions = self.mysql_handler.query_by_sql(
            """select * from spider.function_entrence where source='%s'
            and resourceType='RESUME_FETCH' and valid=1""" %
            self.common_settings.SOURCE)
        # functions = function_mapping
        self.logger.info('共加载城市： %s个 职能： %s个' % (
            len(cities), len(functions)))
        if not cities or not functions:
            self.logger.info('城市/职能加载失败.')
            return

        today = datetime.datetime.today()
        next_datetime = datetime.datetime(today.year, today.month, today.day,
                                          0, 0, 0) + datetime.timedelta(days=3)
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
        for city in city_result:
            for func in functions:
                param_zl = json.dumps({
                    'model_name': 'zhilian',
                    'job_code': func[8],
                    'job_name': func[7],
                    'area_code': city[6],
                    'area_name': city[1]}, ensure_ascii=False)
                param_lp = json.dumps({
                    'model_name': 'liepin',
                    'job_code': func[8],
                    'job_name': func[7],
                    'area_code': city[6],
                    'area_name': city[1]}, ensure_ascii=False)
                res = self.add_task(param_zl, deadline=deadline)
                if res.json().get('code') != 200:
                    self.logger.warning('任务推送失败： %s|%s'
                                        % (city[1].encode('utf-8'),
                                           func[7].encode('utf-8')))

                self.logger.info('任务推送成功： %s|%s'
                                 % (city[1].encode('utf-8'),
                                    func[7].encode('utf-8')))
                res = self.add_task(param_lp, deadline=deadline)
                if res.json().get('code') != 200:
                    self.logger.warning('任务推送失败： %s|%s'
                                        % (city[1].encode('utf-8'),
                                           func[7].encode('utf-8')))

                self.logger.info('任务推送成功： %s|%s'
                                 % (city[1].encode('utf-8'),
                                    func[7].encode('utf-8')))

        self.logger.info('执行完毕.')


if __name__ == '__main__':
    runner = CreateTask()
    runner.preview_settings()
    runner.create_task_from_mysql()
