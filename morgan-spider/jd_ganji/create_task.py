#! /usr/bin/env python
# coding=utf8
import ConfigParser
import json
import sys
import uuid

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
import utils

utils.set_setting({"PROJECT_NAME": 'jd_ganji_create_task', })
logger = utils.get_logger()

sql = '''
select cityName,url,thirdFunction,thirdFunctionURL
from spider.jd_task_entrence
where source = 'GJ_HR'
and valid = 1
'''


def get_entrence():
    result = []
    entrence = utils.query_by_sql(sql)
    if entrence:
        for item in entrence:
            record = (
                item[0], item[1].encode('utf-8')
                , item[2], item[3].encode('utf-8'))
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
            'callSystemID': 'morgan-ganji-jd-1',
            'taskType': 'JD_FETCH',
            'source': 'GJ_HR',
            'executeParam': json.dumps(
                {
                    'cityUrl': item[1],
                    'cityName': item[0],
                    'funcUrl': item[3],
                    'funcName': item[2],
                    'pageNum': 1,
                },
                ensure_ascii=False)
        }
        utils.add_task(data=data)


if __name__ == '__main__':
    main()
