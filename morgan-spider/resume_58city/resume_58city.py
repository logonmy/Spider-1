#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: IntelliJ IDEA
@file: resume_58city.py
@create at: 2018-08-30 18:29

这一行开始写关于本文件的说明与解释
"""
import datetime
import json
import random
import re
import time
import uuid
import gevent
from urllib import unquote
from MySQLdb.cursors import DictCursor

from conf import settings as static_settings
from create_task import settings, CreateTask
from mf_utils.core import InitCorePlus
from mf_utils.common import cookie2str, datetime2str, cookie2dict
from mf_utils.sql.mysql import MysqlHandle
from crwy.utils.data.RedisHash import RedisHash
from crwy.utils.filter.RedisSortedSet import RedisSortedSet
from crwy.utils.queue.RedisQueue import RedisQueue
from mf_utils.html.font_analysis import FontAnalysis, font_mapping
from mf_utils.decorates import cls_catch_exception, cls_refresh_cookie
from mf_utils.exceptions import MfCookieValidException
from mf_utils.extend.dingding_robot import DingDingRobot
from crwy.utils.no_sql.redis_m import get_redis_client

from retrying import retry
from gevent.lock import BoundedSemaphore
from gevent import monkey

monkey.patch_all()

# 账号锁
sem = BoundedSemaphore(1)

# 任务锁
sem_1 = BoundedSemaphore(1)

# 用于防止多协程共用同一账号
RUN_STATUS = {}

server = get_redis_client(
    host='r-2ze0889fc8e3c784.redis.rds.aliyuncs.com',
    port=6379,
    password='uV2ngVk9AC',
    db=6,
    cls_singleton=False
)


class Resume58City(InitCorePlus):
    def __init__(self, local_setting=None):
        super(Resume58City, self).__init__(local_setting=local_setting)
        self.site = 'FIVE_EIGHT'
        self.cookie_pool = RedisHash(
            'cookie_pool:{}'.format(self.site), server=server)
        # 账号cookie状态 key为 username
        self.h_account_limit = RedisHash(
            'account_limit:{}'.format(self.site), server=server)
        # 搜索上限
        self.h_search_limit = RedisHash(
            'search_limit:{}'.format(self.site), server=server)
        self.auth_kwargs = None
        self.cookie = None
        self.q_search_account = RedisQueue(
            'five_eight_search_account_1', **static_settings.REDIS_CONF)
        self.s_filter = RedisSortedSet(
            'five_eight_search', **static_settings.REDIS_CONF)
        self.proxies = None
        # self.mysql_handler = MysqlHandle(**static_settings.MYSQL_CONF_TEST)
        self.mysql_handler = MysqlHandle(**static_settings.MYSQL_CONF)
        self.mns_handler = self.init_mns(
            endpoint='http://1315265288610488.mns.cn-beijing.aliyuncs.com',
            queue='morgan-queue-resume-raw'
            # queue='morgan-queue-test-resume-raw'
        )
        self.robot_login = DingDingRobot(
            access_token="3c7b5bd12b49cfdd5f47f00df7fa9c478"
                         "485254485d567ff6abcbf45927e648a"
        )

    @staticmethod
    def get_real_html(html):
        """
        还原html字体
        :param html:
        :return:
        """
        fa = FontAnalysis(html=html)
        real_font_mapping = fa.get_real_font_mapping(
            fa.analysis(), font_mapping)
        return fa.recover_html(
            html=html,
            real_font_mapping=real_font_mapping)

    def get_cookie(self):
        """
        根据账号获取cookie
        :return:
        """
        username = self.auth_kwargs.get('username')
        if not username:
            raise Exception('username is empty.')
        self.cookie = self.cookie_pool.hget('{username}'.format(
            username=username.encode('utf-8')
        ))
        if not self.cookie:
            raise MfCookieValidException('cookie invalid.')

        self.cookie = cookie2str(eval(self.cookie))

        return username, self.cookie

    def init_search_account(self, use_type='SEARCH_AWAKE'):
        """
        初始化可用账号队列
        :param use_type:
        :return:
        """

        sem.acquire()
        try:
            mysql_ = self.init_mysql(
                user='super_reader',
                passwd='nMGZKQIXr4PE8aR2',
                host='rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
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
                            AND a.source = 'FIVE_EIGHT'
                  )
                ORDER BY a.id DESC;
                """ % use_type)
            self.logger.info('共匹配到%s个有效帐号' % len(account_list))
            effective_account_list = []
            for account in account_list:
                # 跳过已达上限账号
                self.auth_kwargs = account
                if self.is_limit(change=False):
                    continue
                # 跳过cookie失效账号
                if self.h_account_limit.hget(
                        self.auth_kwargs['username'].encode(
                            'utf-8')) in ['1', 1]:
                    self.logger.info('账号被禁用: {}'.format(
                        self.auth_kwargs['username'].encode('utf-8')
                    ))
                    continue
                if RUN_STATUS.get(self.auth_kwargs['username']):
                    continue

                self.q_search_account.put(account)
                effective_account_list.append(account)

            self.logger.info('初始化搜索帐号队列完毕 %s'
                             % len(effective_account_list))
            sem.release()
            return effective_account_list

        except Exception as e:
            self.logger.exception('初始化搜索帐号队列失败: ' + str(e))
            sem.release()

    def init_auth_kwargs(self):
        while True:
            if self.q_search_account.empty():
                if not self.init_search_account():
                    time.sleep(60)
                    self.logger.warning('账号队列为空, sleep 60s')
                    continue

            break

        auth_kwargs = eval(self.q_search_account.get())
        # print auth_kwargs
        if RUN_STATUS.get(auth_kwargs['username']):
            self.logger.info('账号： {}， 正在被其他线程使用'.format(
                auth_kwargs['username'].encode('utf-8')
            ))
            time.sleep(10)
            self.init_auth_kwargs()

        self.auth_kwargs = auth_kwargs
        RUN_STATUS[auth_kwargs['username']] = 1

    @staticmethod
    def get_resume_id(url):
        resume_id = re.search('(?=3_).*?(?=&)', url).group()
        return resume_id[:16]

    def is_limit(self, change=True):
        """
        判断是否达到上限
        :param change: 用于标识是否变更limit
        :return:
        """
        today = datetime2str(datetime.datetime.now(), '%Y-%m-%d')
        key = today + '|' + self.auth_kwargs['username'].encode('utf-8')
        limit = self.h_search_limit.hget(key)

        if not limit:
            self.h_search_limit.hset(key, 0)
            return False

        if int(limit) >= settings.SEARCH_LIMIT:
            self.logger.warning('当前帐号 %s 已达上限 %s，当天不再进行搜索.' % (
                self.auth_kwargs['username'].encode('utf-8'),
                settings.SEARCH_LIMIT))
            return True
        if change:
            limit = int(limit)
            limit += 1
            self.h_search_limit.hset(key, limit)
        return False

    def do_filter(self, resume_id):
        """
        用于去重
        :param resume_id:
        :return:
        """
        now = time.time()
        last_time = self.s_filter.zscore(resume_id)
        if not last_time:
            self.s_filter.zadd(now, resume_id)
            return False
        if (datetime.datetime.utcfromtimestamp(now) -
            datetime.datetime.utcfromtimestamp(last_time)).days >= \
                settings.DELAY_DAY:
            self.s_filter.zadd(now, resume_id)
            return False
        return True

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def get_resume_list(self, page=1, **params):
        self.logger.info('开始执行搜索任务， USER: {} PAGE: {} {}'.format(
            self.auth_kwargs['username'].encode('utf-8'), page,
            json.dumps(params, ensure_ascii=False).encode('utf-8')
        ))
        end = datetime.datetime.now() + datetime.timedelta(days=1)
        start = end - datetime.timedelta(days=settings.SEARCH_DAY)
        post_date = datetime2str(start, fmt='%Y%m%d') + '000000_' \
                    + datetime2str(end, fmt='%Y%m%d') + '000000'
        url = '{}pn{}/pve_5593_{}/?key={}&age=18_30&postdate={}'.format(
            params.get('city_url'), page, params.get('degree', '4'),
            params.get('keyword').encode('utf-8'), post_date
        )
        # print(url)
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'cookie': self.cookie,
            'pragma': 'no-cache',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/68.0.3440.84 Safari/537.36'
        }
        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies)
        if 'passport.58.com' in res.url:
            raise MfCookieValidException('cookie invalid. {}'.format(
                self.auth_kwargs['username'].encode('utf-8')))
        real_html = self.get_real_html(res.content)
        soups = self.html_parser.parser(real_html).find(
            'div', id='infolist').find_all('dl')

        has_next = True if self.html_parser.parser(real_html).find(
            'div', class_='pagerout').find(
            'a', class_='next') else False

        url_lst = []
        for soup in soups:
            url = soup.find('dt').find('a').get('href')
            resume_id = self.get_resume_id(url)
            if self.do_filter(resume_id):
                self.logger.info('简历: {}, {}天内已被采集过'.format(
                    resume_id, settings.DELAY_DAY))
                continue
            url_lst.append(url)
        time.sleep(random.randint(1, 2))
        return has_next, url_lst[:-1]

    def start_push_task(self):
        if sem_1.locked():
            return
        try:
            sem_1.acquire()
            self.logger.info('开始推送58同城唤醒任务.')
            act = CreateTask()
            act.create_task()
            sem_1.release()
        except Exception as e:
            self.logger.exception(e)
            sem_1.release()

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def get_resume_detail(self, url):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;'
                      'q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            # 'cache-control': 'no-cache',
            'Cookie': self.cookie,
            # 'pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/68.0.3440.84 Safari/537.36'
        }
        url = unquote(url)

        if not self.cookie:
            raise Exception('account_limit')

        cookies = cookie2dict(self.cookie)
        res = self.html_downloader.download(url, headers=headers,
                                            proxies=self.proxies,
                                            cookies=cookies)
        if 'passport.58.com' in res.url:
            raise MfCookieValidException('cookie invalid.')
        resume_id = self.get_resume_id(res.url)
        try:
            real_html = self.get_real_html(res.content)
        except Exception as e:
            real_html = None
            self.logger.info(res.content)
        time.sleep(random.randint(1, 2))
        return resume_id, real_html

    def resume_search(self, **params):
        self.get_cookie()

        proxy = eval(self.auth_kwargs['proxy'])
        self.proxies = {
            'http': 'http://%s:%s' % (proxy.get('ip'), proxy.get('port')),
            'https': 'https://%s:%s' % (proxy.get('ip'), proxy.get('port')),
        }
        self.logger.info(
            '当前使用的代理为： {}'.format(json.dumps(proxy).encode('utf-8')))
        page = 1
        while True:
            if self.is_limit(change=False):
                raise Exception('account_limited')

            has_next, resume_list = self.get_resume_list(
                page=page, **params)

            if not resume_list and has_next is False:
                raise Exception('no_resume_found')

            for resume in resume_list:
                if not resume.encode('utf-8').startswith('http'):
                    url = 'https:' + resume
                else:
                    url = resume
                try:
                    resume_id, resume_detail = self.get_resume_detail(url=url)
                except MfCookieValidException as e:
                    raise e
                except Exception as e:
                    self.logger.exception(e)
                    continue
                content = resume_detail
                resume_uuid = str(uuid.uuid1())
                sql = '''insert into spider_search.resume_raw (source, content,
                        createBy, subject, emailCity, emailJobType, email,
                        trackId, createtime) values
                        (%s, %s, "python", %s, %s, %s, %s, %s, now())'''
                sql_value = (
                    u'FIVE_EIGHT', content.decode('utf-8'),
                    resume_id, params.get('city_name'), params.get('keyword'),
                    self.auth_kwargs['username'], resume_uuid)

                msg_data = {
                    "channelType": "WEB",
                    "content": {
                        "content": content.decode('utf-8'),
                        "id": '',
                        "createBy": "python",
                        "createTime": int(time.time() * 1000),
                        "ip": '',
                        "resumeSubmitTime": '',
                        "resumeUpdateTime": '',
                        "source": self.site,
                        "trackId": str(resume_uuid),
                        "avatarUrl": '',
                        "email": self.auth_kwargs['username'],
                        'emailJobType': params['keyword'],
                        'emailCity': params['city_name'],
                        'subject': resume_id
                    },
                    "interfaceType": "PARSE",
                    "resourceDataType": "RAW",
                    "resourceType": "RESUME_SEARCH",
                    "source": self.site,
                    "trackId": str(resume_uuid),
                    'traceID': str(resume_uuid),
                    'callSystemID': self.common_settings.CALL_SYSTEM_ID,
                }
                self.save_data(
                    sql=sql, data=sql_value, msg_data=msg_data)
                self.is_limit()
            if has_next:
                page += 1
                continue
            else:
                RUN_STATUS[self.auth_kwargs['username']] = 0


