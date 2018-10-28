#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/16 0016 15:40
# @Author  : huangyee
# @Email   : 1173842904@qq.com
# @File    : zhilian_email_mobile.py
# @description 智联邮箱采集邮件解析获取联系方式
# @Software: PyCharm

from mf_utils.extend.dingding_robot import DingDingRobot
from mf_utils.core import InitCore
from MySQLdb.cursors import DictCursor
from mf_utils.logger import Logger
import json
import random
import datetime
import requests
import re
from lxml import etree
import time
import sys
from mf_utils.common import remove_emoji
from mf_utils.queue.RedisQueue import RedisQueue
import threading

lock = threading.Lock()

reload(sys)
sys.setdefaultencoding("utf8")

STATIC_PROXIES = [
    ['114.116.54.129', '5000'],
    ['114.116.55.213', '5000'],
    ['114.116.51.55', '5000'],
    ['114.116.54.74', '5000'],
    ['114.116.55.57', '5000'],
    ['114.116.50.225', '5000'],
    ['114.116.51.197', '5000'],
    ['114.116.53.13', '5000'],
    ['114.116.51.87', '5000'],
    ['114.116.49.139', '5000'],
    ['114.116.55.229', '5000'],
    ['114.116.55.200', '5000'],
    ['114.116.51.163', '5000'],
    ['114.116.53.104', '5000'],
    ['114.116.53.17', '5000'],
    ['114.116.55.139', '5000'],
    ['114.116.55.124', '5000'],
    ['114.116.48.237', '5000'],
    ['114.116.86.255', '5000'],
    ['114.116.50.168', '5000'],
]

at_mobiles = ['15367117098']


def get_proxy():
    global STATIC_PROXIES
    p = random.choice(STATIC_PROXIES)
    return {'http': 'http://%s:%s' % (p[0], p[1]), 'https': 'http://%s:%s' % (p[0], p[1])}


