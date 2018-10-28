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

utils.set_setting({"PROJECT_NAME": 'jd_zhilian_create_task', })
logger = utils.get_logger()

sql = '''
select cityName,url,code,thirdFunction,thirdFunctionCode,thirdFunctionURL
from spider.jd_task_entrence
where source = 'ZHI_LIAN'
and valid = 1
'''


def get_entrence():
    result = []
    entrence = utils.query_by_sql(sql)
    if entrence:
        for item in entrence:
            record = (
                item[0], item[1].encode('utf-8')
                , item[2], item[3].encode('utf-8'), item[4].encode('utf-8'))
            result.append(record)
    return result


def main():
    cfg = ConfigParser.ConfigParser()
    cfg.read('/data/config/morgan/morgan_spider_common_settings.cfg')
    entrence_list = get_entrence()
    logger.info('获取到 %s 个' % (len(entrence_list)))
    for item in entrence_list:
        param = {'cityUrl': item[1], 'funcCode': item[4], 'funcName': item[3],
                 'cityCode': item[2], 'cityName': item[0], 'pageNum': 1}
        data = {
            'traceID': str(uuid.uuid1()),
            'callSystemID': 'morgan-zhilian-jd-1',
            'taskType': 'JD_FETCH',
            'source': 'ZHI_LIAN',
            'executeParam': json.dumps(
                param,
                ensure_ascii=False)
        }
        utils.add_task(data=data)


if __name__ == '__main__':
    main()
