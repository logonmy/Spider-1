#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import re
import sys
import uuid

import oss2
import redis
import requests
from pykafka import KafkaClient
reload(sys)
sys.setdefaultencoding("utf-8")
"""
@version: python2.7
@author: 王增帅
@contact: 549409587@qq.com
@software: PyCharm
@file: spider_utils.py
@time: 2017/4/13 14:39
"""

def trim(content):
    if not content:
        return None
    content = content.replace('\t', '')
    content = content.replace('  ', '')
    content = content.replace(' ', '')
    content = content.replace('\r\n', '')
    return content


def find(pattern, context):
    if not context:
        return None

    findall = re.findall(pattern=pattern, string=context)

    if findall:
        return findall[0]
    else:
        return None


def get_info_headers(refer_url=None):
    if refer_url:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Referer": refer_url
        }
    else:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8"
        }

    return headers


def serialize_instance(obj):
    d = {}
    d.update(vars(obj))
    return d


