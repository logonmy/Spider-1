#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: resume_51job.py
@create at: 2018-03-05 10:02

这一行开始写关于本文件的说明与解释

抓取条件
帐号： username/password/ip/port/version
搜索条件: city/function

搜索限制
单个帐号进入详情页次数： COUNT_LIMITED
单个任务进入搜索页次数： TASK_PAGE_LIMIT
简历去重时间限制： DAY_LIMITED

"""

from __future__ import print_function

import os

import PyV8
from gevent import monkey

monkey.patch_all()

import gevent
import random
import re
import time
import uuid
import datetime
from MySQLdb.cursors import DictCursor
from mf_utils.core import InitCorePlus
from mf_utils.logger import Logger
from mf_utils.data.RedisHash import RedisHash
from mf_utils.queue.RedisQueue import RedisQueue
from mf_utils.common import cookie2str, str2datetime, datetime2str
from mf_utils.extend.dingding_robot import DingDingRobot
from mf_utils.exceptions import MfCookieValidException
from mf_utils.decorates import cls_refresh_cookie, cls_catch_exception
from mf_utils.identify import Identify
from create_task import CreateTask, settings
from conf.settings import FIVE_ONE_JS_FUNC
from retrying import retry
from gevent.lock import BoundedSemaphore

sem = BoundedSemaphore(1)

REDIS_HOST = '172.16.25.36'
REDIS_PORT = '6379'
REDIS_PASSWORD = ''

RUN_STATUS = {}
LOGIN_STATUS = {}
EXCEPTION_COUNT = 0


class AccountLimitedException(MfCookieValidException):
    pass


class FiveOneResumeException(MfCookieValidException):
    pass


class Resume51job(InitCorePlus):
    def __init__(self, local_setting=settings.project_settings):
        super(Resume51job, self).__init__(
            local_setting=local_setting,
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )
        self.cookie = None
        self.proxies = None
        self.auth_kwargs = None
        self.source = 'FIVE_ONE'
        self.logger = Logger.timed_rt_logger()
        self.h = RedisHash("cookie_pool",
                           host=REDIS_HOST,
                           port=REDIS_PORT,
                           password=REDIS_PASSWORD)
        self.h_limit = RedisHash("account_limit",
                                 host=REDIS_HOST,
                                 port=REDIS_PORT,
                                 password=REDIS_PASSWORD)
        self.h_black_list = RedisHash("five_one_resume_back_list",
                                      host=REDIS_HOST,
                                      port=REDIS_PORT,
                                      password=REDIS_PASSWORD)
        self.h_use_record = RedisHash("five_one_resume_search_use_record",
                                      host=REDIS_HOST,
                                      port=REDIS_PORT,
                                      password=REDIS_PASSWORD)
        self.h_search_empty_times = RedisHash("five_one_resume_search_empty_times",
                                              host=REDIS_HOST,
                                              port=REDIS_PORT,
                                              password=REDIS_PASSWORD)
        self.q_search_account = RedisQueue("five_one_resume_search_account",
                                           host=REDIS_HOST,
                                           port=REDIS_PORT,
                                           password=REDIS_PASSWORD)
        self.h_status = RedisHash('FIVE_ONE',
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
        self.robot_login = DingDingRobot(
            access_token="3c7b5bd12b49cfdd5f47f00df7fa9c478"
                         "485254485d567ff6abcbf45927e648a"
        )

    def release_run_status(self):
        global RUN_STATUS
        RUN_STATUS[self.auth_kwargs['username'].encode('utf-8')] = 0
        self.logger.info('将帐号 %s 置为非运行状态' %
                         self.auth_kwargs['username'].encode('utf-8'))

    def get_cookie(self):
        count = self.h_limit.hget(
            self.source + '|' + self.auth_kwargs['username'].encode('utf-8'))
        if not count:
            count = 0
        else:
            count = int(count)
        count += 1

        # 回写账号重试次数
        self.h_limit.hset(
            self.source + '|' + self.auth_kwargs['username'].encode(
                'utf-8'), count)

        cookies = self.h.hget(
            self.source + '|' + self.auth_kwargs['username'].encode('utf-8'))

        # 强制禁用账号
        if not cookies:
            count = 5

        # 调用登录接口进行登录
        # if count == 5:
        #     self.auth_kwargs['user_agent'] = self.user_agent
        #
        #     self.logger.info(
        #         "开始登录：%s %s %s %s %s" % (
        #             self.auth_kwargs['username'].encode('utf-8'),
        #             self.auth_kwargs['password'].encode('utf-8'),
        #             self.auth_kwargs['account_name'].encode(
        #                 'utf-8'),
        #             self.auth_kwargs['ip'].encode('utf-8'),
        #             self.auth_kwargs['port'].encode('utf-8')))
        #     url = 'http://172.16.25.36:5000/fiveone_login/' \
        #           '?username=%s&password' \
        #           '=%s&ip=%s&port=%s&user_agent=%s&account_name=%s' % (
        #               self.auth_kwargs['username'].encode('utf-8'),
        #               self.auth_kwargs['password'].encode('utf-8'),
        #               self.auth_kwargs['ip'].encode('utf-8'),
        #               self.auth_kwargs['port'].encode('utf-8'),
        #               self.auth_kwargs['user_agent'].encode('utf-8'),
        #               self.auth_kwargs['account_name'].encode('utf-8')
        #           )
        #
        #     res = self.html_downloader.download(url, timeout=180)
        #
        #     code = res.json().get("code")
        #     # code = 500
        #     if not code == 200:
        #         self.logger.warning(
        #             "登录失败: %s" % (self.auth_kwargs['username'].encode(
        #                 'utf-8')))
        #         return None
        #
        #     cookies = res.json().get('cookies')
        #     self.h.hset(self.auth_kwargs['username'], cookies)
        #
        #     self.cookie = cookie2str(cookies)
        #     self.h_limit.hset(
        #         self.source + '|' + self.auth_kwargs['username'].encode(
        #             'utf-8'), 0)
        #     return cookies

        if count >= 5:
            self.logger.warning("帐号%s 被限制登录"
                                % self.auth_kwargs['username'].encode('utf-8'))
            if int(count) == 6:
                self.robot_login.send_markdown(
                    title="简历搜索",
                    content="#### 前程简历搜索帐号被禁用.\n"
                            "- 帐号： %s\n"
                            "- 密码： %s\n"
                            "- 会员名: %s\n"
                            "- 代理： %s\n\n"
                            % (
                                self.auth_kwargs['username'].encode(
                                    'utf-8'),
                                self.auth_kwargs['password'].encode(
                                    'utf-8'),
                                self.auth_kwargs['account_name'].encode(
                                    'utf-8'),
                                self.auth_kwargs['ip'].encode(
                                    'utf-8') + ':' +
                                self.auth_kwargs['port'].encode('utf-8'))
                )

            raise FiveOneResumeException('account_limited')

        self.cookie = cookie2str(eval(cookies))
        self.h_limit.hset(
            self.source + '|' + self.auth_kwargs['username'].encode(
                'utf-8'), 0)
        return cookies

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

    def is_limited(self, username):
        # 用于限制帐号进入详情页次数
        today = '|' + datetime2str(datetime.datetime.now(), '%Y-%m-%d')

        if not self.h_use_record.hget(username + today):
            self.h_use_record.hset(username + today, 0)
            count = 0
        else:
            count = int(self.h_use_record.hget(username + today))

        if username == ('E4gl36307', '18518261507', 'bjlb7610'):
            # if count >= 2000:
            if count >= settings.COUNT_LIMITED:
                return True

        # elif username in ('lzmy9771', 'hgmy2130'):
        #     if count > 5000:
        #         return True

        else:
            if count >= settings.COUNT_LIMITED:
                return True
        return count

    def init_search_account(self):
        if sem.locked():
            return
        try:
            sem.acquire()
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
            sql = """
                SELECT a.*
                FROM
                  autojob_v2.t_account a
                WHERE
                  EXISTS(
                      SELECT 1
                      FROM autojob_v2.t_account_use_type b
                      WHERE a.id = b.accountId
                            AND b.useType = 'SEARCH_AWAKE'
                            AND b.valid=1
                            AND a.valid = 1
                            AND a.status = 1
                            AND a.source = 'FIVE_ONE'
                  );
                """
            account_list = mysql_.query_by_sql(sql)
            self.logger.info('共匹配到%s个有效帐号' % len(account_list))
            for account in account_list:
                global RUN_STATUS
                if RUN_STATUS.get(account['username'].encode('utf-8')):
                    self.logger.warning('当前帐号 %s 处于执行状态.' % account[
                        'username'].encode('utf-8'))
                    continue
                if self.is_limited(username=account['username']) is True:
                    continue

                self.q_search_account.put(account)
            self.logger.info('初始化搜索帐号队列完毕, %s'
                             % self.q_search_account.qsize())
            sem.release()

        except Exception as e:
            self.logger.exception('初始化搜索帐号队列失败: ' + str(e))
            sem.release()

    def start_push_task(self):
        if sem.locked():
            return
        try:
            sem.acquire()
            self.logger.info('开始推送前程唤醒任务.')
            act = CreateTask()
            act.create_task_from_mysql(use_keywords=True)
            sem.release()
        except Exception as e:
            self.logger.exception(e)
            sem.release()

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def init_search_page(self):
        url = 'https://ehire.51job.com/Candidate/SearchResumeNew.aspx'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'ehire.51job.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies,
                                            allow_redirects=False)
        if res.status_code == 302:
            self.logger.warning('cookie invalid.')
            # self.h.hset(
            #     self.source + '|' + self.auth_kwargs['username'].encode(
            #         'utf-8'), '')
            raise MfCookieValidException('cookie_invalid')

        self.logger.info('初始化search_page成功.')
        return res.content

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    def get_captcha(self, referer, access_key, do_type='CheckResumeView'):

        js_context = PyV8.JSContext()
        js_context.__enter__()
        # js_context.eval(js_text)
        js_context.eval(FIVE_ONE_JS_FUNC)
        get_guid = js_context.locals.get_guid
        guid = get_guid(20, 16)
        url = 'https://ehire.51job.com/ajax/Validate/PageValidate.aspx?' \
              'type=getverify&key=%s&guid=%s' \
              '&doType=%s' % (access_key, guid, do_type)

        headers = {
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'ehire.51job.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies,
                                            allow_redirects=False)
        if res.status_code != 200:
            self.logger.warning('获取验证码失败.')
            raise Exception
        self.logger.info('获取验证码图片成功.')

        img_path = './data/img/test-%s.png' % str(uuid.uuid1())
        with open(img_path, 'wb') as f:
            f.write(res.content)

        self.check_captcha(img_path=img_path, referer=referer,
                           guid=get_guid(20, 16), access_key=access_key,
                           do_type=do_type)

    @retry(stop_max_attempt_number=3)
    @cls_catch_exception
    def check_captcha(self, img_path, referer, guid, access_key, do_type):
        identify = Identify()
        captcha_order = '{"height_row3": 156, "height_row2": 98, "height_row1": 40, "index_list_1": [12, 7, 2, 11, 5, 8, 4, 0, 1, 3, 6, 9, 10, 13, 14], "index_list_3": [23, 4, 22, 10, 12, 5, 26, 28, 0, 11, 17, 25, 16, 29, 20], "col_num": 15, "index_list_2": [3, 13, 18, 2, 7, 1, 19, 9, 24, 27, 14, 8, 15, 21, 6]}'
        new_img_path = identify.recover_captcha(captcha_file_path=img_path,
                                                captcha_order=captcha_order)
        res_string = identify.analysis_captcha(img_path=new_img_path,
                                               type_code=9104)

        # os.rmdir(img_path)
        # os.rmdir(new_img_path)

        if not res_string:
            raise Exception

        self.logger.info('返回的验证码坐标为： %s' % res_string.encode('utf-8'))

        url = 'https://ehire.51job.com/ajax/Validate/PageValidate.aspx'
        headers = {
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'ehire.51job.com',
            'Origin': 'https://ehire.51job.com',
            'Pragma': 'no-cache',
            'Referer': referer,
            'User-Agent': self.user_agent,
            'X-Requested-With': 'XMLHttpRequest',
        }

        real_string = ';'.join(
            [','.join([item.split(',')[0], str(int(item.split(',')[1]) - 40)])
             for item in res_string.split('|')]
        )

        self.logger.info('真实验证码坐标为： %s' % real_string.encode('utf-8'))

        data = {
            'type': 'checkverift',
            'key': access_key,
            'p': real_string,
            'guid': guid,
            'doType': do_type,
        }

        res = self.html_downloader.download(url, method='POST',
                                            data=data,
                                            headers=headers,
                                            proxies=self.proxies,
                                            allow_redirects=False)

        code = self.html_parser.parser(res.content).find(
            'msgtype').text.encode('utf-8')
        if code == '0':
            self.logger.warning("验证码不正确")
            return
        if code == '1':
            self.logger.info('验证成功')

        else:
            self.logger.warning('未知的返回code: %s' % code)

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def get_resume_list(self, previous_page_html,
                        action='pagerTopNew$ctl03',
                        **search_args):
        """

        :param previous_page_html:
        :param action:
        :param search_args: city['北京|010000'], keywords['销售代表|3001']
        :return:
        """
        url = 'https://ehire.51job.com/Candidate/SearchResumeNew.aspx'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'ehire.51job.com',
            'Origin': 'https://ehire.51job.com',
            'Pragma': 'no-cache',
            'Referer': 'https://ehire.51job.com/Candidate/'
                       'SearchResumeNew.aspx',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }

        _soups = self.html_parser.parser(previous_page_html)

        data = {
            '__EVENTTARGET': action,
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': _soups.find('input', id='__VIEWSTATE').get('value'),
            'ctrlSerach$search_keyword_txt': search_args['keywords'].split(
                '|')[0],
            'ctrlSerach$search_company_txt': '',
            'ctrlSerach$search_area_input': '',
            'ctrlSerach$search_area_hid': '',
            'ctrlSerach$search_funtype_hid': '',
            'ctrlSerach$search_expectsalaryf_input': '不限',
            'ctrlSerach$search_expectsalaryt_input': '不限',
            'ctrlSerach$search_industry_hid': '',
            'ctrlSerach$search_wyf_input': '不限',
            'ctrlSerach$search_wyt_input': '不限',
            'ctrlSerach$search_df_input': '不限',
            'ctrlSerach$search_dt_input': '不限',
            'ctrlSerach$search_cursalaryf_input': '不限',
            'ctrlSerach$search_cursalaryt_input': '不限',
            'ctrlSerach$search_age_input': '年龄:18-30',
            'ctrlSerach$search_agef_input': '18',
            'ctrlSerach$search_aget_input': '30',
            'ctrlSerach$search_expjobarea_input': search_args['city'].split(
                '|')[0],
            'ctrlSerach$search_expjobarea_hid': search_args['city'],
            'ctrlSerach$search_forlang_input': '语言',
            'ctrlSerach$search_fl_input': '不限',
            'ctrlSerach$search_fllsabilityll_input': '不限',
            'ctrlSerach$search_englishlevel_input': '英语等级',
            'ctrlSerach$search_sex_input': '性别',
            'ctrlSerach$search_major_input': '专业',
            'ctrlSerach$search_major_hid': '',
            'ctrlSerach$search_hukou_input': '户口',
            'ctrlSerach$search_hukou_hid': '',
            'ctrlSerach$search_rsmupdate_input': '近1周',
            'ctrlSerach$search_jobstatus_input': '求职状态',
            'send_cycle': '1',
            'send_time': '7',
            'send_sum': '10',
            'ctrlSerach$hidSearchValue':
                u'%s##0#######20#35############近1周|1##1#0##%s#0#0#0'
                % (search_args['keywords'].split('|')[0], search_args['city']),
            'ctrlSerach$hidKeyWordMind': '',
            'ctrlSerach$hidRecommend': '',
            'ctrlSerach$hidWorkYearArea': '',
            'ctrlSerach$hidDegreeArea': '',
            'ctrlSerach$hidSalaryArea': '',
            'ctrlSerach$hidCurSalaryArea': '',
            'ctrlSerach$hidIsRecDisplay': '1',
            'showselected': '',
            'pagerTopNew$ctl06': '50',
            'cbxColumns$0': 'AGE',
            'cbxColumns$1': 'WORKYEAR',
            'cbxColumns$2': 'SEX',
            'cbxColumns$3': 'AREA',
            'cbxColumns$4': 'WORKFUNC',
            'cbxColumns$5': 'TOPDEGREE',
            'cbxColumns$6': 'LASTUPDATE',
            'hidAccessKey': _soups.find(
                'input', id='hidAccessKey').get('value'),
            'hidShowCode': '0',
            'hidDisplayType': '1',
            'hidEhireDemo': '',
            'hidUserID': '',
            'hidCheckUserIds': _soups.find(
                'input', id='hidCheckUserIds').get('value'),
            'hidCheckKey': _soups.find('input', id='hidCheckKey').get('value'),
            'hidEvents': '',
            'hidNoSearchIDs': '',
            'hidBtnType': '',
            'hideMarkid': '',
            'hidStrAuthority': _soups.find('input', id='hidStrAuthority').get(
                'value'),
            'hidDownloadNum': _soups.find('input', id='hidDownloadNum').get(
                'value'),
            'hidKeywordCookie': '',
            'showGuide': '',
        }

        if not search_args['use_keywords']:
            self.logger.info('采用职能进行搜索.')
            data['ctrlSerach$search_keyword_txt'] = ''
            data['ctrlSerach$search_funtype_hid'] = search_args['keywords']
            data['hidSearchValue'] = \
                u'##0#%s######20#35############近1周|1##1#0##%s#0#0#0' \
                % (search_args['keywords'], search_args['city'])
        else:
            self.logger.info('采用关键词进行搜索.')

        res = self.html_downloader.download(url, method='POST',
                                            headers=headers, data=data,
                                            proxies=self.proxies,
                                            allow_redirects=False)
        if res.status_code == 302:
            self.logger.warning('cookie invalid.')
            # self.h.hset(
            #     self.source + '|' + self.auth_kwargs['username'].encode(
            #         'utf-8'), '')
            raise MfCookieValidException('cookie_invalid')

        access_key = self.html_parser.parser(res.content).find(
            'input', id='hidAccessKey').get('value')
        # auth_ = self.html_parser.parser(res.content).find(
        #     'div', id='divVerifyCode_ch').get('style')

        soups = self.html_parser.parser(res.content).find_all(
            'td', class_='Common_list_table-id-text')

        resume_list = []

        if not soups:
            # 通过empty_times控制，当某账号累计10次遇到返回为空的情况，则进行验证码验证
            empty_times = int(self.h_search_empty_times.hget(self.auth_kwargs['username'])) \
                if self.h_search_empty_times.hget(self.auth_kwargs['username']) else 0
            if empty_times > 10:
                self.logger.warning('搜索列表遇到验证码. %s' %
                                    self.auth_kwargs['username'].encode(
                                        'utf-8')
                                    )
                self.get_captcha(referer=res.url, access_key=access_key,
                                 do_type='CheckSearchResume')
                self.h_search_empty_times.hset(self.auth_kwargs['username'], 0)
                raise Exception
            else:
                self.logger.warning('未匹配到搜索结果，跳过该任务[%s, %s, %s]'
                                    % (
                                        self.auth_kwargs['username'].encode(
                                            'utf-8'),
                                        search_args['keywords'].encode('utf-8'),
                                        search_args['city'].encode('utf-8')))
                empty_times += 1
                self.h_search_empty_times.hset(self.auth_kwargs['username'], empty_times)
                return resume_list, ''


        for soup in soups:
            ref_time = soup.find_parent().find_all('td')[-2].text.encode(
                'utf-8')
            if datetime.datetime.now().isoweekday() == 1:
                # 周一
                # global DAY_LIMITED
                # DAY_LIMITED = 5
                # limited_day = datetime.datetime.now() - datetime.timedelta(
                #     days=4)
                global DAY_LIMITED
                DAY_LIMITED = settings.DAY_LIMITED
                limited_day = datetime.datetime.now() - datetime.timedelta(
                    days=1
                )
            else:
                global DAY_LIMITED
                DAY_LIMITED = settings.DAY_LIMITED
                limited_day = datetime.datetime.now() - datetime.timedelta(
                    days=1
                )

            if str2datetime(ref_time, '%Y-%m-%d').date() < \
                    limited_day.date():
                self.logger.warning('匹配到%s天前的简历，执行跳过操作.' % DAY_LIMITED)
                break
            resume_list.append(soup.find('a').get('href'))

        try:
            page = self.html_parser.parser(res.content).find(
                'div', class_='Search_page-numble').find(
                'a', class_='active').get('title').encode('utf-8')
        except Exception as e:
            self.logger.warning('未找到分页组件，跳过该任务[%s, %s]'
                                % (search_args['keywords'].encode('utf-8'),
                                   search_args['city'].encode('utf-8')))
            return resume_list, ''

        self.logger.info('page: %s, 总计获取到简历%s份, 搜索条件[%s, %s]'
                         % (page, len(resume_list),
                            search_args['keywords'].encode('utf-8'),
                            search_args['city'].encode('utf-8')))

        if int(page) > settings.TASK_PAGE_LIMIT:
            raise FiveOneResumeException('task_page_limit')

        return resume_list, res.content

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def get_resume_detail(self, resume_url):
        url = 'https://ehire.51job.com/' + resume_url
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'ehire.51job.com',
            'Referer': 'https://ehire.51job.com/Candidate/SearchResumeNew.aspx',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie
        }

        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies,
                                            allow_redirects=False)
        if res.status_code == 302:
            self.logger.warning('cookie invalid.')
            # self.h.hset(
            #     self.source + '|' + self.auth_kwargs['username'].encode(
            #         'utf-8'), '')
            raise MfCookieValidException('cookie_invalid')

        if '简历ID：' in res.content:
            self.logger.info('获取简历正文成功 %s'
                             % self.auth_kwargs['username'].encode('utf-8'))
            return res.content

        self.logger.warning('获取简历正文失败 %s'
                            % self.auth_kwargs['username'].encode('utf-8'))

        access_key = self.html_parser.parser(res.content).find(
            'input', id='hidAccessKey').get('value')

        # self.robot_login.send_markdown(
        #     title="简历搜索",
        #     content="#### 前程简历搜索详情页出现验证码.\n"
        #             "- 帐号： %s\n"
        #             "- 密码： %s\n"
        #             "- 会员名: %s\n"
        #             "- 代理： %s\n\n"
        #             % (
        #                 self.auth_kwargs['username'].encode(
        #                     'utf-8'),
        #                 self.auth_kwargs['password'].encode(
        #                     'utf-8'),
        #                 self.auth_kwargs['account_name'].encode(
        #                     'utf-8'),
        #                 self.auth_kwargs['ip'].encode(
        #                     'utf-8') + ':' +
        #                 self.auth_kwargs['port'].encode('utf-8'))
        # )
        self.get_captcha(referer=res.url, access_key=access_key)

        time.sleep(60)
        raise Exception

    def resume_search(self, **search_args):
        self.get_cookie()
        ip = eval(self.auth_kwargs['proxy'])['ip']
        port = eval(self.auth_kwargs['proxy'])['port']

        self.proxies = {
            'http': 'http://%s:%s' % (ip, port),
            'https': 'https://%s:%s' % (ip, port),
        }
        today = '|' + datetime2str(datetime.datetime.now(), '%Y-%m-%d')

        # print(search_args)

        flag = False
        while True:

            awake_flow_no = self.h_awake_flow_no.hget('FIVE_ONE')
            if self.h_status.hget(awake_flow_no) == '400':
                self.logger.info("程序当前处于暂停状态.sleep 60s")
                time.sleep(60)
                continue

            if flag is False:
                # 扫描第一页
                page_html = self.init_search_page()
                resume_list, page_html = self.get_resume_list(
                    page_html, action='pagerTopNew$ctl00', **search_args)
                flag = True
            else:
                resume_list, page_html = self.get_resume_list(page_html,
                                                              **search_args)

            if not resume_list:
                raise FiveOneResumeException('resume_list_empty')

            time.sleep(random.randint(1, 5))
            for resume_args in resume_list:

                if self.is_limited(self.auth_kwargs['username']) is True:
                    raise FiveOneResumeException('user_record_limited')

                count = self.is_limited(self.auth_kwargs['username'])

                # 用于简历去重
                resume_id = re.findall('''(?<=hidUserID=)\d+?(?=&)''',
                                       resume_args)[0].encode('utf-8')

                last_search_day = self.h_black_list.hget(resume_id)
                if last_search_day:
                    distance = (str2datetime(today.replace('|', ''),
                                             '%Y-%m-%d')
                                - str2datetime(last_search_day,
                                               '%Y-%m-%d')).days
                else:
                    distance = DAY_LIMITED + 1
                if distance < DAY_LIMITED:
                    self.logger.warning('该简历%s天内已经被采集过: %s'
                                        % (DAY_LIMITED, resume_id))
                    continue
                self.h_black_list.hset(resume_id, today.replace('|', ''))
                resume_detail = self.get_resume_detail(
                    resume_url=resume_args)
                if not resume_detail:
                    continue
                resume_uuid = str(uuid.uuid1())
                # content_origin = {'name': '', 'email': '', 'phone': '',
                #                   'html': resume_detail.decode('utf-8')}
                # content = json.dumps(content_origin, ensure_ascii=False)

                content = resume_detail.decode('utf-8')

                sql = '''INSERT INTO spider_search.resume_raw (source, content, 
                createBy, 
                trackId, createtime, email, emailJobType, emailCity, subject) VALUES 
                (%s, %s, "python", %s, now(), %s, %s, %s, %s)'''
                sql_value = (self.common_settings.SOURCE, content, resume_uuid,
                             self.auth_kwargs['username'],
                             search_args['keywords'].split('|')[0],
                             search_args['city'].split('|')[0],
                             str(resume_id))

                resume_update_time = ''
                msg_data = {
                    "channelType": "WEB",
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
                        'emailJobType': search_args['keywords'].split('|')[0],
                        'emailCity': search_args['city'].split('|')[0],
                        'subject': str(resume_id)
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
                res = self.save_data(sql=sql, data=sql_value,
                                     msg_data=msg_data)

                if res:
                    count += 1
                    self.h_use_record.hset(
                        self.auth_kwargs['username'] + today,
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
                    INSERT INTO spider.resume_awake_record (source, position, city,
                     raw_id, create_time, username) VALUES ('FIVE_ONE', %s, 
                     %s, %s, now(), %s)
                    '''
                    value = (
                        search_args['keywords'].split('|')[0], search_args[
                            'city'].split('|')[0], res,
                        self.auth_kwargs['username'])
                    mysql_.save(sql, value)

                time.sleep(random.randint(5, 7))


def exchange_account(obj):
    while True:
        if obj.q_search_account.empty():
            obj.init_search_account()
            time.sleep(10)
        search_account = eval(obj.q_search_account.get())
        RUN_STATUS[search_account['username'].encode('utf-8')] = 1
        return search_account


def execute_resume_search():
    runner = Resume51job()
    # runner.init_search_account()
    search_account = None

    while True:
        try:

            hour = datetime.datetime.now().hour
            if hour < 7 or hour >= 22:
                runner.logger.info("当前程序不再执行时间段内， sleep...")
                global RUN_STATUS, LOGIN_STATUS
                RUN_STATUS = {}
                LOGIN_STATUS = {}
                time.sleep(6000)
                continue

            task_id, param = runner.get_task()  # 从调度获取任务

            if not task_id:
                continue

            if not search_account:
                # 初始化search_account
                search_account = exchange_account(runner)

            runner.auth_kwargs = {
                'username': search_account['username'],
                'password': search_account['password'],
                'account_name': search_account['accountName'],
                'ip': eval(search_account['proxy'])['ip'],
                'port': eval(search_account['proxy'])['port'],
                'proxy': search_account['proxy'],
            }

            # param = {
            #     'city': u'北京|010000',
            #     'keywords': u'销售代表|3001',
            #     'use_keywords': False
            # }
            #
            # runner.auth_kwargs = {
            #     'username': 'ytkj6164',
            #     'password': 'Meih660ua9',
            #     'account_name': u'晟易塔科技',
            #     'ip': '47.93.115.141',
            #     'port': '3128',
            #     'proxy': '{"ip": "47.93.115.141", "port": "3128"}',
            # }

            runner.logger_prefix = '[%s - %s] ' % (
                param['city'].encode('utf-8').split('|')[0],
                param['keywords'].encode('utf-8').split('|')[0]
            )

            try:
                runner.resume_search(**param)
            except FiveOneResumeException as e:
                runner.release_run_status()
                runner.update_task(task_id=task_id, execute_result=str(e))
                if e.value == 'resume_list_empty':
                    runner.update_task(task_id=task_id)
                    # break   # Test
                    search_account = exchange_account(runner)
                    runner.logger.info('未返回任何简历.')
                    continue

                elif e.value == 'account_limited':
                    search_account = exchange_account(runner)
                    runner.logger.warning('帐号被限制登录了.开始更换帐号。')
                    continue

                elif e.value == 'user_record_limited':
                    runner.logger.warning('帐号使用次数超额了: %s'
                                          % settings.COUNT_LIMITED)
                    runner.update_task(task_id=task_id)
                    # break   # Test
                    search_account = exchange_account(runner)
                    continue
                elif e.value == 'task_page_limit':
                    runner.logger.warning('任务页码超限: %s' %
                                          settings.TASK_PAGE_LIMIT)
                    continue
            except MfCookieValidException as e:
                if not LOGIN_STATUS.get(runner.auth_kwargs[
                                            'username'].encode('utf-8'), ''):
                    LOGIN_STATUS[runner.auth_kwargs[
                        'username'].encode(
                        'utf-8')] = 1
                    runner.h_limit.hset(
                        runner.source + '|' + runner.auth_kwargs[
                            'username'].encode(
                            'utf-8'), 4)
                    runner.logger.info('强制调整账号限制次数: %s' % runner.auth_kwargs[
                        'username'].encode(
                        'utf-8'))
                else:
                    runner.logger.warning('该账号已重新登录过: %s' % runner.auth_kwargs[
                        'username'].encode(
                        'utf-8'))
                    time.sleep(300)
                runner.release_run_status()
                runner.update_task(task_id=task_id, execute_result=str(e))
                search_account = exchange_account(runner)
                continue

            except Exception as e:
                runner.logger.exception(str(e))
                continue
            runner.update_task(task_id=task_id, execute_result=str(e))
        except Exception as e:
            runner.logger.exception(str(e))


def execute_create_task():
    base = Resume51job(local_setting={
        'TASK_TYPE': 'SEARCH_AWAKE',
        'SOURCE': 'FIVE_ONE',
        'BACK_ENDS': settings.project_settings['BACK_ENDS']
    })

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
            base.h_awake_flow_no.hset('FIVE_ONE', flow_no)
            base.logger.info('当前flow_no为： %s' % flow_no.encode('utf-8'))

            creator = CreateTask()
            creator.create_task_from_mysql()
            base.update_task(task_id=task_id)
            base.logger.info('任务生成完毕.')
        except Exception as e:
            base.logger.exception(str(e))


if __name__ == '__main__':
    # execute_create_task()
    # execute_resume_search()
    gevent.joinall(
        [gevent.spawn(execute_resume_search)
         for i in xrange(settings.COROUTINE_NUM)
         ].append(gevent.spawn(execute_create_task)))
    # runner = Resume51job()
    # runner.cookie = 'EhireGuid=307543dedcac4ae5b717ba94366a4b85; guid=15194434655236790044; search=jobarea%7E%60090200%7C%21ord_field%7E%600%7C%21recentSearch0%7E%601%A1%FB%A1%FA090200%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2530%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA2%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1526265305%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch1%7E%601%A1%FB%A1%FA050000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA5405%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA2%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1526264847%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch2%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA0000%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA2%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1520476378%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21; nsearch=jobarea%3D%26%7C%26ord_field%3D%26%7C%26recentSearch0%3D%26%7C%26recentSearch1%3D%26%7C%26recentSearch2%3D%26%7C%26recentSearch3%3D%26%7C%26recentSearch4%3D%26%7C%26collapse_expansion%3D; LangType=Lang=&Flag=1; ASP.NET_SessionId=px0wveqylryv5gwabfaiytgz; HRUSERINFO=CtmID=3946229&DBID=1&MType=02&HRUID=5101770&UserAUTHORITY=1111111111&IsCtmLevle=1&UserName=18518261507&IsStandard=0&LoginTime=06%2f21%2f2018+14%3a30%3a01&ExpireTime=06%2f21%2f2018+14%3a40%3a01&CtmAuthen=0000011000000001000110010000000011100001&BIsAgreed=true&IsResetPwd=0&CtmLiscense=2&AccessKey=479c89d2669952f0; AccessKey=0861c959e65d42f; KWD=SEARCH='
    # referer = 'https://ehire.51job.com/Candidate/ResumeView.aspx?hidUserID=678918363&hidEvents=23&pageCode=3&hidKey=0e38003f5d99ebdf334a8bbd5f81cc98'
    # access_key = '0861c959e65d42f'
    # runner.get_captcha(referer, access_key)
    #
    # runner.check_captcha(img_path='./data/img/test-a7ad07a6-7520-11e8-ba2d'
    #                               '-1866da075675.png')
