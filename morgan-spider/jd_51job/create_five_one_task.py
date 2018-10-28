#! /usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import random
import re
import sys
import os
from five_one_module import SearchCondition

import traceback
import uuid
import time
import datetime
import json

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
import utils

utils.set_setting({"PROJECT_NAME": 'jd_51_create_task', })

logger = utils.get_logger()

sql = '''
select cityName,code,thirdFunction,thirdFunctionCode
from spider.jd_task_entrence
where source = 'FIVE_ONE'
and valid = 1
'''


def get_entrence():
    result = []
    entrence = utils.query_by_sql(sql)
    if entrence:
        for item in entrence:
            record = (item[0].encode('utf-8'), item[1].encode('utf-8'), item[2].encode('utf-8'), item[3].encode('utf-8'))
            result.append(record)
    return result


def main():
    cfg = ConfigParser.ConfigParser()
    cfg.read('/data/config/morgan/morgan_spider_common_settings.cfg')
    entrence_list = get_entrence()
    logger.info('获取到 %s 个' % (len(entrence_list)))
    random.shuffle(entrence_list)
    for item in entrence_list:
        condition = SearchCondition(item[0], item[1], item[2], item[3])
        execute_param = json.dumps(condition.to_dics(), ensure_ascii=False)
        data = {
            'traceID': str(uuid.uuid1()),
            'callSystemID': 'morgan-51job-jd-1',
            'taskType': 'JD_FETCH',
            'source': 'FIVE_ONE',
            'executeParam': execute_param
        }
        utils.add_task(data=data)


if __name__ == '__main__':
    main()
