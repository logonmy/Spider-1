#!coding:utf8

import ConfigParser
import sys

import uuid
import json

sys.path.append('../common')
import utils

utils.set_setting({"PROJECT_NAME": 'jd_chinahr_create_task', })
logger = utils.get_logger()

sql = '''
select cityName, code,thirdFunction
from spider.jd_task_entrence
where source = 'CH_HR'
and valid = 1
'''


def get_entrence():
    result = []
    entrence = utils.query_by_sql(sql)
    if entrence:
        for item in entrence:
            record = (
                item[0].encode('utf-8'), item[1].encode('utf-8'), item[2].encode('utf-8'))
            result.append(record)
    return result


def main():
    cfg = ConfigParser.ConfigParser()
    cfg.read('/data/config/morgan/morgan_spider_common_settings.cfg')
    entrence_list = get_entrence()
    logger.info('获取到 %s 个' % (len(entrence_list)))
    for item in entrence_list:
        data = {
            'traceID': str(uuid.uuid1()),
            'callSystemID': 'morgan-chinahr-jd-1',
            'taskType': 'JD_FETCH',
            'source': 'CH_HR',
            'executeParam': json.dumps(
                {"funName": item[2], "cityCode": item[1], "cityName": item[0], "keyword": item[2]},
                ensure_ascii=False)
        }
        utils.add_task(data=data)


if __name__ == '__main__':
    main()
