#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 0023 18:07
# @Author  : huangyee
# @Email   : 1173842904@qq.com
# @File    : redis-test.py
# @Software: PyCharm
import sys
import os
import logging.handlers

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
current_file_name = os.path.basename(__file__)
logger = logging.getLogger()

import redis


def awake(redis_key, hash_key, mobile):
    redis_ = redis.Redis(host='10.0.3.52', port=6379, db=0)
    # print redis.hget('ZHI_LIAN', '2f56d972-fa35-4670-a1dd-cadbdc92a659')
    print ' redis db 0 查询操作结果： %s' % redis_.hget(redis_key, hash_key)
    print redis_.hset(redis_key, hash_key, mobile)
    print ' redis db 0 读取操作结果： %s' % redis_.hget(redis_key, hash_key)
    # print redis_.hdel(redis_key, hash_key)
    pass


def mobile2name(mobile, name, email):
    redis_ = redis.Redis(host='10.0.3.52', port=6379, db=2)
    print '根据手机号查找姓名跟邮箱结果： %s ' % redis_.get(mobile)
    print redis_.set(mobile, '"%s#%s"' % (name, email))
    pass


def awakeyouben(redis_key, hash_key, resumeid):
    redis_ = redis.Redis(host='10.0.3.52', port=6379, db=5)

    print '有本唤醒结果：%s ' % redis_.hget(redis_key, hash_key)
    print redis_.hset(redis_key, hash_key, resumeid)
    pass


def clear_db10():
    redis_ = redis.Redis(host='10.0.3.52', port=6379, db=10)
    keys = redis_.keys()
    repeat = []
    noRepeat = []
    for k in keys:
        print k + '====>>>' + redis_.get(k)
    #     if 'noRepeat' in k:
    #         noRepeat.append(str(k).replace('resume.noMobile.noRepeat', ''))
    #     else:
    #         repeat.append(str(k).replace('resume.noMobile', ''))
    # print list(set(noRepeat) ^ set(repeat))
    # redis_.flushdb()
    # clear_db11()
    # redis_.delete("*")
    # redis_.flushall()

def clear_db11():
    redis_ = redis.Redis(host='10.0.3.52', port=6379, db=10)
    redis_.flushdb()

def process():
    clear_db10()
    #
    # redis_ = redis.Redis(host='10.0.3.52', port=6379, db=10)
    # # print redis_.get('resume.noMobile__splitParam__258__splitParam__2018-W17__splitParam__1')
    # for key in redis_.keys(''):
    #     print '%s===>>>%s' % (key, redis_.get(key))
    #     print redis_.delete(key)
    #
    # redis_key0 = '李198218631'
    # hash_key0 = ' Aston Rose Project Consulting Co|上海市同济大学'
    # mobile = '17621769467'
    # awake(redis_key0, hash_key0, mobile)
    # report_redis_online()
    pass


if __name__ == '__main__':
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('/data/logs', 'redis-test'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)
    process()
    pass
