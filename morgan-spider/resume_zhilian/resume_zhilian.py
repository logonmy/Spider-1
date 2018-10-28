#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: resume_zhilian.py
@create at: 2018-02-28 16:24

这一行开始写关于本文件的说明与解释

抓取条件
帐号： username/password/ip/port/version
搜索条件: city/keywords/degree

搜索限制
单个帐号进入详情页次数： COUNT_LIMITED
单个任务进入搜索页次数： TASK_PAGE_LIMIT
简历去重时间限制： DAY_LIMITED

"""

from __future__ import print_function

from gevent import monkey

monkey.patch_all()
import json
import random
import uuid
import gevent
import time

import datetime
from MySQLdb.cursors import DictCursor
from mf_utils.core import InitCorePlus
from mf_utils.common import cookie2str, datetime2str, str2datetime
from mf_utils.data.RedisHash import RedisHash
from mf_utils.queue.RedisQueue import RedisQueue
from mf_utils.logger import Logger
from mf_utils.extend.dingding_robot import DingDingRobot
from mf_utils.exceptions import MfCookieValidException
from mf_utils.decorates import cls_refresh_cookie
from mf_utils.common import remove_emoji
from create_task import CreateTask, settings
from retrying import retry

from gevent.lock import BoundedSemaphore

sem = BoundedSemaphore(1)

run_status_sem = BoundedSemaphore(1)

REDIS_HOST = '172.16.25.36'
REDIS_PORT = '6379'
REDIS_PASSWORD = ''

COOKIE_CONTROL = {}

# 用于控制单帐号同时只有一个线程使用
RUN_STATUS = {}

LIMIT_MESSAGE_BOX = {}


class AccountLimitedException(MfCookieValidException):
    pass


class ZhiLianResumeException(MfCookieValidException):
    pass


class ResumeZhiLianBase(InitCorePlus):
    def __init__(self, local_setting=None):
        super(ResumeZhiLianBase, self).__init__(
            local_setting=local_setting,
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )
        self.cookie = None
        self.access_token = None
        self.proxies = None
        self.auth_kwargs = None
        self.source = 'ZHI_LIAN'
        self.logger = Logger.timed_rt_logger()
        self.h = RedisHash("cookie_pool",
                           host=REDIS_HOST,
                           port=REDIS_PORT,
                           password=REDIS_PASSWORD)
        self.h_limit = RedisHash("account_limit",
                                 host=REDIS_HOST,
                                 port=REDIS_PORT,
                                 password=REDIS_PASSWORD)
        # detail 黑名单
        self.h_black_list = RedisHash("zhi_lian_resume_back_list",
                                      host=REDIS_HOST,
                                      port=REDIS_PORT,
                                      password=REDIS_PASSWORD)
        # 帐号当天使用次数
        self.h_use_record = RedisHash("zhi_lian_resume_search_use_record",
                                      host=REDIS_HOST,
                                      port=REDIS_PORT,
                                      password=REDIS_PASSWORD)
        # 帐号已达上限标识
        self.h_over_search_limit = RedisHash("zhi_lian_over_search_limit",
                                             host=REDIS_HOST,
                                             port=REDIS_PORT,
                                             password=REDIS_PASSWORD)
        self.q_search_account = RedisQueue("zhi_lian_resume_search_account",
                                           host=REDIS_HOST,
                                           port=REDIS_PORT,
                                           password=REDIS_PASSWORD)
        self.h_status = RedisHash('ZHI_LIAN',
                                  # host='172.16.25.35',
                                  # port='6379',
                                  host='r-2ze95acf94ea4a04.redis.rds.aliyuncs.com',
                                  port='6379',
                                  password='CSQotv3PCL',
                                  db=6)
        self.h_awake_flow_no = RedisHash("awake_flow_no",
                                         host=REDIS_HOST,
                                         port=REDIS_PORT,
                                         password=REDIS_PASSWORD)
        # self.search_db = self.init_mysql(db='spider_search')
        self.mns_handler = self.init_mns(
            endpoint='http://1315265288610488.mns.cn-beijing.aliyuncs.com',
            queue='morgan-queue-resume-raw'
            # queue='morgan-queue-test-resume-raw'
        )
        self.mysql_handler = self.init_mysql()
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) ' \
                          'AppleWebKit/537.36 (KHTML, ' \
                          'like Gecko) Chrome/62.0.3202.62 ' \
                          'Safari/537.36'
        self.robot = DingDingRobot(
            access_token="eb749abfe9080a69da6524b77f589b8f6"
                         "ddbcc182c7a41bf095b095336edb0a1")
        self.robot_login = DingDingRobot(
            access_token="3c7b5bd12b49cfdd5f47f00df7fa9c478"
                         "485254485d567ff6abcbf45927e648a"
        )

    def init_search_account(self, use_type='SEARCH_AWAKE'):
        if sem.locked():
            return

        sem.acquire()
        try:
            self.q_search_account.clean()
            self.logger.info('开始初始化搜索帐号队列')
            if not self.q_search_account.empty():
                self.logger.info('当前队列非空，剩余帐号： %s'
                                 % self.q_search_account.qsize())
                return

            mysql_ = self.init_mysql(
                user='super_reader',
                passwd='nMGZKQIXr4PE8aR2',
                host='rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
                # user='bi_admin',
                # passwd='bi_admin#@1mofanghr',
                # host='10.0.3.52',

                cursorclass=DictCursor,
                cls_singleton=False
            )
            account_list = mysql_.query_by_sql(
                """
                SELECT a.*
                FROM
                  autojob_v2.t_account a
                WHERE
                  EXISTS(
                      SELECT 1
                      FROM autojob_v2.t_account_use_type b
                      WHERE a.id = b.accountId
                            AND b.useType = '%s'
                            AND b.valid=1
                            AND a.valid = 1
                            AND a.status = 1
                            AND a.source = 'ZHI_LIAN'
                  )
                ORDER BY a.id DESC;
                """ % use_type)
            self.logger.info('共匹配到%s个有效帐号' % len(account_list))
            effective_account_list = []
            for account in account_list:
                today = datetime2str(datetime.datetime.now(), '%Y-%m-%d')
                global RUN_STATUS
                if RUN_STATUS.get(account['username'].encode('utf-8')):
                    self.logger.warning('当前帐号 %s 处于执行状态.' % account[
                        'username'].encode('utf-8'))
                    continue

                if self.h_over_search_limit.hget(today + '|' + account[
                    'username'].encode('utf-8')):
                    self.logger.warning('当前帐号 %s 已达上限 %s，当天不再进行搜索.' % (
                        account['username'].encode('utf-8'),
                        self.h_use_record.hget(
                            account['username'].encode(
                                'utf-8') + '|' + today)
                    ))
                    continue

                self.q_search_account.put(account)
                effective_account_list.append(account)

            self.logger.info('初始化搜索帐号队列完毕 %s'
                             % len(effective_account_list))
            sem.release()

        except Exception as e:
            self.logger.exception('初始化搜索帐号队列失败: ' + str(e))
            sem.release()

    def start_push_task(self):
        if sem.locked():
            return
        try:
            sem.acquire()
            self.logger.info('开始推送智联唤醒任务.')
            act = CreateTask()
            act.create_task_from_mysql(use_keywords=True)
            sem.release()
        except Exception as e:
            self.logger.exception(e)
            sem.release()

    def release_run_status(self):
        global RUN_STATUS
        RUN_STATUS[self.auth_kwargs['username'].encode('utf-8')] = 0
        self.logger.info('将帐号 %s 置为非运行状态' %
                         self.auth_kwargs['username'].encode('utf-8'))

    def check_limit(self, count):
        if self.auth_kwargs['username'].encode('utf-8') in \
                settings.SAFE_LIMITED:
            if count >= settings.SAFE_COUNT_LIMITED:
                return True
            return False

        if random.randint(1, 200) == 1:
            # 0.5%的几率检查是否达到 最小搜索上限
            if count >= settings.COUNT_LIMITED_L:
                return True
        if count >= settings.COUNT_LIMITED:
            return True
        return False

    def get_cookie(self):
        count = self.h_limit.hget(
            self.source + '|' + self.auth_kwargs['username'].encode('utf-8'))
        if not count:
            pass
        elif int(count) >= 5:
            self.logger.warning(
                "帐号%s 被限制登录" %
                self.auth_kwargs['username'].encode('utf-8')
            )
            count = int(count)
            count += 1
            self.h_limit.hset(
                self.source + '|' + self.auth_kwargs['username'].encode(
                    'utf-8'), count)

            if int(count) == 6:
                self.robot_login.send_markdown(
                    title="智联简历搜索",
                    content="#### 智联简历搜索帐号被禁用.\n"
                            "- 帐号： %s\n"
                            "- 密码： %s\n"
                            "- 代理： %s\n\n"
                            % (
                                self.auth_kwargs['username'].encode(
                                    'utf-8'),
                                self.auth_kwargs['password'].encode(
                                    'utf-8'),
                                self.auth_kwargs['ip'].encode(
                                    'utf-8') + ':' +
                                self.auth_kwargs['port'].encode('utf-8'))
                )

            raise AccountLimitedException('account_limited')

        cookies = self.h.hget(
            self.source + '|' + self.auth_kwargs['username'].encode('utf-8'))

        # 调用登录接口进行登录
        # if not cookies:
        #     self.auth_kwargs['user_agent'] = self.user_agent
        #
        #     self.logger.info(
        #         "开始登录：%s %s %s %s" % (
        #             self.auth_kwargs['username'].encode('utf-8'),
        #             self.auth_kwargs['password'].encode('utf-8'),
        #             self.auth_kwargs['ip'].encode('utf-8'),
        #             self.auth_kwargs['port'].encode('utf-8')))
        #     url = 'http://127.0.0.1:5000/zhilian_login/' \
        #           '?user_name=%s&password' \
        #           '=%s&ip=%s&port=%s&user_agent=%s' % (
        #               self.auth_kwargs['username'].encode('utf-8'),
        #               self.auth_kwargs['password'].encode('utf-8'),
        #               self.auth_kwargs['ip'].encode('utf-8'),
        #               self.auth_kwargs['port'].encode('utf-8'),
        #               self.auth_kwargs['user_agent'].encode('utf-8')
        #           )
        #
        #     res = self.html_downloader.download(url, timeout=180)
        #     code = res.json().get("code")
        #     # code = 500
        #     if not code == 200:
        #         self.logger.warning(
        #             "登录失败: %s" % (
        #                 self.auth_kwargs['username'].encode('utf-8'))
        #         )
        #
        #         count = self.h_limit.hget(self.source+'|'+self.auth_kwargs['username'].encode('utf-8'))
        #         if not count:
        #             count = 1
        #         else:
        #             count = int(count)
        #             count += 1
        #         self.h_limit.hset(self.source+'|'+self.auth_kwargs['username'].encode('utf-8'), count)
        #
        #         return None
        #
        #     cookies = res.json().get('cookies')
        #     self.h.hset(self.source+'|'+self.auth_kwargs['username'].encode('utf-8'), cookies)
        #     self.h_limit.hset(self.source+'|'+self.auth_kwargs['username'].encode('utf-8'), 0)
        #     self.cookie = cookie2str(cookies)
        #     self.access_token = cookies['Token']
        #     return cookies

        # 强制
        if not cookies:
            self.cookie = ''
            self.h_limit.hset(
                self.source + '|' + self.auth_kwargs['username'].encode(
                    'utf-8'), 5)
            return

        else:
            self.cookie = cookie2str(eval(cookies))
            self.access_token = eval(cookies).get('Token', '')
            if not self.access_token:
                raise AccountLimitedException('account_limited')
            return eval(cookies)

    def set_cookie_invalid(self):
        self.h.hset(
            self.source + '|' + self.auth_kwargs['username'].encode('utf-8'),
            '')
        # global COOKIE_CONTROL
        # last_invalid_time = COOKIE_CONTROL.get(self.auth_kwargs['username'])
        # if not last_invalid_time:
        #     COOKIE_CONTROL[self.auth_kwargs['username']] = datetime.datetime.now()
        #     self.h.hset(self.source+'|'+self.auth_kwargs['username'].encode('utf-8'), '')
        # else:
        #     if datetime.datetime.now().minute - last_invalid_time.minute > 5:
        #         COOKIE_CONTROL[
        #             self.auth_kwargs['username']] = datetime.datetime.now()
        #         self.h.hset(self.source+'|'+self.auth_kwargs['username'].encode('utf-8'), '')
        #     else:
        #         self.logger.info('%s距离上次失效帐号已达到%s分钟.' % (
        #             self.auth_kwargs['username'].encode('utf-8'), 5))

    def update_status(self, **kwargs):
        try:
            url = self.common_settings.BACK_ENDS + \
                  '/task/searchAwake/update.json'
            data = {
                'flowNo': kwargs['flow_no'],
                'source': self.common_settings.SOURCE,
                'status': kwargs['status'],
                'message': ''
            }
            res = self.html_downloader.download(url, method='POST', data=data)
            if res.json().get('code') == 200:
                self.logger.info('任务状态更新成功.')
            else:
                self.logger.warning('任务更新失败： %s' % str(res.json()))
        except Exception as e:
            self.logger.exception('任务状态更新异常： %s' % str(e))

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

            mysql_1 = self.init_mysql(
                user='bi_admin',
                passwd='bi_admin#@1mofanghr',
                host='172.16.25.1',
                # user='bi_admin',
                # passwd='bi_admin#@1mofanghr',
                # host='10.0.3.52',

                cursorclass=DictCursor,
                cls_singleton=False
            )
            sql = '''
                 insert into spider.resume_awake_record_no_repeat (source, 
                 position, 
                 city,
                  raw_id, create_time, username) VALUES ('ZHI_LIAN', %s, 
                  %s, %s, now(), %s)
                 '''
            value = (search_args['keywords'].split('|')[0], search_args[
                'city'].split('|')[0], resume_id, self.auth_kwargs['username'])
            mysql_1.save(sql, value)
            del mysql_1

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
            resume_uuid = str(uuid.uuid1())
            content = json.dumps({'name': '', 'email': '', 'phone': '',
                                  'html': resume_detail},
                                 ensure_ascii=False)
            sql = '''insert into spider_search.resume_raw (source, content, 
            createBy, 
            trackId, createtime, email, emailJobType, emailCity, subject) values 
            (%s, %s, "python", %s, now(), %s, %s, %s, %s)'''
            sql_value = (self.common_settings.SOURCE, content, resume_uuid,
                         self.auth_kwargs['username'], search_args['keywords'],
                         search_args['city'],
                         str(resume_detail.get('resumeNo')))

            resume_update_time = ''
            msg_data = {
                "channelType": "APP",
                "content": {
                    "content": content,
                    "id": '',
                    "createBy": "python",
                    "createTime": int(time.time() * 1000),
                    "ip": '',
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": resume_update_time,
                    "source": self.common_settings.SOURCE,
                    "trackId": str(resume_uuid),
                    "avatarUrl": '',
                    "email": self.auth_kwargs['username'],
                    'emailJobType': search_args['keywords'],
                    'emailCity': search_args['city'],
                    'subject': str(resume_detail.get('resumeNo'))
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_SEARCH_AWAKE",
                "source": self.common_settings.SOURCE,
                "trackId": str(resume_uuid),
                'traceID': str(resume_uuid),
                'callSystemID': self.common_settings.CALL_SYSTEM_ID,
            }
            # self.mysql_handler.save(sql=sql, data=sql_value)
            res = self.save_data(sql=sql, data=sql_value, msg_data=msg_data)

            if res:
                count += 1
                self.h_use_record.hset(self.auth_kwargs['username'] + today,
                                       count)
                mysql_ = self.init_mysql(
                    user='bi_admin',
                    passwd='bi_admin#@1mofanghr',
                    host='172.16.25.1',
                    # user='bi_admin',
                    # passwd='bi_admin#@1mofanghr',
                    # host='10.0.3.52',

                    cursorclass=DictCursor,
                    cls_singleton=False
                )
                sql = '''
                    insert into spider.resume_awake_record (source, position, city,
                     raw_id, create_time, username) VALUES ('ZHI_LIAN', %s, 
                     %s, %s, now(), %s)
                    '''
                value = (search_args['keywords'].split('|')[0], search_args[
                    'city'].split('|')[0], res, self.auth_kwargs['username'])
                mysql_.save(sql, value)
                del mysql_

            time.sleep(random.randint(3, 5))


class ResumeZhiLianRd2(ResumeZhiLianBase):
    def __init__(self, local_setting=settings.rd2_settings):
        super(ResumeZhiLianRd2, self).__init__(local_setting=local_setting)

    def get_resume_list(self, page=1, **search_args):
        url = 'https://rdsearch.zhaopin.com/Home/ResultForCustom?' \
              'SF_1_1_6=530&SF_1_1_27=0&orderBy=DATE_MODIFIED,1' \
              '&exclude=1&pageSize=60&pageIndex=%s' % page
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'rdsearch.zhaopin.com',
            'Referer': 'https://rdsearch.zhaopin.com/Home/ResultForCustom?'
                       'SF_1_1_6=530&SF_1_1_27=0&orderBy=DATE_MODIFIED,'
                       '1&exclude=1&pageSize=60&pageIndex=%s' % (
                               page - 1),
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies)
        print(res.status_code, res.content)

        print(self.cookie)


class ResumeZhiLianRd5(ResumeZhiLianBase):
    def __init__(self, local_setting=settings.rd5_settings):
        super(ResumeZhiLianRd5, self).__init__(local_setting=local_setting)

    @retry(stop_max_attempt_number=5)
    @cls_refresh_cookie
    def get_resume_list(self, page=1, **search_args):
        """
        获取简历列表页
        搜索条件： 关键词/所在地/年龄20-35/学历/最近三天SF_1_1_7
        :param page:
        :param search_args:
        :return:
        """

        if search_args['use_keywords'] is False:
            self.logger.info('采用职能进行搜索.')
            url = 'https://ihrsearch.zhaopin.com/Home/ResultForCustom?' \
                  'SF_1_1_2=%s&' \
                  'SF_1_1_18=%s&' \
                  'orderBy=DATE_MODIFIED,1&' \
                  'pageSize=30&' \
                  'SF_1_1_27=0&' \
                  'SF_1_1_5=%s,16&' \
                  'SF_1_1_8=18,30&' \
                  'SF_1_1_7=1,9&' \
                  'exclude=1&pageIndex=%s' \
                  % (search_args['keywords'].split('|')[1].encode('utf-8'),
                     search_args['city'].split('|')[1].encode('utf-8'),
                     search_args['degree'],
                     page)
            referer = 'https://ihrsearch.zhaopin.com/Home/ResultForCustom?' \
                      'SF_1_1_2=%s&' \
                      'SF_1_1_18=%s&' \
                      'orderBy=DATE_MODIFIED,1&' \
                      'pageSize=30&' \
                      'SF_1_1_27=0&' \
                      'SF_1_1_5=%s,16&' \
                      'SF_1_1_8=18,30&' \
                      'SF_1_1_7=1,9&' \
                      'exclude=1&pageIndex=%s' \
                      % (search_args['keywords'].split('|')[1].encode('utf-8'),
                         search_args['city'].split('|')[1].encode('utf-8'),
                         search_args['degree'],
                         page)

        else:
            self.logger.info('采用关键词进行搜索.')
            url = 'https://ihrsearch.zhaopin.com/Home/ResultForCustom?' \
                  'SF_1_1_1=%s&' \
                  'SF_1_1_18=%s&' \
                  'orderBy=DATE_MODIFIED,1&' \
                  'pageSize=30&' \
                  'SF_1_1_27=0&' \
                  'SF_1_1_5=%s,16&' \
                  'SF_1_1_8=18,30&' \
                  'SF_1_1_7=1,9&' \
                  'exclude=1&pageIndex=%s' \
                  % (search_args['keywords'].split('|')[0].encode('utf-8'),
                     search_args['city'].split('|')[1].encode('utf-8'),
                     search_args['degree'],
                     page)
            referer = 'https://ihrsearch.zhaopin.com/Home/ResultForCustom?' \
                      'SF_1_1_1=%s&' \
                      'SF_1_1_18=%s&' \
                      'orderBy=DATE_MODIFIED,1&' \
                      'pageSize=30&' \
                      'SF_1_1_27=0&' \
                      'SF_1_1_5=%s,16&' \
                      'SF_1_1_8=18,30&' \
                      'SF_1_1_7=1,9&' \
                      'exclude=1&pageIndex=%s' \
                      % (search_args['keywords'].split('|')[0].encode('utf-8'),
                         search_args['city'].split('|')[1].encode('utf-8'),
                         search_args['degree'],
                         page)

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'ihrsearch.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies,
                                            allow_redirects=False)

        if res.status_code == 302:
            self.logger.warning('cookie失效了')
            self.set_cookie_invalid()
            raise MfCookieValidException('cookie_invalid')

        try:
            soups = self.html_parser.parser(
                res.content).find('form', attrs={'name': 'frmResult'}).find(
                'tbody').find_all('tr', class_='info')
            soups1 = self.html_parser.parser(
                res.content).find('form', attrs={'name': 'frmResult'}).find(
                'tbody').find_all('tr', valign='middle')
        except Exception as e:
            self.logger.exception('获取resume_list失败: %s' % str(e))
            return []
        resume_list = []
        for index, soup in enumerate(soups):
            # global DAY_LIMITED
            # DAY_LIMITED = 5
            # limited_day = datetime.datetime.now() - datetime.timedelta(
            #     days=4
            # )
            if datetime.datetime.now().isoweekday() == 1:
                # 周一
                # global DAY_LIMITED
                # DAY_LIMITED = 5
                # limited_day = datetime.datetime.now() - datetime.timedelta(
                #     days=4)
                global DAY_LIMITED
                DAY_LIMITED = 2
                limited_day = datetime.datetime.now() - datetime.timedelta(
                    days=1
                )
            else:
                global DAY_LIMITED
                DAY_LIMITED = 2
                limited_day = datetime.datetime.now() - datetime.timedelta(
                    days=1
                )

            if str2datetime(soups1[index].find_all('td')[-1].text.encode(
                    'utf-8'), '%y-%m-%d').date() < limited_day.date():
                self.logger.warning('匹配到%s天前的简历，执行跳过操作.' % DAY_LIMITED)
                break
            resume_item = dict()
            resume_item['resumeNo'] = soup.find('a').get('resumeurlpart')
            resume_item['t'] = soup.find('a').get('t')
            resume_item['k'] = soup.find('a').get('k')
            resume_list.append(resume_item)
        self.logger.info('page: %s, 总计获取到简历%s份, 搜索条件[%s, %s]'
                         % (page, len(resume_list),
                            search_args['keywords'].encode('utf-8'),
                            search_args['city'].encode('utf-8')))
        return resume_list

    @retry(stop_max_attempt_number=5)
    @cls_refresh_cookie
    def get_resume_detail(self, resume_args):
        url = 'https://ihr.zhaopin.com/resumesearch/getresumedetial.do?' \
              'access_token=46e7d16be97a4f3ba9ca7beb2c42f8a8&' \
              'resumeNo=%s&searchresume=1&resumeSource=1&keyword=java' \
              '&t=%s&k=%s&v=0&version=1' \
              '&openFrom=1' % (resume_args['resumeNo'], resume_args['t'],
                               resume_args['k'])
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': url,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies)
        if res.json().get('code') == 6001:
            self.logger.info(self.logger_prefix + 'cookie失效了')
            self.set_cookie_invalid()
            raise MfCookieValidException('cookie_invalid')

        if res.json().get('code') != 1:
            self.logger.info(self.logger_prefix + '获取简历详情失败: %s - %s' % (
                self.auth_kwargs['username'].encode('utf-8'),
                resume_args.get('resumeNo').encode('utf-8')[:-4]
            ))
            return
        self.logger.info(self.logger_prefix + '获取简历详情成功: %s - %s' % (
            self.auth_kwargs['username'].encode('utf-8'),
            resume_args.get('resumeNo').encode('utf-8')[:-4]
        ))
        return res.json().get('data')


class ResumeZhiLianIhr(ResumeZhiLianBase):
    def __init__(self, local_setting=settings.ihr_settings):
        super(ResumeZhiLianIhr, self).__init__(local_setting=local_setting)

    @retry(stop_max_attempt_number=5)
    @cls_refresh_cookie
    def get_resume_list(self, page=1, is_download=False, **search_args):
        """
        获取简历列表页
        搜索条件： 关键词/所在地/年龄20-35/学历/最近三天upDate
        :param page:
        :param search_args:
        :return:
        """
        url = 'https://ihr.zhaopin.com/resumesearch/search.do?' \
              'access_token=%s' % self.access_token
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
            'Referer': 'https://ihr.zhaopin.com/resumesearch/search/',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }

        data = {
            'keywords': search_args['keywords'].split('|')[0].encode('utf-8'),
            'startNum': (page - 1) * 30,
            'rowsCount': '30',
            'resumeGrade': '',
            'sortColumnName': 'sortUpDate',
            'sortColumn': 'sortUpDate desc',
            'onlyHasImg': 'false',
            'anyKeyWord': 'false',
            'hopeWorkCity': search_args['city'].split('|')[1].encode('utf-8'),
            'ageStart': search_args.get('age_start', '18'),
            'ageEnd': search_args.get('age_end', '30'),
            'workYears': search_args.get('work_years', ''),
            'liveCity': search_args.get('live_city', ''),
            'sex': search_args.get('sex', ''),
            'edu': search_args.get('degree', '5'),
            'upDate': search_args.get('up_date', ''),  # 默认搜索最近三天
            'companyName': search_args.get('company_name', ''),
            'jobType': '',
            'desiredJobType': search_args.get('desired_job_type', ''),
            'industry': search_args.get('industry', ''),
            'desiredIndustry': '',
            'careerStatus': '',
            'desiredSalary': '',
            'langSkill': '',
            'hukouCity': '',
            'major': '',
            'onlyLastWork': 'false',
        }
        # print(json.dumps(data, ensure_ascii=False, indent=4))
        if search_args['use_keywords'] is False:
            data['desiredJobType'] = search_args['keywords'].split('|')[1]
            self.logger.info('采用职能进行搜索.')
        else:
            self.logger.info('采用关键词进行搜索')

        res = self.html_downloader.download(url, method='POST', data=data,
                                            headers=headers,
                                            proxies=self.proxies)
        # self.logger.info('搜索返回 %s' % res.json())
        if res.json().get('code') == 6001:
            self.logger.info(self.logger_prefix + 'cookie失效了')
            self.set_cookie_invalid()
            raise MfCookieValidException('cookie_invalid')

        if res.json().get('code') == 808:
            self.logger.warning(self.logger_prefix + res.json().get(
                'message').encode('utf-8'))
            today = datetime2str(datetime.datetime.now(), '%Y-%m-%d')
            self.h_over_search_limit.hset(today + '|' + self.auth_kwargs[
                'username'].encode('utf-8'), 1)
            # 当日搜索大库简历已达上限

            global LIMIT_MESSAGE_BOX
            if not LIMIT_MESSAGE_BOX.get(self.auth_kwargs['username'].encode(
                    'utf-8'), ''):
                LIMIT_MESSAGE_BOX[self.auth_kwargs['username'].encode(
                    'utf-8')] = 1
                self.robot_login.send_markdown(
                    title="智联简历搜索",
                    content="#### 智联简历当日关键词搜索量已达上限.\n"
                            "- 帐号： %s\n"
                            "- 密码： %s\n"
                            "- 代理： %s\n"
                            "- 达到上限账号总数： %s\n"
                            % (
                                self.auth_kwargs['username'].encode(
                                    'utf-8'),
                                self.auth_kwargs['password'].encode(
                                    'utf-8'),
                                self.auth_kwargs['ip'].encode(
                                    'utf-8') + ':' +
                                self.auth_kwargs['port'].encode('utf-8'),
                                len(LIMIT_MESSAGE_BOX)
                            )
                )

            raise ZhiLianResumeException('user_record_limited')

        try:
            resume_list = res.json().get('results')
            if not resume_list:
                raise Exception
        except Exception as e:
            self.logger.exception('获取list失败： %s | %s'
                                  % (str(e), res.content))
            return []

        resume_accept_list = []
        for resume in resume_list:
            # global DAY_LIMITED
            # DAY_LIMITED = 5
            # limited_day = datetime.datetime.now() - datetime.timedelta(
            #     days=4
            # )
            if is_download is False:
                if datetime.datetime.now().isoweekday() == 1:
                    # 周一
                    # global DAY_LIMITED
                    # DAY_LIMITED = 5
                    # limited_day = datetime.datetime.now() - datetime.timedelta(
                    #     days=4)
                    global DAY_LIMITED
                    DAY_LIMITED = 2
                    limited_day = datetime.datetime.now() - datetime.timedelta(
                        days=1
                    )
                else:
                    global DAY_LIMITED
                    DAY_LIMITED = 2
                    limited_day = datetime.datetime.now() - datetime.timedelta(
                        days=1
                    )

                if str2datetime(resume.get('modifyDate'),
                                '%Y-%m-%d').date() < limited_day.date():
                    self.logger.warning('匹配到%s天前的简历，执行跳过操作.' % DAY_LIMITED)
                    break
            resume_accept_list.append(resume)

        self.logger.info('page: %s, 总计获取到简历%s份, 搜索条件[%s, %s]'
                         % (page, len(resume_accept_list),
                            search_args['keywords'].encode('utf-8'),
                            search_args['city'].encode('utf-8')))
        return resume_accept_list

    def get_resume_detail(self, resume_args):
        url = 'http://ihr.zhaopin.com/resumesearch/getresumedetial.do' \
              '?access_token=%s&resumeNo=%s_1&searchresume=1&resumeSource=1' \
              '&%s' % (self.access_token,
                       resume_args.get('id'),
                       resume_args.get('valResumeTimeStr'))

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'ihr.zhaopin.com',
            'Pragma': 'no-cache',
            'Referer': url,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies)
        if res.json().get('code') == 6001:
            self.logger.info('cookie失效了')
            self.set_cookie_invalid()
            raise MfCookieValidException('cookie_invalid')

        if res.json().get('code') != 1:
            self.logger.info(self.logger_prefix + '获取简历详情失败: %s - %s' % (
                self.auth_kwargs['username'].encode('utf-8'),
                resume_args.get('number').encode('utf-8')
            ))
            return
        self.logger.info(self.logger_prefix + '获取简历详情成功: %s - %s' % (
            self.auth_kwargs['username'].encode('utf-8'),
            resume_args.get('number').encode('utf-8')
        ))
        return res.json().get('data')


def exchange_target_version(obj):
    while True:
        if obj.q_search_account.empty():
            obj.init_search_account()
            time.sleep(5)
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
        elif auth_kwargs['version'] == 10003:
            obj.logger.info('当前执行版本为: RD5 - ' +
                            auth_kwargs['username'].encode('utf-8'))
            runner = ResumeZhiLianRd5()
        else:
            obj.logger.info('当前执行版本为: IHR - ' +
                            auth_kwargs['username'].encode('utf-8'))
            runner = ResumeZhiLianIhr()
        runner.auth_kwargs = auth_kwargs
        global RUN_STATUS
        RUN_STATUS[auth_kwargs['username'].encode('utf-8')] = 1

        return runner


def execute_resume_search():
    base = ResumeZhiLianBase(local_setting={
        'TASK_TYPE': 'RESUME_FETCH',
        'SOURCE': 'ZHI_LIAN'
    })

    runner = None

    while True:
        try:

            hour = datetime.datetime.now().hour
            if hour < 7 or hour >= 22:
                base.logger.info("当前程序不再执行时间段内， sleep...")
                global RUN_STATUS, LIMIT_MESSAGE_BOX
                RUN_STATUS = {}
                LIMIT_MESSAGE_BOX = {}
                runner = None
                time.sleep(6000)
                continue

            if not runner:
                # 初始化runner
                runner = exchange_target_version(base)

            task_id, param = base.get_task()

            if not task_id:
                base.start_push_task()
                continue

            # Test
            # runner = ResumeZhiLianIhr()
            # runner.preview_settings()
            # runner.auth_kwargs = {
            #     "username": 'taopusol',
            #     "password": 'tao89010',
            #     "port": "3128",
            #     "ip": "39.106.249.207",
            #     "proxy": '{"port":"3128","ip":"39.106.249.207"}',
            #     "version": 10002
            # }

            # Test
            param['up_date'] = 3
            runner.logger_prefix = '[%s - %s] ' % (
                param['city'].encode('utf-8').split('|')[0],
                param['keywords'].encode('utf-8').split('|')[0]
            )

            page = 1
            while True:
                try:
                    awake_flow_no = runner.h_awake_flow_no.hget('ZHI_LIAN')
                    if runner.h_status.hget(awake_flow_no) == '400':
                        runner.logger.info("程序当前处于暂停状态.sleep 60s")
                        time.sleep(60)
                        continue

                    runner.resume_search(page=page, **param)
                    page += 1
                    if page > settings.TASK_PAGE_LIMIT:
                        runner.logger.warning('任务页码超限: %s' %
                                              settings.TASK_PAGE_LIMIT)
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
                            param['city'].encode('utf-8').split('|')[0],
                            param['keywords'].encode('utf-8').split('|')[0]
                        )

                        break
                except AccountLimitedException as e:
                    runner.logger.warning('帐号被限制登录了.开始更换帐号。')
                    # break
                    runner.release_run_status()
                    runner = exchange_target_version(base)
                    runner.logger_prefix = '[%s - %s] ' % (
                        param['city'].encode('utf-8').split('|')[0],
                        param['keywords'].encode('utf-8').split('|')[0]
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


def execute_create_task():
    base = ResumeZhiLianBase(local_setting={
        'TASK_TYPE': 'SEARCH_AWAKE',
        'SOURCE': 'ZHI_LIAN',
        # 'BACK_ENDS': 'http://10.0.4.199:5000/api/autojob'
        'BACK_ENDS': 'http://172.16.25.8:5000/api/autojob'
    })
    # base.init_search_account()

    while True:
        try:
            task_id, param = base.get_task()
            if not task_id:
                continue

            flow_no = param.get('flowNo')
            kwargs = {
                'flow_no': flow_no,
                'status': 300,
            }
            base.update_status(**kwargs)
            base.h_awake_flow_no.hset('ZHI_LIAN', flow_no)
            base.logger.info('当前flow_no为： %s' % flow_no.encode('utf-8'))

            creator = CreateTask()
            creator.create_task_from_mysql(use_keywords=True)
            base.update_task(task_id=task_id)
            base.logger.info('任务生成完毕.')
        except Exception as e:
            base.logger.exception(str(e))


def push_to_mns():
    base = ResumeZhiLianBase(local_setting={
        'TASK_TYPE': 'RESUME_FETCH',
        'SOURCE': 'ZHI_LIAN'
    })
    base.mysql_handler = base.init_mysql(cursorclass=DictCursor)

    sql = '''
    select * from spider_search.resume_raw WHERE id in (
    39491466
    ) and rdCreateTime>=curdate()
    '''

    data_lst = base.mysql_handler.query_by_sql(sql)
    base.logger.info("获取简历成功: %s" % len(data_lst))

    for data in data_lst:
        try:
            msg_data = {
                "channelType": "APP",
                "content": {
                    "content": data['content'],
                    "id": data['id'],
                    "createBy": "python",
                    "createTime": str(data['createTime']),
                    "ip": '',
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": str(data['resumeUpdateTime']),
                    "source": data['source'],
                    "trackId": str(data['trackId']),
                    "avatarUrl": '',
                    "email": data['email'],
                    'emailJobType': data['emailJobType'],
                    'emailCity': data['emailCity'],
                    'subject': data['subject']
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_SEARCH_AWAKE",
                "source": data['source'],
                "trackId": data['trackId'],
                'traceID': data['trackId'],
                'callSystemID': 'resume_awake_search',
            }
            dumps = json.dumps(msg_data, ensure_ascii=False).encode('utf-8')
            dumps = remove_emoji(dumps)
            base.mns_handler.save(dumps)
            base.logger.info('推送成功： %s' % data['id'])
        except Exception as e:
            base.logger.exception(str(e))


if __name__ == '__main__':
    # execute_resume_search()
    # push_to_mns()
    gevent.joinall(
        [
            gevent.spawn(execute_resume_search)
            for i in xrange(settings.COROUTINE_NUM)
        ].append(gevent.spawn(execute_create_task)))