class ZhiLianEmailMobile(InitCore):
    def __init__(self):
        super(ZhiLianEmailMobile, self).__init__(
        )
        self.mns_handler = self.init_mns(
            endpoint='http://1315265288610488.mns.cn-beijing.aliyuncs.com',
            # queue='morgan-queue-resume-raw'
            queue='morgan-queue-resume-raw'
        )
        # self.spider_admin = self.init_mysql(host='10.0.3.52',
        #                                     port=3306,
        #                                     user='bi_admin',
        #                                     passwd='bi_admin#@1mofanghr',
        #                                     db='spider', cursorclass=DictCursor)
        self.spider_admin = self.init_mysql(host='rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
                                            port=3306,
                                            user='spider_admin',
                                            passwd='n4UZknFH6F',
                                            db='spider', cursorclass=DictCursor)

        self.robot = DingDingRobot(
            access_token="2d021b9d686a5432aa0d65f0e75d03bc6200d2b766616c75224d8e7bfb1cbc57")

        self.logger = Logger.timed_rt_logger()
        self.q = RedisQueue('zhi_lian_need_get_mobile', host='172.16.25.36',
                            port=6379)

    def prepare_resume_ids(self):
        if lock.locked():
            return
        lock.acquire()
        try:
            download_record_sql = '''
                    SELECT * FROM spider.download_record WHERE source=3 AND valid=0 
                    ORDER BY id ASC LIMIT 100
                    '''
            result = self.spider_admin.query_by_sql(download_record_sql)
            if len(result) == 0 or not result:
                self.logger.info('没有需要下载的简历了 %s' % download_record_sql)
                time.sleep(60)
                lock.release()
                return
            for item in result:
                self.q.put(item)
            self.logger.info('任务添加完成 %s' % self.q.qsize())
        except Exception as e:
            self.logger.exception(str(e))

        lock.release()

    def load_data(self, result):
        """
        加载需要请求的数据
        valid为0，标识待下载
               2，标识下载完成
        :return:
        """
        self.logger.info('加载 %s 记录 %s'
                         % (result['id'], result['resumeId'].encode('utf-8')))

        sql = '''
                   select * from spider.resume_raw WHERE id =%s
                   ''' % result['resumeId'].encode('utf-8')
        data_lst = self.spider_admin.query_by_sql(sql)
        self.logger.info("获取简历成功: %s" % len(data_lst))
        if len(data_lst) > 0:
            raw_data = data_lst[0]
            # origin_url = re.search('(https://ihr\.zhaopin\.com/job/relay\.html?.*?)">我要联系TA', data_lst[0]['content'])
            origin_url = re.search('(https://ihr.*?)">我要联系TA</a>', data_lst[0]['content'].encode('utf-8'))
            if origin_url:
                origin_url = origin_url.group(1)
                raw_data['origin_url'] = origin_url
                raw_data['download_id'] = result['id']
                return raw_data
            else:
                self.logger.warning('未匹配到获取联系方式的.')
                self.update_record(result['id'], 3)
        else:
            self.logger.error('没有找到简历原文 %s ' % (result['resumeId'].encode('utf-8')))
        return None

    def update_record(self, id, result):
        """
        更新download_record的值
        :param id:
        :param result:
        :return:
        """
        sql = '''
            UPDATE spider.download_record SET valid=%s WHERE id=%s
        '''
        result = self.spider_admin.save(sql, [result, id])
        self.logger.info('%s download_record 修改成功 %s' % (id, result))

    def load_html(self, origin_url):
        """
        请求联系方式页面
        :param origin_url:
        :return:
        """
        proxy = get_proxy()
        self.logger.info('当前使用的代理为： %s' % proxy)
        session = requests.session()
        content1 = session.get(url=origin_url, proxies=proxy, headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'ihr.zhaopin.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }).content
        document = etree.HTML(content1)
        name = document.xpath('//div[@class="login_content"]/p')[0].xpath('//a')[0].text
        if not name:
            params = re.search('param=(.*?)$', origin_url)
            if params:
                params = params.group(1)
            else:
                return None
            url = '''https://ihr.zhaopin.com/resumemanage/emailim.do?s=%s''' % params
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Host': 'ihr.zhaopin.com',
                'Referer': 'https://ihr.zhaopin.com/job/relay.html?param=%s' % params,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            content = session.get(url=url, headers=headers, proxies=proxy, allow_redirects=True).content
            self.logger.info('%s' % content)
            if '近期我们监控到您所用的IP地址出现风险，您的IP地址是' in content and '临时将此IP地址进行安全保护，但可能导致您无法正常登陆' in content and '如有问题，请与客服联系，给您带来的不便，敬请谅解' in content:
                self.robot.send_text('代理不能正常使用 %s ' % proxy)
                return None
            if content:
                data = json.loads(content, encoding='utf-8')
                if data['code'] == 200:
                    return json.loads(content, encoding='utf-8')
        return None

    def push_mns(self, raw_data):

        try:
            msg_data = {
                "channelType": "WEB",
                "content": {
                    "content": raw_data['content'],
                    "id": raw_data['id'],
                    "createBy": "python",
                    "createTime": str(raw_data['createTime']),
                    "ip": '',
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": str(raw_data['resumeUpdateTime']),
                    "source": raw_data['source'],
                    "trackId": str(raw_data['trackId']),
                    "avatarUrl": '',
                    "email": raw_data['email'],
                    'emailJobType': raw_data['emailJobType'],
                    'emailCity': raw_data['emailCity'],
                    'subject': raw_data['subject'],
                    'externalInfo': raw_data['externalInfo']
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_EMAIL",
                "source": raw_data['source'],
                "trackId": raw_data['trackId'],
                'traceID': raw_data['trackId'],
                'callSystemID': 'resume_awake_search',
            }
            dumps = json.dumps(msg_data, ensure_ascii=False).encode('utf-8')
            dumps = remove_emoji(dumps)
            self.mns_handler.save(dumps)
            self.logger.info('推送成功： %s' % raw_data['id'])
        except Exception as e:
            self.logger.exception(str(e))


def process():
    zhilian_email_mobile = ZhiLianEmailMobile()
    while True:
        try:
            if zhilian_email_mobile.q.empty():
                zhilian_email_mobile.prepare_resume_ids()
                continue

            resume = eval(zhilian_email_mobile.q.get())
            raw_data = zhilian_email_mobile.load_data(resume)
            if not raw_data:
                continue
            else:
                try:
                    touch_content = zhilian_email_mobile.load_html(raw_data['origin_url'])
                    # touch_content = {u'message': u'\u64cd\u4f5c\u6210\u529f', u'code': 200,
                    #                  u'data': {u'username': u'\u5f20\u7389\u6167',
                    #                            u'phone': u'18926874933', u'gid': u'511450440703',
                    #                            u'email': u'244364808@qq.com'},
                    #                  u'taskId': u'0-0fecb3a5-a89b-424b-8d9f-29099b9edf6c', u'time': u'2018-04-16 18:17:54'}
                    zhilian_email_mobile.logger.info('%s 返回的联系方式内容： %s' % (raw_data['id'], touch_content))
                    if touch_content:
                        raw_data['externalInfo'] = touch_content
                        zhilian_email_mobile.push_mns(raw_data)
                        """
                        result 为2，表示下载完成，1表示初始状态
                        """
                        zhilian_email_mobile.update_record(raw_data['download_id'], 2)
                        zhilian_email_mobile.logger.info('%s 处理完毕' % (raw_data['id']))
                    else:
                        zhilian_email_mobile.logger.error('%s 联系方式获取失败 ' % raw_data['id'])
                        zhilian_email_mobile.robot.send_text(
                            'python-简历获取联系方式失败 rawid:%s，返回的内容为：\n %s' % (raw_data['id'], touch_content),
                            at_mobiles=at_mobiles)
                except Exception as e:
                    zhilian_email_mobile.logger.exception(str(e))
                    zhilian_email_mobile.robot.send_text('python-简历获取联系方式失败 rawid:%s' % raw_data['id'])
        except Exception as e:
            zhilian_email_mobile.logger.exception(e)
            continue

    pass


if __name__ == '__main__':
    thread_lst = []
    for i in xrange(4):
        t = threading.Thread(target=process, name='Thread-%s' % i)
        t.start()
        thread_lst.append(t)

    for t in thread_lst:
        t.join()
