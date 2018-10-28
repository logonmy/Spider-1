#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
"""
@version: python2.7
@author: 王增帅
@contact: 549409587@qq.com
@software: PyCharm
@file: __init__.py.py
@time: 2017/4/28 10:18
"""

import logging
import traceback
from logging.handlers import RotatingFileHandler
import uuid
import time
import datetime
import json
import os
import requests
import re

logger = logging.getLogger()


def main():
    pass


if __name__ == '__main__':
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('/data/logs', '__init__.py'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)

    main()