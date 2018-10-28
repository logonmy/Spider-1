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
WHERE source = 'CH_HR'
and valid = 1
AND cityName = '%s' AND thirdFunction
IN (%s)
'''


def filter(cityName, v):
    utils.update_by_sql(update_sql % (cityName, v))


def handle():
    prop_file = open('/data/config/morgan/jd-task/chinahr_task_deleted', 'r')
    task_deleted = json.loads(prop_file.readline())
    prop_file.close()
    count = len(task_deleted)
    for key, v in task_deleted.items():
        filter(key, "'" + "','".join(v) + "'")
        count -= 1
        logger.info(count)
    logger.info('finish')


def main():
    cfg = ConfigParser.ConfigParser()
    cfg.read('/data/config/morgan/morgan_spider_common_settings.cfg')
    logger.info('读取配置文件/data/config/morgan/morgan_spider_common_settings.cfg')
    handle()


if __name__ == '__main__':
    main()
