#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: resume_fen.py
@create at: 2018-04-08 09:19

这一行开始写关于本文件的说明与解释
"""
import re

from gevent import monkey
monkey.patch_all()
import base64
import hashlib
import json
import random
import time
import datetime
import uuid
import gevent
from gevent.lock import BoundedSemaphore
from mf_utils.core import InitCorePlus
from mf_utils.decorates import cls_catch_exception, cls_refresh_cookie
from mf_utils.exceptions import MfCookieValidException
from mf_utils.data.RedisHash import RedisHash
from mf_utils.common import datetime2str, str2datetime
from conf.settings import project_settings
from create_task import CreateTask
from retrying import retry


TIME_LIMIT = 3

REDIS_HOST = '172.16.25.36'
REDIS_PORT = 6379
REDIS_PASSWORD = ''

locker = BoundedSemaphore(1)


class ResumeFen(InitCorePlus):
    def __init__(self, local_setting=project_settings):
        super(ResumeFen, self).__init__(
            local_setting=local_setting,
            # TEST
            # common_settings_path='/data/config/morgan/'
            #                      'morgan_spider_common_settings_test.cfg'
        )
        self.cookie = ''
        self.auth_kwargs = {}
        self.proxies = {
            'http': 'http://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun'
                    '.com:9020',
            'https': 'https://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun'
                     '.com:9020',
        }
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) ' \
                          'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                          'Chrome/62.0.3202.62 Safari/537.36'
        self.h_search_back_list = RedisHash('resume_fen_search_black_list',
                                            host=REDIS_HOST,
                                            port=REDIS_PORT,
                                            password=REDIS_PASSWORD)

        self.h_account_limit = RedisHash('resume_fen_account_limit',
                                         host=REDIS_HOST,
                                         port=REDIS_PORT,
                                         password=REDIS_PASSWORD)

        self.mns_handler = self.init_mns(
            endpoint='http://1315265288610488.mns.cn-beijing.aliyuncs.com',
            queue='morgan-queue-resume-raw'
            # TEST
            # queue='morgan-queue-test-resume-raw'
        )
        self.mysql_handler = self.init_mysql()

    def get_cookie(self):
        account = self.get_account(use_type='RESUME_FETCH')
        # print json.dumps(account, ensure_ascii=False)
        if account.get('code') == 200 and account.get('msg') == 'SUCCESS':
            self.cookie = account.get('data').get('cookie')
            self.auth_kwargs['username'] = account.get('data').get(
                'userName')
            self.auth_kwargs['password'] = account.get('data').get(
                'password'
            )
            self.logger.info('%s 获取cookie成功.' % account.get('data').get(
                'userName').encode('utf-8'))
            return self.cookie
        else:
            self.logger.warning('获取帐号失败： %s' % account)

    def invalid_cookie(self, username=None, password=None, url=None):
        # 添加cookie重试次数限制
        time.sleep(random.randint(1, 10))
        if not self.h_account_limit.hget(username):
            self.h_account_limit.hset(username, 1)
            return
        count = int(self.h_account_limit.hget(username))
        if count <= 5:
            count += 1
            self.h_account_limit.hset(username, count)
            self.logger.info('开始第%s次重新尝试 Cookie' % count)
            return

        return super(ResumeFen, self).invalid_cookie(username=username,
                                                     password=password,
                                                     url=url)

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def get_resume_list_zl(self, page, **kwargs):
        """
        智联模式
        :return:
        """
        url = 'http://www.fenjianli.com/search/search.htm'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'www.fenjianli.com',
            'Origin': 'http://www.fenjianli.com',
            'Pragma': 'no-cache',
            'Referer': 'http://www.fenjianli.com/search/home.htm',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'jobs': kwargs['job_code'],
            'updateDate': '7',
            'hareas': kwargs['area_code'],
            'rows': '30',
            'sortBy': '1',
            'sortType': '1',
            'offset': 30 * (page - 1),
            '_random': str(random.random()),
        }
        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            proxies=self.proxies,
                                            allow_redirects=False)

        if res.status_code == 302:
            self.logger.info('cookie_invalid: %s' % res.content)
            # self.invalid_cookie(self.auth_kwargs['username'],
            #                     self.auth_kwargs['password'])
            raise MfCookieValidException('cookie_invalid')

        if not res.json().get('list'):
            self.logger.warning('%s' % json.dumps(res.json(),
                                                  ensure_ascii=False))

            return

        self.logger.info('Page: %s 获取到%s份匹配的简历 [%s-%s]'
                         % (page, len(res.json().get('list')),
                            kwargs['area_name'].encode('utf-8'),
                            kwargs['job_name'].encode('utf-8')))

        return res.json().get('list')

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def get_resume_list_lp(self, page, **kwargs):
        """
        猎聘模式
        :return:
        """
        url = 'http://www.fenjianli.com/search/liepinSearch.htm'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'www.fenjianli.com',
            'Origin': 'http://www.fenjianli.com',
            'Pragma': 'no-cache',
            'Referer': 'http://www.fenjianli.com/search/liepinHome.htm',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'searchNear': 'on',
            'areas': kwargs['area_code'],
            'hJobs': kwargs['job_code'] + ',',
            'rows': '30',
            'sortBy': '1',
            'sortType': '1',
            'degree': '0-0',
            'offset': 30 * (page - 1),
            '_random': str(random.random()),
        }
        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            proxies=self.proxies,
                                            allow_redirects=False)

        if res.status_code == 302:
            self.logger.info('cookie_invalid: %s' % res.content)
            # print self.auth_kwargs
            # self.invalid_cookie(self.auth_kwargs['username'],
            #                     self.auth_kwargs['password'])
            raise MfCookieValidException('cookie_invalid')

        if not res.json().get('list'):
            self.logger.warning('%s' % json.dumps(res.json(),
                                                  ensure_ascii=False))
            return

        self.logger.info('Page: %s 获取到%s份匹配的简历 [%s-%s]'
                         % (page, len(res.json().get('list')),
                            kwargs['area_name'].encode('utf-8'),
                            kwargs['job_name'].encode('utf-8')))

        return res.json().get('list')

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def get_resume_detail(self, resume_id, mode='zl'):
        url = 'http://fenjianli.com/search/getDetail.htm'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'fenjianli.com',
            'Origin': 'http://fenjianli.com',
            'Pragma': 'no-cache',
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'id': resume_id,
            '_random': str(random.random())
        }

        if mode == 'zl':
            headers['Referer'] = 'http://www.fenjianli.com/search/' \
                                 'detail.htm?ids=' \
                                 + base64.b64encode(resume_id)
        else:
            headers['Referer'] = 'http://www.fenjianli.com/search/' \
                                 'liepinDetail.htm?ids=' \
                                 + base64.b64encode(resume_id)

        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            proxies=self.proxies,
                                            allow_redirects=False)
        if res.status_code == 302:
            self.logger.warning('cookie_invalid: %s' % res.content)
            raise MfCookieValidException('cookie_invalid_from_detail')

        if '登录异常，请联系客服处理' in res.content:
            self.logger.info('cookie_invalid: %s' % res.content)
            raise MfCookieValidException('cookie_invalid_from_detail')

        self.logger.info('获取简历详情成功: %s' % resume_id.encode('utf-8'))
        return res.json()

    def push_task(self):
        global locker
        locker.acquire()
        self.logger.info("开始推送纷简历任务.")
        creator = CreateTask()
        creator.create_task_from_mysql()
        locker.release()
        time.sleep(60)

    ######### 简历下载相关 ##########
    def find_customer_channel_account(self, resume_id):
        url = 'http://www.fenjianli.com/userResumeDetail/' \
              'findCustomerChannelAccount.htm'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Length': '26',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'www.fenjianli.com',
            'Origin': 'http://www.fenjianli.com',
            'Pragma': 'no-cache',
            'Referer': 'http://www.fenjianli.com/search/detail.htm?type=1'
                       '&ids=%s' % base64.b64encode(resume_id),
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            '_random': random.random()
        }
        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            allow_redirects=False,
                                            proxies=self.proxies)
        if res.status_code == 302 or 'error' in res.json():
            self.logger.warning('cookie_invalid: %s' % res.content)
            raise MfCookieValidException('cookie_invalid')

        self.logger.info('%s' % res.content)
        return res.json()

    def tree_of_folder_catalog(self, resume_id):
        url = 'http://www.fenjianli.com/folderCatalog/treeOfFolderCatalog.htm'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Length': '26',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'www.fenjianli.com',
            'Origin': 'http://www.fenjianli.com',
            'Pragma': 'no-cache',
            'Referer': 'http://www.fenjianli.com/search/detail.htm?type=1'
                       '&ids=%s' % base64.b64encode(resume_id),
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'folderCatalogType': 'Download',
            '_random': random.random()
        }
        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            allow_redirects=False,
                                            proxies=self.proxies)
        if res.status_code == 302 or 'error' in res.json():
            self.logger.warning('cookie_invalid: %s' % res.content)
            raise MfCookieValidException('cookie_invalid')

        self.logger.info('%s' % res.content)
        return res.json()

    def add_to_folder_catalog(self, resume_id, ids, folder_catalog_id):
        url = 'http://www.fenjianli.com/userResumeDetail/' \
              'addToFolderCatalog.htm'
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Length': '26',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'www.fenjianli.com',
            'Origin': 'http://www.fenjianli.com',
            'Pragma': 'no-cache',
            'Referer': 'http://www.fenjianli.com/search/detail.htm?type=1'
                       '&ids=%s' % base64.b64encode(resume_id),
            'User-Agent': self.user_agent,
            'Cookie': self.cookie,
            'X-Requested-With': 'XMLHttpRequest',
        }
        data = {
            'ids': ids,
            'folderCatalogId': folder_catalog_id,
            'folderCatalogType': 'Download',
            'type': 'add',
            'isResumeId': 'true',
            '_random': random.random()
        }
        res = self.html_downloader.download(url, method='POST',
                                            headers=headers,
                                            data=data,
                                            allow_redirects=False,
                                            proxies=self.proxies)
        if res.status_code == 302 or 'error' in res.json():
            self.logger.warning('cookie_invalid: %s' % res.content)
            raise MfCookieValidException('cookie_invalid')

        self.logger.info('%s' % res.content)
        return res.json()

    @retry(stop_max_attempt_number=5)
    @cls_catch_exception
    @cls_refresh_cookie
    def download_resume(self, resume_id):
        resume_detail = self.get_resume_detail(resume_id)
        if not resume_detail:
            self.logger.info('获取简历详情失败. %s' % resume_id.encode('utf-8'))
            raise MfCookieValidException('get_resume_detail_failed.')

        self.find_customer_channel_account(resume_id)
        tree_folder = self.tree_of_folder_catalog(resume_id)
        folder_catalog_id = re.findall('(?<=id:)\d+(?=, pId:[1-9])',
                                       tree_folder.get('data'))[0]
        ids = resume_id.encode('utf-8') + '/' + resume_detail.get(
            'name').encode('utf-8')
        self.logger.info('%s: 开始执行下载操作： %s - %s' % (
            self.auth_kwargs['username'].encode('utf-8'),
            ids, folder_catalog_id.encode('utf-8')
        ))

        res = self.add_to_folder_catalog(resume_id, ids, folder_catalog_id)
        if '下载简历成功[1]份' in res:
            self.logger.info('下载成功')
            return self.get_resume_detail(resume_id)
        else:
            self.logger.info('下载失败： %s' % res)
            return


def execute_awake():
    runner = ResumeFen()
    while True:
        task_id, params = runner.get_task()
        if not task_id:
            runner.push_task()
            continue

        try:
            runner.get_cookie()
            page = 1
            has_next_page = True
            while has_next_page:
                if params.get('model_name') == 'ZHI_LIAN':
                    mode = 'zl'
                    resume_list = runner.get_resume_list_zl(page, **params)
                else:
                    mode = 'lp'
                    resume_list = runner.get_resume_list_lp(page, **params)

                if not resume_list:
                    runner.logger.warning('简历列表为空，开始切换任务.')
                    runner.update_task(task_id=task_id)
                    break

                flag = 0
                for resume in resume_list:
                    resume_id = resume.get('id').encode('utf-8')
                    day = datetime.datetime.now().day
                    today = datetime2str(datetime.datetime.now(),
                                         '%Y-%m-%d')
                    last_search_day = runner.h_search_back_list.hget(
                        resume_id)

                    if flag > 25:
                        runner.logger.info('当前页存在超过25个已采集简历，跳过任务.')
                        has_next_page = False
                        break

                    # 用于去重天数限制 TIME_LIMIT
                    if last_search_day:
                        last_search_day = str2datetime(last_search_day,
                                                       fmt='%Y-%m-%d').day

                        if day - last_search_day <= TIME_LIMIT:
                            runner.logger.warning('该简历[%s] %s天内已采集过.'
                                                  % (resume_id, TIME_LIMIT))
                            flag += 1
                            continue

                    content = runner.get_resume_detail(
                        resume_id=resume_id, mode=mode
                    )

                    if not content:
                        continue

                    content = json.dumps(content, ensure_ascii=False)

                    resume_uuid = str(uuid.uuid1())

                    sql = '''insert into spider_search.resume_raw (source, content, 
                                createBy, 
                                trackId, createtime, email, emailJobType, emailCity, subject) values 
                                (%s, %s, "python", %s, now(), %s, %s, %s, %s)'''
                    sql_value = (
                        runner.common_settings.SOURCE, content, resume_uuid,
                        runner.auth_kwargs['username'], params['job_name'],
                        params['area_name'], str(resume_id))

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
                            "source": runner.common_settings.SOURCE,
                            "trackId": str(resume_uuid),
                            "avatarUrl": '',
                            "email": runner.auth_kwargs['username'],
                            'emailJobType': params['job_name'],
                            'emailCity': params['area_name'],
                            'subject': resume_id
                        },
                        "interfaceType": "PARSE",
                        "resourceDataType": "RAW",
                        "resourceType": "RESUME_SEARCH",
                        "source": runner.common_settings.SOURCE,
                        "trackId": str(resume_uuid),
                        'traceID': str(resume_uuid),
                        'callSystemID': runner.common_settings.CALL_SYSTEM_ID,
                    }
                    # self.mysql_handler.save(sql=sql, data=sql_value)
                    res = runner.save_data(sql=sql, data=sql_value,
                                           msg_data=msg_data)
                    if res:
                        # 重置cookie重试次数
                        runner.h_account_limit.hset(
                            runner.auth_kwargs['username'], 0)
                        runner.h_search_back_list.hset(resume_id, today)
                    time.sleep(random.randint(1, 5))
                if len(resume_list) < 30:
                    runner.logger.info('当前页简历小于30，任务结束。')
                    has_next_page = False

                page += 1
                runner.update_task(task_id=task_id)

        except MfCookieValidException:
            runner.update_task(task_id=task_id)
            runner.add_task(param=json.dumps(params, ensure_ascii=False))
            runner.logger.warning('因Cookie失败导致任务退出，重新添加任务！')

        except Exception as e:
            runner.update_task(task_id=task_id, execute_status='FAILURE',
                               execute_result=str(e))
            runner.logger.exception(str(e))


if __name__ == '__main__':
    runner = ResumeFen()
    runner.preview_settings()
    # exit()
    gevent.joinall([
        gevent.spawn(execute_awake) for i in xrange(1)
    ])
    # execute_awake()