def main():
    runner = Resume58City(
        local_setting={
            'TASK_TYPE': 'RESUME_FETCH',
            'SOURCE': 'FIVE_EIGHT',
            'SAVE_TYPE': 'mns'
        }
    )
    # runner.preview_settings()
    task_repush = 0
    while True:
        today = datetime.datetime.now()
        if today.hour < 7 or today.hour > 21:
            runner.logger.info("当前程序不再执行时间段内， sleep...")
            global RUN_STATUS
            RUN_STATUS = {}
            time.sleep(6000)
            continue
        task_id, params = runner.get_task()

        try:
            if not task_id:
                # 累计5次获取任务失败则推送任务
                task_repush += 1
                if task_repush == 5:
                    runner.start_push_task()
                    task_repush = 0
                continue
            try:
                runner.init_auth_kwargs()
                runner.resume_search(**params)
                runner.update_task(task_id=task_id)
                RUN_STATUS[runner.auth_kwargs['username']] = 0
            except MfCookieValidException as e:
                key = runner.auth_kwargs[
                    'username'].encode('utf-8')
                runner.h_account_limit.hset(key, 1)
                runner.robot_login.send_markdown(
                    title="58同城简历搜索",
                    content="#### 58同城简历搜索帐号被禁用.\n"
                            "- 帐号： %s\n"
                            "- 密码： %s\n"
                            "- 代理： %s\n\n"
                            % (
                                runner.auth_kwargs['username'].encode(
                                    'utf-8'),
                                runner.auth_kwargs['password'].encode(
                                    'utf-8'),
                                runner.auth_kwargs['proxy'].encode(
                                    'utf-8'))
                )
                runner.update_task(task_id=task_id, execute_result=str(e))
                RUN_STATUS[runner.auth_kwargs['username']] = 0
                continue

            except Exception as e:
                if 'no_resume_found' in e.message:
                    runner.logger.info('没有更多简历.')
                    runner.update_task(task_id=task_id, execute_result=str(e))
                    RUN_STATUS[runner.auth_kwargs['username']] = 0
                    continue

                if 'account_limit' in e.message:
                    runner.update_task(task_id=task_id, execute_result=str(e))
                    RUN_STATUS[runner.auth_kwargs['username']] = 0
                    continue

                runner.logger.exception(e)
                runner.update_task(task_id=task_id, execute_result=str(e))
                RUN_STATUS[runner.auth_kwargs['username']] = 0

        except Exception as e:
            runner.logger.exception(e)
            runner.update_task(task_id=task_id, execute_result=str(e))
            RUN_STATUS[runner.auth_kwargs['username']] = 0


if __name__ == '__main__':
    gevent.joinall([
        gevent.spawn(main, ) for i in xrange(
            settings.COROTINE_NUM
        )
    ])
    # main()
