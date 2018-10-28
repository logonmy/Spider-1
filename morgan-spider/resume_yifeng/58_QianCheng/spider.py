#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com


import time
import json
import sys
import uuid
import redis
import datetime
from conf.settings import *
from utils.logger import Logger
from utils.RedisQueue import RedisQueue, RedisSet, RedisHash
from utils.db import ResumeRaw, Database
from utils.html_downloader import HtmlDownloader
from utils.html_parser import HtmlParser
from pykafka import KafkaClient


__all__ = ["ResumeSpider", "Spider"]


class Spider(object):
    """ Spider基础类 """
    def __init__(self, worker=None):
        """
        初始化下载器/解析器及日志接口
        :param worker: 标识当前worker
        """
        self.downloader = HtmlDownloader()
        self.parser = HtmlParser()
        self.log = Logger.rt_logger()
        self.worker = worker
        self.proxies = None


class ResumeSpider(Spider):
    def __init__(self, worker=None, site=None):
        super(ResumeSpider, self).__init__(worker=worker)
        self.site = site

        # 初始化卡夫卡
        self.kafka_client = KafkaClient(KAFKA_HOSTS)
        self.kafka_producer = self.kafka_client.topics[
            KAFKA_TOPIC].get_sync_producer()

        # 初始化redis队列
        self.q_user = RedisQueue(self.site+'_USER', host=REDIS_HOST,
                                 port=REDIS_PORT)
        self.q_search = RedisQueue(self.site+'_SEARCH', host=REDIS_HOST,
                                   port=REDIS_PORT)

        # 初始化redis集合
        self.s_filter = RedisSet(self.site+'_FILTER', host=REDIS_HOST,
                                 port=REDIS_PORT)

        # 初始化redis哈希表
        self.h_cookies = RedisHash(self.site + '_COOKIES', host=REDIS_HOST,
                                   port=REDIS_PORT)

        # 初始化mysql数据库
        self.db = Database('mysql+mysqldb://%s:%s@%s:%s/%s?charset=utf8'
                           % (MYSQL_USER, MYSQL_PASSWD,
                              MYSQL_HOST, MYSQL_PORT, MYSQL_DB),
                           encoding='utf-8')
        self.db.init_table()

        if self.h_cookies.hget('cookies'):
            self.cookies = eval(self.h_cookies.hget('cookies'))
        else:
            self.cookies = None

    def init_user(self, *args, **kwargs):
        pass

    def init_search(self, *args, **kwargs):
        pass

    def login(self, *args, **kwargs):
        while True:
            if args:
                username, password = args
            else:
                if not self.q_user.empty():
                    username, password = eval(self.q_user.get())
                else:
                    self.log.error("%s[%s]: login 没有足够的账户了" %
                                   (self.site, self.worker))
                    time.sleep(60)
                    continue
            res = self.downloader.download(
                'http://www.yifengjianli.com/base/signin',
                proxies=self.proxies)
            if res.status_code == 200:
                self.log.info("%s[%s]: login 跳转到登录页面"
                              % (self.site, self.worker))
            else:
                self.log.warning("%s[%s]: login 登录页面加载失败"
                                 % (self.site, self.worker))
                sys.exit()

            data = {
                'email': username,
                'password': password,
                'status': 1
            }
            res1 = self.downloader.download(
                'http://www.yifengjianli.com/user/userLogin', method='POST',
                data=data, proxies=self.proxies)
            # print res1.text
            try:
                code = json.loads(res1.content).get('code')
                if code == 200:
                    self.log.info("%s[%s]: login %s 登录成功" %
                                  (self.site, self.worker, username))
                    self.h_cookies.hset('cookies',
                                        str(res1.cookies.get_dict()))
                    return True
                elif code == 301:
                    self.log.warning("%s[%s]: login %s 帐号被拉黑了" %
                                   (self.site, self.worker, username))
                    return False
                else:
                    self.log.error("%s[%s]: login %s 登录失败" %
                                   (self.site, self.worker, username))
                    return False
            except AttributeError:
                self.log.error("%s[%s]: login %s 登录异常" %
                               (self.site, self.worker, username))
                return False

    def get_resume_list(self, *args, **kwargs):
        pass

    def get_resume(self, *args, **kwargs):
        pass

    def download_resume(self, *args, **kwargs):
        pass

    def save(self, resume_result):
        resume_uuid = uuid.uuid1()
        mysql_data = {
            'source': self.site,
            'content': resume_result,
            'createBy': 'python',
            'trackId': resume_uuid,
            'createTime': datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"),
            # 'email': '',
        }
        self.db.session.execute(
            ResumeRaw.__table__.insert(), mysql_data
        )
        self.db.session.commit()

        save_mysql_id = self.db.session.query(ResumeRaw).filter_by(
            source=mysql_data['source'],
            content=mysql_data['content'],
            createBy=mysql_data['createBy'],
            createTime=mysql_data['createTime']
        ).first().id

        # print save_mysql_id

        kafka_data = {
            "channelType": "WEB",
            "content": {
                "content": resume_result,
                "id": save_mysql_id,
                "createBy": "python",
                "createTime": int(time.time() * 1000),
                "ip": '',
                "resumeSubmitTime": '',
                "resumeUpdateTime": '',
                "source": self.site,
                "trackId": str(resume_uuid),
                "avatarUrl": '',
            },
            "interfaceType": "PARSE",
            "resourceDataType": "RAW",
            "resourceType": "RESUME_SEARCH",
            "source": self.site,
            "trackId": str(resume_uuid),
            'traceID': str(resume_uuid),
            'callSystemID': "YI_FENG_51_58",
        }
        dumps = json.dumps(kafka_data, ensure_ascii=False)
        self.kafka_producer.produce(dumps)
