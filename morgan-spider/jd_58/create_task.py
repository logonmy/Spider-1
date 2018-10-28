#! /usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import random
import sys
import os
import traceback
import uuid
import time
import datetime
import json
import requests
import lxml.html as xmlh
import re
from five_eight_module import SearchCondition

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
sys.path.append("..")
current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
import utils

utils.set_setting({"PROJECT_NAME": 'jd_58_create_task', })

logger = utils.get_logger()

sql = '''
select cityName,url,secondFunction,thirdFunction,thirdFunctionURL
from spider.jd_task_entrence
where source = 'FIVE_EIGHT'
and valid = 1
'''


def get_entrence():
    result = []
    entrence = utils.query_by_sql(sql)
    if entrence:
        for item in entrence:
            record = (
                item[0].encode('utf-8'), item[1].encode('utf-8'), item[2].encode('utf-8'), item[3].encode('utf-8'),
                item[4].encode('utf-8'))
            result.append(record)
    return result


def main():
    cfg = ConfigParser.ConfigParser()
    cfg.read('/data/config/morgan/morgan_spider_common_settings.cfg')
    entrence_list = get_entrence()
    logger.info('获取到 %s 个' % (len(entrence_list)))
    for item in entrence_list:
        condition = SearchCondition(item[0], item[1], item[2], item[3], item[4])
        execute_param = json.dumps(condition.to_dics(), ensure_ascii=False)
        data = {
            'traceID': str(uuid.uuid1()),
            'callSystemID': 'morgan-58-jd-1',
            'taskType': 'JD_FETCH',
            'source': 'FIVE_EIGHT',
            'executeParam': execute_param
        }
        utils.add_task(data=data)


if __name__ == '__main__':
    main()
