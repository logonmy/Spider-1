#! /usr/bin/env python
# coding=utf8

"""
@version: python2.7
@author: huangyee
@contact: 1173842904@qq.com
@software: PyCharm
@file: create_task.py
@time: 2017/5/2 15:05
"""

import json
import sys
import requests
import uuid
import datetime
import time
import traceback
import settings

sys.path.append("../common")
import utils
import common_settings

logger = utils.get_logger()

'''
添加登陆任务
'''


def load_function():
    sql = '''
    SELECT type_code,type_name from dim.dim_source_function_type WHERE
    source_id=3 AND
    type_level = 3 AND
    parent_type_code in ('4010200', '7002000') AND
    type_name != '其他'
    '''
    results = utils.query_by_sql(sql)
    return results


def create_task():
    function_data = load_function()
    # account_data = load_account()
    # acc_index = 0
    if function_data:
        for x in range(len(function_data)):
            func = function_data[x]
            func_code = func[0]
            func_name = func[1]
            city_code = '530'
            city_name = '北京'
            data = {
                'source': "ZHI_LIAN",
                'pageNum': 0,
                'funcName': func_name.decode('utf8'), 'funcCode': func_code,
                'cityCode': city_code,
                'cityName': city_name
            }

            utils.add_task({
                'callSystemID': settings.project_settings['CALLSYSTEMID'],
                'taskType': 'RESUME_FETCH',
                'source': "ZHI_LIAN",
                'executeParam': json.dumps(data, ensure_ascii=False)

            })
        logger.info('add task success')
    else:
        logger.error('there are no functions or accounts found')


if __name__ == '__main__':
    create_task()
