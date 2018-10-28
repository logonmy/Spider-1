#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
import sys
import logging
import requests

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
logger = logging.getLogger()


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
            "Accept-Encoding": "gzip, deflate, sdch",
            "Referer": refer_url
        }
    else:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
        }

    return headers


def serialize_instance(obj):
    d = {}
    d.update(vars(obj))
    return d

