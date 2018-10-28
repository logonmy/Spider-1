#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: resume_zhilian_crm.py
@create at: 2018-05-14 09:25

这一行开始写关于本文件的说明与解释
"""
import json
import random
import sys
import time
import datetime
import uuid
import gevent
from mf_utils.data.RedisHash import RedisHash
from mf_utils.extend.dingding_robot import DingDingRobot
from mf_utils.queue.RedisQueue import RedisQueue
from simplejson.scanner import JSONDecodeError
from mf_utils.common import cookie2str, datetime2str, str2datetime
from mf_utils.logger import fileConfigWithLogPath

from resume_zhilian import ResumeZhiLianBase, ResumeZhiLianIhr, \
    ZhiLianResumeException, AccountLimitedException

from create_task import settings
from gevent import monkey
monkey.patch_all()

REDIS_HOST = '172.16.25.36'
REDIS_PORT = '6379'
REDIS_PASSWORD = ''

COOKIE_CONTROL = {}

# 用于控制单帐号同时只有一个线程使用
RUN_STATUS = {}

DAY_LIMITED = 1

fileConfigWithLogPath(
    log_path='/data/logs/morgan-spider/resume_zhilian_crm.log')


class JsonCustomEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, datetime.date):
            return value.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, value)


class ResumeZhiLianCrmBase(ResumeZhiLianBase):
    def __init__(self, local_setting=None):
        super(ResumeZhiLianCrmBase, self).__init__(
            local_setting=local_setting,
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )
        # detail 黑名单
        self.h_black_list = RedisHash("zhi_lian_resume_crm_back_list",
                                      host=REDIS_HOST,
                                      port=REDIS_PORT,
                                      password=REDIS_PASSWORD)
        # 帐号当天使用次数
        self.h_use_record = RedisHash("zhi_lian_resume_crm_search_use_record",
                                      host=REDIS_HOST,
                                      port=REDIS_PORT,
                                      password=REDIS_PASSWORD)
        # 帐号已达上限标识
        self.h_over_search_limit = RedisHash("zhi_lian_crm_over_search_limit",
                                             host=REDIS_HOST,
                                             port=REDIS_PORT,
                                             password=REDIS_PASSWORD)
        self.q_search_account = RedisQueue(
            "zhi_lian_resume_crm_search_account",
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD)
        self.robot_login = DingDingRobot(
            access_token="b80ce3024c1818fe341bfad52bed12f2"
                         "4448d6180174a88bc1570c8908f4623a"
        )

    def push_resume(self, **data):
        # url = 'http://10.0.3.60:8213/parse/resume.json'
        url = 'http://172.16.25.2:8213/parse/resume.json'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }
        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data)
        if res.json().get('code') == 200:
            self.logger.info('[%s] 简历 %s 推送成功'
                             % (data['ResourceType'],
                                data['resumeId'].encode('utf-8')))
        else:
            self.logger.warning('[%s] 简历 %s 推送失败： %s'
                                % (data['ResourceType'],
                                   data['resumeId'].encode('utf-8'),
                                   res.content))

    def resume_search(self, page, **search_args):
        self.get_cookie()
        ip = eval(self.auth_kwargs['proxy'])['ip']
        port = eval(self.auth_kwargs['proxy'])['port']

        self.proxies = {
            'http': 'http://%s:%s' % (ip, port),
            'https': 'https://%s:%s' % (ip, port),
        }
        today = '|' + datetime2str(datetime.datetime.now(), '%Y-%m-%d')

        # print(search_args)
        resume_list = self.get_resume_list(page=page, **search_args)

        if not resume_list:
            raise ZhiLianResumeException('resume_list_empty')

        for resume_args in resume_list:
            # 用于限制帐号进入详情页次数
            if not self.h_use_record.hget(
                    self.auth_kwargs['username'] + today):
                self.h_use_record.hset(self.auth_kwargs['username'] + today, 0)
                count = 0
            else:
                count = int(
                    self.h_use_record.hget(
                        self.auth_kwargs['username'] + today))

            if self.check_limit(count=count):
                today = datetime2str(datetime.datetime.now(), '%Y-%m-%d')
                self.h_over_search_limit.hset(today + '|' + self.auth_kwargs[
                    'username'].encode('utf-8'), 1)
                raise ZhiLianResumeException('user_record_limited')

            # 用于简历去重
            try:
                resume_id = str(resume_args.get('resumeNo').encode('utf-8')[
                                :10])
            except:
                resume_id = str(resume_args.get('number')[:10])
            last_search_day = self.h_black_list.hget(resume_id)
            if last_search_day:
                distance = (str2datetime(today.replace('|', ''), '%Y-%m-%d')
                            - str2datetime(last_search_day, '%Y-%m-%d')).days
            else:
                distance = DAY_LIMITED + 1
            if distance < DAY_LIMITED:
                self.logger.warning('该简历%s天内已经被采集过: %s'
                                    % (DAY_LIMITED, resume_id))
                continue
            self.h_black_list.hset(resume_id, today.replace('|', ''))
            resume_detail = self.get_resume_detail(
                resume_args=resume_args)

            if not resume_detail:
                continue

            if resume_detail.get('resumeSource').encode('utf-8').lower() == \
                    'download':
                resource_type = 'RESUME_INBOX'
            else:
                resource_type = 'RESUME_SEARCH'

            content = json.dumps({'name': '', 'email': '', 'phone': '',
                                  'html': resume_detail},
                                 ensure_ascii=False)
            data = {
                'ChannelType': 'APP',
                'Source': self.source,
                'ResourceType': resource_type,
                'content': content,
                'accountContent': json.dumps(self.auth_kwargs,
                                             ensure_ascii=False,
                                             cls=JsonCustomEncoder),
                'resumeId': resume_detail.get('resumeNo'),
                'searchData': json.dumps(
                    search_args.get('origin_search_args'), ensure_ascii=False),
                'code': 200
            }
            self.push_resume(**data)
            time.sleep(random.randint(1, 5))


class ResumeZhiLianCrmIhr(ResumeZhiLianCrmBase, ResumeZhiLianIhr):
    def __init__(self, local_setting=None):
        super(ResumeZhiLianCrmIhr, self).__init__(
            local_setting=local_setting,
        )

    def get_downresumevali(self, referer, **kwargs):
        url = 'https://ihr.zhaopin.com/resumemanage/downresumevali.do' \
              '?access_token=%s' % self.access_token
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'ihr.zhaopin.com',
            'Origin': 'https://ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }

        data_ = [{
            "resumejlname": "",
            "resumeNo": kwargs['resume_id'] + "_1_1",
            "version": 1,
            "lanType": 1,
            "resumenumber": kwargs['resume_id'],
            "tjString": "3010,1002,601",
            "resumeJobId": 0
        }]
        data = {
            'data': json.dumps(data_, ensure_ascii=False)
        }

        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            proxies=self.proxies)
        if res.json().get('code') == 200:
            self.logger.info('获取downresumevali成功: %s' % res.content)
            return True
        elif res.json().get('code') == 802:
            self.logger.info('获取downresumevali成功: %s' % res.content)
            return False
        else:
            self.logger.warning('获取downresumevali失败: %s' % res.content)
            return

    def get_balance(self, referer, **kwargs):
        url = 'https://ihr.zhaopin.com/resumedownload/balance.do' \
              '?access_token=%s' % self.access_token
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'ihr.zhaopin.com',
            'Origin': 'https://ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = [{
            'cityId': kwargs['city_code'],
            'resumeNumber': kwargs['resume_id']
        }]

        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=json.dumps(
                                                data, ensure_ascii=False),
                                            proxies=self.proxies)
        if res.json().get('code') == 200:
            coins = res.json().get('data').get('zlcoins')
            self.logger.info('获取balance成功. %s' % coins)
            return coins
        else:
            self.logger.warning('获取balance失败: %s' % res.content)

    def get_price(self, referer, **kwargs):
        url = 'https://ihr.zhaopin.com/resumedownload/price.do' \
              '?access_token=%s' % self.access_token
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'ihr.zhaopin.com',
            'Origin': 'https://ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'coupon': '',
            'resumeList': [{
                'cityId': kwargs['city_code'],
                'resumeNumber': kwargs['resume_id']
            }]
        }

        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=json.dumps(
                                                data, ensure_ascii=False),
                                            proxies=self.proxies)
        if res.json().get('code') == 200:
            price = res.json().get('data').get('zlcoinsRealPrice')
            self.logger.info('获取price成功. %s' % price)
            return price
        else:
            self.logger.warning('获取price失败: %s' % res.content)

    def get_assetcount(self, referer):
        url = 'https://ihr.zhaopin.com/zlCoins/assetcount.do?access_token' \
              '=%s&type=1' % self.access_token

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Host': 'ihr.zhaopin.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'Referer': referer,
            'X-Requested-With': 'XMLHttpRequest',
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies)
        if res.json().get('code') == 200:
            self.logger.info('获取assetcount成功.')
        else:
            self.logger.warning('获取assetcount失败: %s' % res.content)

    def get_download_gold(self, referer, **kwargs):
        url = 'https://ihr.zhaopin.com/resumemanage/getdownloadgold.do' \
              '?access_token=%s' % self.access_token
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'ihr.zhaopin.com',
            'Origin': 'https://ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }

        data_ = [{
            "resumejlname": "",
            "resumeNo": kwargs['resume_id'] + "_1_1",
            "version": 1,
            "lanType": 1,
            "resumenumber": kwargs['resume_id'],
            "tjString": "3010,1002,601",
            "resumeJobId": 0
        }]
        data = {
            'data': json.dumps(data_, ensure_ascii=False)
        }

        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            proxies=self.proxies)
        if res.json().get('code') == 1:
            self.logger.info('获取download_gold成功.')
        else:
            self.logger.warning('获取download_gold失败: %s' % res.content)

    def get_minilist(self, referer):
        url = 'https://ihr.zhaopin.com/api/job/minilist.do?' \
              'pageIndex=1&pageSize=4000&' \
              'access_token=%s' % self.access_token
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'Cookie': self.cookie,
            'User-Agent': self.user_agent,
            'X-Requested-With': 'XMLHttpRequest',
        }
        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies)
        if res.json().get('code') == 200:
            minilist = res.json().get('data').get('list')
            self.logger.info('获取minilist成功. %s' % len(minilist))
            return minilist
        else:
            self.logger.warning('获取minilist失败: %s' % res.content)

    def get_download(self, referer, **kwargs):
        url = 'https://ihr.zhaopin.com/resumemanage/download.do?access_token' \
              '=%s' % self.access_token

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'ihr.zhaopin.com',
            'Origin': 'https://ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }

        data = {
            'data': json.dumps([{
                "resumejlname": "",
                "resumeNo": kwargs["resume_id"] + "_1_1",
                "version": 1,
                "lanType": 1,
                "resumenumber": kwargs["resume_id"],
                "tjString": "3010,1002,601",
                "resumeJobId": 0,
                "ticketCode": "-1",
                "jobno": kwargs.get('jobno', ''),
                "gold": 30,
                "downtype": 0
            }], ensure_ascii=False)
        }
        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            proxies=self.proxies)
        if res.json().get('code') == 200:
            self.logger.info('下载成功: %s '
                             % res.content)
            return True
        else:
            self.logger.info('下载失败: %s'
                             % res.content)
            return False

    def download_resume(self, **kwargs):

        resource_type = 'RESUME_INBOX'
        self.get_cookie()
        ip = eval(self.auth_kwargs['proxy'])['ip']
        port = eval(self.auth_kwargs['proxy'])['port']

        self.proxies = {
            'http': 'http://%s:%s' % (ip, port),
            'https': 'https://%s:%s' % (ip, port),
        }

        url = 'https://ihr.zhaopin.com/api/redirect.do?' \
              'searchresume=1&resumeNo=%s_1_1&resumeSource' \
              '=1&rn=%s' % (kwargs['resume_id'], kwargs['resume_id'])
        headers = {
            'Host': 'ihr.zhaopin.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://ihr.zhaopin.com/resumesearch/searchlist/?'
                       'keyword=%E9%94%80%E5%94%AE',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        res = self.html_downloader.download(url=url, headers=headers,
                                            proxies=self.proxies)

        try:
            if res.json().get('code', '') == 6001:
                self.logger.warning('Cookie invalid: %s' % res.content)
                raise ZhiLianResumeException('cookie_invalid')
        except JSONDecodeError:
            pass

        referer = res.url
        self.logger.info('获取referer成功: %s' % referer.encode('utf-8'))
        resume_args = {
            'id': kwargs['resume_id'] + '_1',
            'number': kwargs['resume_id'],
            'valResumeTimeStr': 't' + referer.encode('utf-8').split('&t')[1]
        }
        resume_detail_n = self.get_resume_detail(resume_args)
        if not resume_detail_n:
            self.logger.warning(
                '[%s]获取简历详情失败，下载中断: %s' % (
                    self.auth_kwargs['username'].encode('utf-8'),
                    kwargs['resume_id']))
            raise ZhiLianResumeException('get resume_detail_n failed')

        kwargs['city_code'] = resume_detail_n.get('userDetials').get('cityId')

        resumevali = self.get_downresumevali(referer, **kwargs)
        if resumevali is False:
            resource_type = 'RESUME_SEARCH'
        balance = self.get_balance(referer, **kwargs)
        if balance < 30:
            self.logger.warning(
                '[%s]智联币不足，下载中断: %s' % (
                    self.auth_kwargs['username'].encode('utf-8'),
                    kwargs['resume_id']))
            raise ZhiLianResumeException('balance_not_enough')
        price = self.get_price(referer, **kwargs)
        if price > 30:
            self.logger.warning('[%s]简历价格大于30, 下载中断: %s' % (
                self.auth_kwargs['username'].encode(
                    'utf-8'),
                kwargs['resume_id']))
            raise ZhiLianResumeException('price_out_of_range')
        self.get_assetcount(referer)
        self.get_download_gold(referer, **kwargs)
        minilist = self.get_minilist(referer)
        if minilist:
            kwargs['jobno'] = random.choice(minilist).get('jobNumber')
        if resource_type != 'RESUME_SEARCH':
            if self.get_download(referer, **kwargs) is False:
                self.download_failed(**kwargs)
                self.release_run_status()
                return
        resume_detail_y = self.get_resume_detail(resume_args)
        # self.logger.info(resume_detail_y)
        if resume_detail_y.get('resumeSource').encode('utf-8').lower() == \
                'download':
            resource_type = 'RESUME_INBOX'

        content = json.dumps({'name': '', 'email': '', 'phone': '',
                              'html': resume_detail_y},
                             ensure_ascii=False)
        data = {
            'ChannelType': 'APP',
            'Source': self.source,
            'ResourceType': resource_type,
            'content': content,
            'accountContent': json.dumps(self.auth_kwargs,
                                         ensure_ascii=False,
                                         cls=JsonCustomEncoder),
            'resumeId': resume_detail_y.get('resumeNo'),
            'searchData': '',
            'buyOwner': kwargs.get('buyOwner'),
            'outUserID': kwargs.get('outUserID'),
            'code': 200
        }
        # print data
        self.push_resume(**data)

    def download_failed(self, **kwargs):
        data = {
            'ChannelType': 'APP',
            'Source': self.source,
            'ResourceType': 'RESUME_INBOX',
            'content': '',
            'accountContent': json.dumps(self.auth_kwargs,
                                         ensure_ascii=False,
                                         cls=JsonCustomEncoder),
            'resumeId': '',
            'searchData': '',
            'buyOwner': kwargs.get('buyOwner', ''),
            'outUserID': kwargs.get('outUserID', ''),
            'code': 500
        }
        # print data
        self.push_resume(**data)


def exchange_target_version(obj):
    while True:
        if obj.q_search_account.empty():
            obj.init_search_account(use_type='HUNT')
            time.sleep(60)
            continue

        auth_kwargs = eval(obj.q_search_account.get())
        auth_kwargs['ip'] = eval(auth_kwargs['proxy'])['ip']
        auth_kwargs['port'] = eval(auth_kwargs['proxy'])['port']

        if auth_kwargs['version'] == 10001:
            # obj.logger.info('当前执行版本为: RD2 - ' +
            #                 auth_kwargs['username'].encode('utf-8'))
            obj.logger.info('当前不支持： RD2版本帐号简历搜索 - ' + auth_kwargs[
                'username'].encode('utf-8'))
            runner = exchange_target_version(obj)
        # elif auth_kwargs['version'] == 10003:
        #     obj.logger.info('当前执行版本为: RD5 - ' +
        #                     auth_kwargs['username'].encode('utf-8'))
        #     runner = ResumeZhiLianRd5()
        else:
            obj.logger.info('当前执行版本为: IHR - ' +
                            auth_kwargs['username'].encode('utf-8'))
            runner = ResumeZhiLianCrmIhr()
        runner.auth_kwargs = auth_kwargs
        global RUN_STATUS
        RUN_STATUS[auth_kwargs['username'].encode('utf-8')] = 1

        return runner


def execute_resume_search_test():
    local_setting = {
        'SOURCE': 'ZHI_LIAN',
        'TASK_TYPE': 'HUNT_SEARCH',
        'SAVE_TYPE': 'mns'
    }

    params = {
        'keywords': u'销售',
        'city': u'北京|530',
        'age_start': '',
        'age_end': '',
        'work_years': '',
        'sex': '',
        'degree': '',
        'industry': '',
        'company_name': u'石家庄康诺科技有限公司',
        'use_keywords': True
    }

    runner = ResumeZhiLianCrmIhr(local_setting=local_setting)
    runner.auth_kwargs = {
        'username': 'cdylld',
        'password': '',
        'ip': '',
        'port': ''
    }
    runner.get_cookie()
    resume_list = runner.get_resume_list(page=1, **params)
    resume_id = resume_list[0].get('number')
    runner.logger.info(
        '%s|%s|%s' % (params.get('city').encode('utf-8').split('|')[1],
                      params.get('keywords').encode(
                          'utf-8').split('|')[1], resume_id
                      ))


def execute_resume_search():
    local_setting = {
        'SOURCE': 'ZHI_LIAN',
        'TASK_TYPE': 'HUNT_SEARCH',
        'SAVE_TYPE': 'mns'
    }
    base = ResumeZhiLianCrmIhr(local_setting=local_setting)
    runner = None
    # base.q_search_account.clean()
    while True:
        try:

            hour = datetime.datetime.now().hour
            if hour < 7 or hour >= 21:
                base.logger.info("当前程序不再执行时间段内， sleep...")
                global RUN_STATUS
                RUN_STATUS = {}
                time.sleep(6000)
                continue

            if not runner:
                # 初始化runner
                runner = exchange_target_version(base)

            task_id, param = base.get_task()

            if not task_id:
                continue
            # task_id = '1111'
            # param = {
            #     "count": 1000,
            #     "gender": "",
            #     "keyWord": [
            #         u"销售"
            #     ],
            #     "maxAge": 28,
            #     "maxDegree": 999,
            #     "maxExp": 999,
            #     "minAge": 23,
            #     "minDegree": 999,
            #     "minExp": 999,
            #     "source": "ZHI_LIAN",
            #     "targetJobType": {
            #         "createBy": "python",
            #         "createTime": 1526610326000,
            #         "currentCode": "2153",
            #         "currentName": u"会籍顾问",
            #         "id": 3262,
            #         "mfCode": "050101",
            #         "mfName": u"销售代表",
            #         "parentCode": "4010200",
            #         "parentName": u"销售业务",
            #         "source": "ZHI_LIAN",
            #         "type": "job",
            #         "updateTime": 1526610326000,
            #         "valid": True
            #     },
            #     "targetWorkLocation": {
            #         "createBy": "python",
            #         "createTime": 1526610279000,
            #         "currentCode": "530",
            #         "currentName": u"北京",
            #         "id": 1977,
            #         "mfCode": "8611",
            #         "mfName": u"北京",
            #         "parentCode": "489",
            #         "parentName": u"全国",
            #         "source": "ZHI_LIAN",
            #         "type": "city",
            #         "updateTime": 1526610279000,
            #         "valid": True
            #     }
            # }

            kwargs = {
                'count': param.get('count', 0),
                'keywords': u' '.join(param.get('keyWord', [])),
                'city': param.get('targetWorkLocation').get(
                    'currentName') + u'|' + param.get(
                    'targetWorkLocation').get('currentCode'),
                # 'job_type': param.get('targetJobType').get(
                #     'currentCode'),
                'age_start': param.get('minAge')
                if param.get('minAge') != 999 else '',
                'age_end': param.get('maxAge')
                if param.get('maxAge') != 999 else '',
                'work_years': param.get('minExp')
                if param.get('minExp') != 999 else '',
                'sex': param.get('gender') if param.get('gender', 999) not in (
                    0, 999) else '',
                'degree': param.get('minDegree')
                if param.get('minDegree') != 999 else '',
                'industry': param.get('currentIndustry').get('currentCode')
                if param.get('currentIndustry') else '',
                'use_keywords': True,
                'up_date': 3,
                'origin_search_args': param
            }
            # print json.dumps(kwargs, indent=4, ensure_ascii=False)
            base.logger_prefix = '[%s - %s] ' % (
                kwargs['city'].encode('utf-8').split('|')[0],
                kwargs['keywords'].encode('utf-8').split('|')[0]
            )

            page = 1
            page_limit = int(kwargs.get('count'))/30
            while True:
                try:
                    # awake_flow_no = runner.h_awake_flow_no.hget('ZHI_LIAN')
                    # if runner.h_status.hget(awake_flow_no) == '400':
                    #     runner.logger.info("程序当前处于暂停状态.sleep 60s")
                    #     time.sleep(60)
                    #     continue
                    if page_limit <= page:
                        break
                    runner.resume_search(page=page, **kwargs)
                    page += 1
                    if page > settings.TASK_PAGE_LIMIT:
                        runner.logger.warning('任务页码超限: %s'
                                              % settings.TASK_PAGE_LIMIT)
                        base.update_task(task_id=task_id,
                                         execute_result='task_page_limited')
                        break

                except ZhiLianResumeException as e:
                    if e.value == 'resume_list_empty':
                        runner.logger.info('未返回任何简历.')
                        break
                    elif e.value == 'user_record_limited':
                        runner.logger.warning('帐号使用次数超额了: %s'
                                              % settings.COUNT_LIMITED)
                        runner.release_run_status()
                        # break
                        runner = exchange_target_version(base)
                        runner.logger_prefix = '[%s - %s] ' % (
                            kwargs['city'].encode('utf-8').split('|')[0],
                            kwargs['keywords'].encode('utf-8').split('|')[0]
                        )

                        break
                except AccountLimitedException as e:
                    runner.logger.warning('帐号被限制登录了.开始更换帐号。')
                    # break
                    runner.release_run_status()
                    runner = exchange_target_version(base)
                    runner.logger_prefix = '[%s - %s] ' % (
                        kwargs['city'].encode('utf-8').split('|')[0],
                        kwargs['keywords'].encode('utf-8').split('|')[0]
                    )
                    continue
                except Exception as e:
                    runner.logger.exception(e)
                    runner.release_run_status()
                    runner = exchange_target_version(base)
                    break
            base.update_task(task_id=task_id, execute_result=str(e))
        except Exception as e:
            base.logger.exception(e)


def execute_resume_download_test():
    local_setting = {
        'SOURCE': 'ZHI_LIAN',
        'TASK_TYPE': 'HUNT_DOWNLOAD',
        'SAVE_TYPE': 'mns'
    }
    runner = ResumeZhiLianCrmIhr(local_setting=local_setting)
    runner.auth_kwargs = {
        'username': 'cdylld'
    }
    # cookies = eval(runner.h.hget('ZHI_LIAN|szljxsm'))
    cookies = eval(runner.h.hget('ZHI_LIAN|cdylld'))
    cookie_str = cookie2str(cookies)
    runner.cookie = cookie_str
    params = {
        'keywords': u'java',
        'city': u'北京|530',
        'short_resume_id': 'dT7moL)pC5',
        'company_name': '石家庄康诺科技有限公司',
        'use_keywords': True
    }

    resume_list = runner.get_resume_list(**params)
    if not resume_list:
        return

    for resume in resume_list:
        resume_nummber = resume.get('number')
        if params.get('resume_id') == resume_nummber[:10]:
            # print resume.get('number')
            break
    # runner.access_token = cookies.get('Token')
    # runner.download_resume(**params)


def execute_resume_download():
    local_setting = {
        'SOURCE': 'ZHI_LIAN',
        'TASK_TYPE': 'HUNT_DOWNLOAD',
        'SAVE_TYPE': 'mns'
    }
    base = ResumeZhiLianCrmIhr(local_setting=local_setting)
    runner = None

    while True:
        try:
            hour = datetime.datetime.now().hour
            if hour < 7 or hour >= 21:
                base.logger.info("当前程序不再执行时间段内， sleep...")
                global RUN_STATUS
                RUN_STATUS = {}
                time.sleep(6000)
                continue

            if not runner:
                runner = exchange_target_version(base)

            task_id, param = base.get_task()

            if not task_id:
                continue

            param = param.get('data')
            if not param:
                continue

            # print json.dumps(param, ensure_ascii=False, indent=4)

            kwargs = {
                'short_resume_id': param['resumeId'].encode('utf-8'),
                'keywords': u' '.join(param.get('KeyWord', [])),
                'city': param.get('targetWorkLocation').get(
                    'currentName') + u'|' + param.get(
                    'targetWorkLocation').get('currentCode'),
                # 'desired_job_type': param.get('targetJobType').get(
                #     'currentCode')
                # if param.get('targetJobType') else '',
                'age_start': param.get('minAge'),
                'age_end': param.get('maxAge'),
                'work_years': param.get('exp'),
                'sex': param.get('gender') if param.get('gender', 999) not in (
                    0, 999) else '',
                'degree': param.get('degree'),
                'industry': param.get('currentIndustry').get('currentCode')
                if param.get('currentIndustry') else '',
                'use_keywords': True,
                # 'company_name': param.get('lastCompany'),
                'buyOwner': param.get('buyOwner'),
                'outUserID': param.get('outUserID'),
                'origin_search_args': param
            }
            runner.logger.info(
                json.dumps(kwargs, ensure_ascii=False).encode('utf-8'))
            # exit()
            e = None
            try:
                runner.get_cookie()
                resume_list = runner.get_resume_list(is_download=True, **kwargs)

                find = False
                for resume in resume_list:
                    if kwargs.get('short_resume_id') == resume.get('number')[:10]:
                        kwargs['resume_id'] = resume.get('number').encode('utf-8')
                        find = True
                        break
                if find is False:
                    runner.download_failed(**kwargs)
                    runner.release_run_status()
                    base.update_task(task_id=task_id)
                    continue

                if not kwargs.get('resume_id', ''):
                    exchange_target_version(base)
                    runner.release_run_status()
                    runner.download_failed(**kwargs)
                    base.update_task(task_id=task_id)
                    continue

                base.logger_prefix = '[%s] ' % (
                    kwargs['resume_id'].encode('utf-8')
                )

                runner.download_resume(**kwargs)

            except AccountLimitedException as e:
                runner.logger.warning('帐号被限制登录了.')
                # break
                runner.download_failed(**kwargs)
                runner.release_run_status()
                # runner.logger_prefix = '[%s - %s] ' % (
                #     param['city'].encode('utf-8').split('|')[0],
                #     param['keywords'].encode('utf-8').split('|')[0]
                # )
                break
            except ZhiLianResumeException as e:
                if e.value == 'balance_not_enough':
                    runner.download_failed(**kwargs)
                    runner.release_run_status()
                    break

            except Exception as e:
                runner.logger.exception(e)
                runner.download_failed(**kwargs)
                runner.release_run_status()
                break
            base.update_task(task_id=task_id, execute_result=str(e))
        except Exception as e:
            base.logger.exception(e)


if __name__ == '__main__':
    try:
        worker = sys.argv[1]
    except IndexError:
        print 'Usage: python resume_zhilian_hunt.py [search/download]'
        sys.exit()

    if worker == 'search':
        gevent.joinall([
            gevent.spawn(execute_resume_search) for i in xrange(5)
        ])
        # execute_resume_search()
    elif worker == 'download':
        gevent.joinall([
            gevent.spawn(execute_resume_download) for i in xrange(5)
        ])
        # execute_resume_download()
    else:
        print 'Invalid worker [%s]' % worker

    # execute_resume_search_test()
    # execute_resume_search()
    # execute_resume_download_test()
    # execute_resume_download()
