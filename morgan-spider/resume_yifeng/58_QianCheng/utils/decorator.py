#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com

from logger import Logger

log = Logger.rt_logger()


def retry(attempt):
    def decorator(func):
        def wrapper(*args, **kwargs):
            att = 0
            while att < attempt:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    att += 1
                    log.exception("%s: %s 第%s次重试"
                                  % (func.__name__, repr(e), str(att)))
        return wrapper
    return decorator
