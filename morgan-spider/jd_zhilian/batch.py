#! /usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import random
import re
import sys
import os

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

utils.set_setting({"PROJECT_NAME": 'batch', })

logger = utils.get_logger()

update_sql = '''
UPDATE jd_task_entrence
SET valid = 0
WHERE source = 'ZHI_LIAN'
and valid = 1
AND concat(code,'_',thirdFunctionCode)
IN (%s)
'''


def filter(key):
    utils.update_by_sql(update_sql % key)


def handle():
    prop_file = open('/data/config/morgan/jd-task/zhilian_city_function.properties', 'r')
    logger.info('读取文件/data/config/morgan/jd-task/zhilian_city_function.properties')
    count = 0
    line_list = prop_file.readlines()
    group = []
    for line in line_list:
        group.append("'" + line.replace('\n', '') + "'")
        count += 1
        if count % 10000 == 0 or count == len(line_list):
            filter(','.join(group))
            logger.info('count：%s', count)
            group = []
    logger.info('finish')
    prop_file.close()


def main():
    cfg = ConfigParser.ConfigParser()
    cfg.read('/data/config/morgan/morgan_spider_common_settings.cfg')
    logger.info('读取配置文件/data/config/morgan/morgan_spider_common_settings.cfg')
    handle()


if __name__ == '__main__':
    main()
