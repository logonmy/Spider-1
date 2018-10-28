#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: awake_fail_save.py
@create at: 2018-07-10 17:22

这一行开始写关于本文件的说明与解释
"""

import datetime
import re
import time

from mf_utils.logger import Logger
from mf_utils.common import datetime2str, str2datetime
from mf_utils.filter.RedisSet import RedisSet
from mf_utils.logger import fileConfigWithLogPath
from elasticsearch import Elasticsearch

fileConfigWithLogPath(log_path='/data/logs/morgan-spider/awake_fail_save.log')

logger = Logger.timed_rt_logger()


def main(check_day):
    es = Elasticsearch(hosts='172.16.25.9')
    index = 'morgan-v3-%s' \
            % (datetime2str(str2datetime(check_day), fmt='%Y.%m.%d'))
    start_time = int(time.mktime((str2datetime(check_day) -
                                  datetime.timedelta(
                                      hours=1)).timetuple())) * 1000 - 1
    end_time = int(time.mktime(
        (str2datetime(check_day)).timetuple())) * 1000

    body = {
        "version": True,
        "size": 10000,  # 用于控制输出数量
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "log_message:\"判断是否需要下载 id=\"",
                            "analyze_wildcard": True
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": end_time,
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "_source": {
            "excludes": []
        },
        "aggs": {
            "2": {
                "date_histogram": {
                    "field": "@timestamp",
                    "interval": "30m",
                    "time_zone": "Asia/Shanghai",
                    "min_doc_count": 1
                }
            }
        }
    }
    res = es.search(index=index, body=body)
    hits = res.get('hits').get('hits')
    today = datetime2str(str2datetime(check_day), fmt='%Y-%m-%d')
    pools = RedisSet('ZHI_LIAN_AWAKE_FAILED-%s' % today)

    logger.info("匹配到%s个唤醒失败的简历 『%s - %s』。"
                % (len(hits), start_time, end_time))
    for hit in hits:
        log_message = hit.get('_source').get('log_message')
        # 正则匹配id
        normal_id = re.findall('(?<=id=)\d+(?=\s)', log_message)[0]
        pools.sadd(normal_id)
    logger.info('当前集合长度为： %s' % len(pools.scard()))


if __name__ == '__main__':
    check_day = datetime2str(datetime.datetime.now())
    main(check_day=check_day)
