#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: IntelliJ IDEA
@file: resumeRaw2mns.py
@create at: 2018-08-29 16:48

这一行开始写关于本文件的说明与解释
"""
import datetime
import json
import time
import uuid

from MySQLdb.cursors import DictCursor
from mf_utils.sql.mysql import MysqlHandle
from mf_utils.mns import MnsHandle

# 数据库权限描述： 读取autojob
MYSQL_CONF = {
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'host': 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'super_reader',
    'passwd': 'nMGZKQIXr4PE8aR2',
    'db': 'autojob'
}

MNS_CONF = {
    'mns_endpoint':
        'http://1315265288610488.mns.cn-beijing-internal-vpc.aliyuncs.com',
    'mns_accid': 'LTAIf2I0xlEogGx5',
    'mns_acckey': '14EJ0FhqZL5czEdw5E54pAjyVkdtbI',
    'mns_token': '',
    'mns_queue': 'morgan-queue-resume-raw'
}

# 解析失败的原文
raw_id_tuple = (
    21943893,
    21945208,
    21947904,
    21948493,
    21949155,
    21958124,
    21966899,
    21966900,
    21967586,
    21972483,
    21972484,
    21975933,
    21976029,
    21978885,
    22000322,
    22004135,
    22007399,
    22009591,
    22010676,
    22010677,
    22010976,
    22011216,
    22011218,
    22011879,
    22012310,
    22013030,
    22013950,
    22013951,
    22014386,
    22014707,
    22015073,
    22015075,
    22015707,
    22016100,
    22016103,
    22016451,
    22016452,
    22016910,
    22017662,
    22018166,
    22018169,
    22018930,
    22019418,
    22021778,
    22021892,
    22022330,
    22022828,
    22022829,
    22023037,
    22023707,
    22023708,
    22023894,
    22024094,
    22024095,
    22025437,
    22025861,
    22026351,
    22026537,
    22026958,
    22029462,
    22030020,
    22030031,
    22030258,
    22030261,
    22030872,
    22031306,
    22031310,
    22031320,
    22031321,
    22031325,
    22031328,
    22031329,
    22031331,
    22031335,
    22031337,
    22031350,
    22031353,
    22031354,
    22031356,
    22031357,
    22031360,
    22031362,
    22031363,
    22031364,
    22031365,
    22031367,
    22031763,
    22031764,
    22031770,
    22031771,
    22031773,
    22031774,
    22031775,
    22031779,
    22031787,
    22031789,
    22031790,
    22031793,
    22031795,
    22031797,
    22031798,
    22031804,
    22031806,
    22031812,
    22031820,
    22031829,
    22031833,
    22032901,
    22032904,
    22033402,
    22033412,
    22033413,
    22034438,
    22034443,
    22035447,
    22035826,
    22037261,
    22038058,
    22038852,
    22039127,
    22039975,
    22040432,
    22040724,
    22042828,
    22043490,
    22043852,
    22044289,
    22044546,
    22045092,
    22048439,
    22048593,
    22048598,
    22048984,
    22050349,
    22050661,
    22050791,
    22054097,
    22054098,
    22056253,
    22056634,
    22057613,
    22059187,
    22059218,
    22059874,
    22060300,
    22060301,
    22060307,
    22061323,
    22061325,
    22062061,
    22062615,
    22063312,
    22063645,
    22064741,
    22065080,
    22065081,
    22065572,
    22066085,
    22066522,
    22067325,
    22067533,
    22067535,
    22068569,
    22069157,
    22069881,
    22070452,
    22070453,
    22071426,
    22072122,
    22072133,
    22072884
)

sql = '''
select * from spider.resume_raw where id in {}
'''.format(raw_id_tuple)


class JsonCustomEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, datetime.date):
            return value.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, value)


def main():
    mysql_handle = MysqlHandle(**MYSQL_CONF)

    mns_handle = MnsHandle(**MNS_CONF)

    data = mysql_handle.query_by_sql(sql)

    for item in data:
        content = json.dumps(
            item, ensure_ascii=False, cls=JsonCustomEncoder).encode('utf-8')
        track_id = str(uuid.uuid1())

        mns_data = {
            "channelType": "WEB",
            "content": {
                "content": content,
                "id": item.get('id'),
                "createBy": "python",
                "createTime": int(time.time() * 1000),
                "ip": '',
                'emailJobType': '',
                'emailCity': '',
                'deliverJobName': '',
                'deliverJobCity': '',
                "resumeSubmitTime": '',
                "resumeUpdateTime": '',
                "source": item.get('source').encode('utf-8'),
                "avatarUrl": '',
                'trackId': track_id
            },
            "interfaceType": "PARSE",
            "resourceDataType": "RAW",
            "resourceType": "RESUME_EMAIL",
            "source": item.get('source').encode('utf-8'),
            "trackId": track_id,
            "traceID": track_id,
            "callSystemID": ''
        }

        print mns_data

        mns_handle.save(json.dumps(mns_data, ensure_ascii=False))


if __name__ == '__main__':
    main()
