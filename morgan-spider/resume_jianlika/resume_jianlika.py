#!coding:utf8
import sys

sys.path.append('../common')
import requests
import time
import traceback
import json
import random
# import logging
# from logging.handlers import RotatingFileHandler
import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import uuid
import datetime
import redis
import settings
import threading
from mns.account import Account
from mns.queue import Message
import gzip
from cStringIO import StringIO
import base64
import common_settings
import utils
import Queue
from lxml import etree
import create_task
import urllib
import re

stop_tag = False
sleep_tag = True
get_task_queue = None
push_task_time = None
push_task_keyword_tag = '0'
push_task_lock = threading.Lock()
get_coin_re = re.compile('<a href="/Property/index.html"><i class="ico-png-money"></i><span>(\d+)</span></a>')


class DingDingRobot(object):
    def __init__(self, access_token=None, api_url="https://oapi.dingtalk.com/robot/send?access_token="):
        self.api_url = api_url
        self.header = {'Content-Type': 'application/json'}
        self.access_token = access_token
        self.session = requests.session()
        self.session.headers = self.header

    def send_text(self, content, at_mobiles=list(), is_at_all=False):
        try:
            data = {
                "text": {
                    "content": content
                },
                "msgtype": "text",
                "at": {
                    "isAtAll": is_at_all,
                    "atMobiles": at_mobiles
                }
            }

            res = self.session.post(self.api_url + self.access_token,
                                    data=json.dumps(data))
            return res
        except Exception as e:
            logger.info(str(traceback.print_exc(e)))
            return None

    def send_markdown(self, title, content, at_mobiles=list(), is_at_all=False):
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": content
                },
                "at": {
                    "atMobiles": at_mobiles,
                    "isAtAll": is_at_all
                }
            }

            res = self.session.post(self.api_url + self.access_token, data=json.dumps(data))
            return res
        except Exception as e:
            logger.info(str(traceback.print_exc(e)))
            return None

    def send_action_card(self, title, content, hide_avatar="0", btn_oriengtation="0", single_title="阅读全文",
                         single_url="#"):
        try:
            data = {
                "actionCard": {
                    "title": title,
                    "text": content,
                    "hideAvatar": hide_avatar,
                    "btnOrientation": btn_oriengtation,
                    "singleTitle": single_title,
                    "singleURL": single_url
                },
                "msgtype": "actionCard"
            }
            res = self.session.post(self.api_url + self.access_token, data=json.dumps(data))
            return res
        except Exception as e:
            logger.info(str(traceback.print_exc(e)))
            return None

    def send_feed_card(self, links):
        """

        :param links: array[{'title':'', 'messageURL':'', 'picURL':''}]
        :return:
        """
        try:
            data = {
                "feedCard": {
                    "links": links
                },
                "msgtype": "feedCard"
            }
            res = self.session.post(self.api_url + self.access_token, data=json.dumps(data))
            return res
        except Exception as e:
            logger.info(str(traceback.print_exc(e)))
            return None


dingding_robot = None


def send_dingding_text(text):
    global dingding_robot
    if not dingding_robot:
        dingding_robot = DingDingRobot('eb749abfe9080a69da6524b77f589b8f6ddbcc182c7a41bf095b095336edb0a1')
    dingding_robot.send_text(text)


def push_task():
    logger = utils.get_logger()
    global push_task_time
    global push_task_lock
    global push_task_keyword_tag
    if push_task_lock.locked():
        return
    push_task_lock.acquire()
    if not push_task_time or (datetime.datetime.now() - push_task_time).seconds > 14400:
        send_dingding_text(u'开始推送简历咖简历任务.')
        create_task.create_task_from_mysql(push_task_keyword_tag)
        push_task_keyword_tag = '0' if push_task_keyword_tag == '1' else '1'
        push_task_time = datetime.datetime.now()
    push_task_lock.release()


def get_one_account(download=False):
    """
    获取账户
    :param download:
    :return:
    """
    # return {'username': 'test130279237', 'passwd': 'jinqian4611', 'id': 805}, 'gift_hide_timeout=1; AWSELB=4B9B4BE516A95C5CEC852C0DFA15D4E95B0DF84E43ABD0E3E867DF4A41D7C97A3E4321B6AD083CC33CEF2345183B0208E7613A0665994376C81E292BDA81FBD4A05045A034; think_language=zh-CN; PHPSESSID=3mt68rpaf839o7j9hs7oo30o14'
    logger = utils.get_logger()
    if download:
        url = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'RESUME_INBOX')
    else:
        url = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'RESUME_FETCH')
    logger.info('开始获取账户 %s ' % url)
    while True:
        try:
            response = requests.get(url, timeout=10)
            response_json = response.json()
            if response_json['code'] in [200, '200'] and response_json['data']:
                account = {'username': response_json['data']['userName'], 'passwd': response_json['data']['password'],
                           'id': response_json['data']['id'], 'downloadScore': response_json['data']['downloadScore'],
                           'freshScore': response_json['data']['freshScore']}
                cookie = json.loads(response_json['data']['cookie'], encoding='utf-8')
                # cookie = json.loads(response_json['data']['cookie'])
                if not cookie:
                    logger.info('not get cookie in result, set to relogin and try again.')
                    # set_unavaliable_account(account)
                    continue
                # cookie_list = eval(cookie)
                cookie_str = []
                for cookie_ in cookie:
                    cookie_str.append(cookie_.get('name') + '=' + cookie_.get('value'))
                cookie_str = ';'.join(cookie_str)
                print cookie_str
                logger.info('using account:' + response.text)
                return account, cookie_str
        except Exception, e:
            logger.info('get error when get search account:' + str(traceback.format_exc()))
        time.sleep(60)


def set_unavaliable_account(account):
    logger = utils.get_logger()
    logger.info('set unavaliable :' + str(account))
    time.sleep(2)
    url = common_settings.SET_INVALID_URL % (
        str(account['username']), str(account['passwd']), str(settings.project_settings.get("SOURCE")))
    try:
        logger.info('失效账户 %s' % url)
        response = requests.get(url)
        logger.info('set unavaliable account response:' + response.text)
    except Exception, e:
        logger.info(str(traceback.format_exc()))


def set_forbidden_account(account):
    logger = utils.get_logger()
    logger.info('set forbidden :' + str(account))
    time.sleep(2)
    url = settings.project_settings.get('SET_FORBIDDEN_URL') % (account['username'], account['passwd'])
    try:
        # pass
        response = requests.get(url)
        send_dingding_text(u'简历咖账号异常:%s' % account['username'])
        logger.info('set forbidden account response:' + response.text)
    except Exception, e:
        logger.info(str(traceback.format_exc()))


redis_client = None


def get_redis_client():
    global redis_client
    if not redis_client:
        # redis_pool = redis.ConnectionPool(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
        # redis_client = redis.Redis(redis_pool)
        redis_client = redis.Redis(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
    return redis_client


def update_coin_number_left(account, coin_number):
    logger = utils.get_logger()
    logger.info('update coin number:' + str(account) + ' ' + str(coin_number))
    url = settings.project_settings.get('UPDATE_DOWNLOAD_SCORE')
    data = {
        # 'id': account['id'],
        'downloadRecord': coin_number,
        'userName': account['username'],
        'password': account['passwd'],
        'source': common_settings.SOURCE,
    }
    try:
        response = requests.post(url, data=data)
    except Exception, e:
        logger.info(str(traceback.format_exc()))


def update_refresh_score(account):
    """
    更新下载点
    :param account:
    :return:
    """
    logger = utils.get_logger()
    logger.info('更新下载点:' + str(account))
    url = settings.project_settings.get('UPDATE_DOWNLOAD_SCORE')
    data = {
        # 'id': account['id'],
        'freshScore': account['freshScore'] - 1,
        'userName': account['username'],
        'password': account['passwd'],
        'source': settings.project_settings.get('SOURCE'),
    }
    try:
        response = requests.post(url, data=data)
    except Exception, e:
        logger.info(str(traceback.format_exc()))


def awake_thread():
    """
    搜索线程
    :return:
    """
    logger = utils.get_logger()
    logger.info('开始执行搜索')
    global stop_tag
    global sleep_tag
    while not stop_tag:
        while not sleep_tag:
            logger.info('当前不进行搜索，进入睡眠.')
            time.sleep(3600)
        task_traceid = str(uuid.uuid1())
        params = {'traceID': task_traceid, 'callSystemID': settings.project_settings.get('CALLSYSTEMID'),
                  'taskType': settings.project_settings.get('TASK_TYPE'),
                  'source': settings.project_settings.get('SOURCE'), 'limit': 1}
        param_str = '&'.join([str(i) + '=' + str(params[i]) for i in params])
        task_url = common_settings.TASK_URL + common_settings.GET_TASK_PATH + param_str
        logger.info(task_url)
        task_result = utils.download(url=task_url, is_json=True)
        if task_result['code'] or task_result['json']['code'] not in [200, '200']:
            logger.info('获取任务异常:' + task_url + ' return is:' + str(task_result))
            time.sleep(settings.project_settings.get('SERVER_SLEEP_TIME'))
            continue
        logger.info('获取到任务了 ' + str(task_result))
        if not task_result['json']['data']:
            logger.info('没有获取到任务了，重新推一轮:' + str(task_result))
            push_task()
            time.sleep(120)
            continue
        process_result = {'code': -1, 'executeParam': task_result['json']['data'][0]['executeParam']}
        try:
            process_result = awake_one_task(json.loads(task_result['json']['data'][0]['executeParam']))
            # print '---------------the process_result:', process_result
        except Exception, e:
            logger.info('任务执行异常:' + str(traceback.format_exc()))
        return_task_url = common_settings.TASK_URL + common_settings.RETURN_TASK_PATH
        return_task_traceid = str(uuid.uuid1())
        return_data = {}
        return_data['traceID'] = return_task_traceid
        return_data['callSystemID'] = settings.project_settings.get('CALLSYSTEMID')
        return_data['uuid'] = task_result['json']['data'][0]['uuid']
        # return_data['executeResult'] = process_result.get('executeResult', '')
        if not process_result.get('code', True):
            return_data['executeStatus'] = 'SUCCESS'
        else:
            return_data['executeStatus'] = 'FAILURE'
            logger.info('get a failed return of task!!!')
        for x in xrange(3):
            try:
                logger.info('send return task time ' + str(x))
                return_task_result = utils.download(url=return_task_url, is_json=True, method='post', data=return_data)
                # print return_task_result
                if not return_task_result['code'] and return_task_result['json']['code'] in [200, '200']:
                    break
            except Exception, e:
                logger.info('error when send return task:' + str(traceback.format_exc()))

        if process_result.get('code', True) and process_result.get('executeParam', ''):
            logger.info('start create task!!!')
            for insert_count in xrange(3):
                try:
                    logger.info('create task time ' + str(insert_count))
                    insert_url = common_settings.TASK_URL + common_settings.CREATE_TASK_PATH
                    insert_task_traceid = str(uuid.uuid1())
                    insert_data = {
                        'traceID': insert_task_traceid,
                        'callSystemID': settings.project_settings.get('CALLSYSTEMID'),
                        'taskType': common_settings.TASK_TYPE,
                        'source': settings.project_settings.get('SOURCE'),
                        'executeParam': task_result['json']['data'][0]['executeParam'],
                        'parentUuid': task_result['json']['data'][0]['uuid'],
                        # 'deadline': task_result['json']['data'][0]['deadline'],
                    }
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    }
                    insert_result = utils.download(url=insert_url, is_json=True, headers=headers, method='post',
                                                   data=insert_data)
                    logger.info('insert result:' + str(insert_result))
                    if not insert_result['code'] and insert_result['json']['code'] in [200, '200']:
                        break
                except Exception, e:
                    logger.info('error when create task:' + str(traceback.format_exc()))

        # time.sleep(5)


def get_mns_client():
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY,
                          common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client


def change_time_thread():
    """
    设置程序睡眠，比如一天只能抓取多少，及几点到几点抓取
    :return:
    """
    logger = utils.get_logger()
    logger.info('start check time!!!')
    # global change_time_tag
    global stop_tag
    global numbers_left
    global sleep_tag
    start_day = datetime.datetime.now().day
    while not stop_tag:
        hour_now = datetime.datetime.now().hour
        # if not change_time_tag and start_day != datetime.datetime.now().day:
        if start_day != datetime.datetime.now().day:
            start_day = datetime.datetime.now().day
            numbers_left = settings.project_settings.get('NUMBERS_ERVERYDAY')
            logger.info('has change day, start_day is ' + str(start_day))
        # if hour_now > 4 and hour_now < 23:
        #     sleep_tag = True
        # else:
        #     sleep_tag = False
        time.sleep(3600)


def get_list(cookie, page_numner, token, params, proxy=None):
    """
    获取列表页面a
    :param cookie:
    :param page_numner:
    :param token:
    :param params:
    :param proxy:
    :return:
    """
    logger = utils.get_logger()
    result = {'code': 0, 'data': [], 'has_next_page': False}
    logger.info('use proxy ' + str(proxy) + ' to download list')

    try:
        if page_numner != 1:
            list_url = 'http://www.jianlika.com/Search/result/token/%s/p/%s.html' % (token, page_numner)
            list_header = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Referer': 'http://www.jianlika.com/Search/result/token/%s/p/%s.html' % (token, page_numner - 1),
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            }

            list_response = requests.get(list_url, headers=list_header, proxies=proxy, allow_redirects=False,
                                         timeout=30)
            # print cookie
            # if list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/login.jsp?errMsg=':
            #         logger.info('invalid cookie, need login.')
            #         result['code'] = 5
            #         return result
            # elif list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
            #     logger.info('list response status headers:'+str(list_response.headers))
            #     result['code'] = 6
            #     return result
            if list_response.status_code in [302, '302'] and list_response.headers.get('Location') == '/':
                result['code'] = 4
                return result
            if list_response.status_code not in [200, '200']:
                logger.info('list response status code:' + str(list_response.status_code))
                result['code'] = 1
                return result
        else:
            list_url1 = 'http://www.jianlika.com/Search/index.html'
            list_header1 = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Origin': 'http://www.jianlika.com',
                'Referer': 'http://www.jianlika.com/Search/index.html',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            list_data1 = {
                'keywords': '',
                'companyName': '',
                'searchNear': 'on',
                'jobs': '',
                'trade': '',
                'areas': params['areas'],
                'hTrade': '',
                'hJobs': params['hJobs'],
                'degree': '',
                'workYearFrom': '',
                'workYearTo': '',
                'ageFrom': '',
                'ageTo': '',
                'sex': '0',
                'updateDate': '3',
            }
            list_response1 = requests.post(list_url1, headers=list_header1, data=list_data1, allow_redirects=False,
                                           proxies=proxy, timeout=30)
            if list_response1.status_code not in [200, '200']:
                logger.info('list response status code:' + str(list_response1.status_code))
                result['code'] = 2
                return result
            logger.info(list_response1.text)
            list_json1 = list_response1.json()
            if list_json1.get('status', '') not in [1, '1'] and not list_json1.get('url', ''):
                logger.info('get error list response1:' + list_response1.text)
                result['code'] = 3
                return result
            if list_json1.get('url', '') == '/':
                result['code'] = 4
                return result
            list_url = 'http://www.jianlika.com' + list_json1['url']
            list_header = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Referer': 'http://www.jianlika.com/Search/index.html',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            }
            list_response = requests.get(list_url, headers=list_header, allow_redirects=False, proxies=proxy,
                                         timeout=30)
            if list_response1.status_code not in [200, '200']:
                logger.info('list response status code:' + str(list_response1.status_code))
                result['code'] = 5
                return result
            result['token'] = list_json1['url'].split('/')[-1].split('.')[0]
        list_root = etree.HTML(list_response.text)
        a_list = list_root.xpath('//td[@width="215"]/a[@target="_blank"]')
        ids = []
        for a in a_list:

            # href = a.attrib.get('href', '')
            #  2018-04-09 新的详情页面链接获取
            href = a.attrib.get('data-href', '')
            resume_id = a.attrib.get('title', '')
            if not href or not resume_id:
                continue

            ids.append(['http://www.jianlika.com' + href, resume_id])

        # ids = list(set(ids))
        # if [] in ids:
        #     ids.remove('')
        result['data'] = ids
        if list_root.xpath('//a[@aria-label="Next"]'):
            result['has_next_page'] = True
            # f=open('123', 'w')
            # f.write(list_response.text.encode('utf8'))
            # f.close()
        else:
            result['has_next_page'] = False
        return result
    except Exception, e:
        logger.info(str(traceback.format_exc()))
    result['code'] = 3
    return result


def get_list_with_keyword(cookie, page_numner, token, params, proxy=None):
    """
    根据关键字获取列表页面
    :param cookie:
    :param page_numner:
    :param token:
    :param params:
    :param proxy:
    :return:
    """
    logger = utils.get_logger()
    result = {'code': 0, 'data': [], 'has_next_page': False}
    logger.info('use proxy ' + str(proxy) + ' to download list')

    try:
        if page_numner != 1:
            list_url = 'http://www.jianlika.com/Search/result/token/%s/p/%s.html' % (token, page_numner)
            list_header = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Referer': 'http://www.jianlika.com/Search/result/token/%s/p/%s.html' % (token, page_numner - 1),
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            }

            list_response = requests.get(list_url, headers=list_header, proxies=proxy, allow_redirects=False,
                                         timeout=30)
            # print cookie
            # if list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/login.jsp?errMsg=':
            #         logger.info('invalid cookie, need login.')
            #         result['code'] = 5
            #         return result
            # elif list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
            #     logger.info('list response status headers:'+str(list_response.headers))
            #     result['code'] = 6
            #     return result
            if list_response.status_code in [302, '302'] and list_response.headers.get('Location') == '/':
                result['code'] = 4
                return result
            if list_response.status_code not in [200, '200']:
                logger.info('list response status code:' + str(list_response.status_code))
                result['code'] = 1
                return result
        else:
            list_url1 = 'http://www.jianlika.com/Search/index.html'
            list_header1 = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Origin': 'http://www.jianlika.com',
                'Referer': 'http://www.jianlika.com/Search/index.html',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            list_data1 = {
                'keywords': params['keywords'],
                'companyName': '',
                'searchNear': 'on',
                'jobs': '',
                'trade': '',
                'areas': params['areas'],
                'hTrade': '',
                'hJobs': '',
                'degree': '',
                'workYearFrom': '',
                'workYearTo': '',
                'ageFrom': '',
                'ageTo': '',
                'sex': '0',
                'updateDate': '3',
            }
            list_response1 = requests.post(list_url1, headers=list_header1, data=list_data1, allow_redirects=False,
                                           proxies=proxy, timeout=30)
            if list_response1.status_code not in [200, '200']:
                logger.info('list response status code:' + str(list_response1.status_code))
                result['code'] = 2
                return result
            logger.info(list_response1.text)
            list_json1 = list_response1.json()
            if list_json1.get('status', '') not in [1, '1'] and not list_json1.get('url', ''):
                logger.info('get error list response1:' + list_response1.text)
                result['code'] = 3
                return result
            if list_json1.get('url', '') == '/':
                result['code'] = 4
                return result
            list_url = 'http://www.jianlika.com' + list_json1['url']
            list_header = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Referer': 'http://www.jianlika.com/Search/index.html',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            }
            list_response = requests.get(list_url, headers=list_header, allow_redirects=False, proxies=proxy,
                                         timeout=30)
            if list_response1.status_code not in [200, '200']:
                logger.info('list response status code:' + str(list_response1.status_code))
                result['code'] = 5
                return result
            result['token'] = list_json1['url'].split('/')[-1].split('.')[0]
        list_root = etree.HTML(list_response.text)
        a_list = list_root.xpath('//td[@width="215"]/a[@target="_blank"]')
        ids = []
        for a in a_list:
            href = a.attrib.get('href', '')
            resume_id = a.attrib.get('title', '')
            if not href or not resume_id:
                continue

            ids.append(['http://www.jianlika.com' + href, resume_id])

        # ids = list(set(ids))
        # if [] in ids:
        #     ids.remove('')
        result['data'] = ids
        if list_root.xpath('//a[@aria-label="Next"]'):
            result['has_next_page'] = True
            # f=open('123', 'w')
            # f.write(list_response.text.encode('utf8'))
            # f.close()
        else:
            result['has_next_page'] = False
        return result
    except Exception, e:
        logger.info(str(traceback.format_exc()))
    result['code'] = 3
    return result


def get_resume(get_resume_url, cookie, proxy=None):
    """
    获取简历详情页面
    :param get_resume_url:
    :param cookie:
    :param proxy:
    :return:
    """
    # time.sleep(1)
    logger = utils.get_logger()
    logger.info('获取简历详情页面 %s' % get_resume_url)
    logger.info('使用代理 ' + str(proxy) + ' 获取简历详情')
    result = {'code': 0}
    resume_id_re = re.compile('token/(.*?).html')
    resume_id_list = resume_id_re.findall(get_resume_url)
    if resume_id_list and len(resume_id_list) > 0:
        result['resumeId'] = resume_id_list[0]
    try:
        # get resume info
        # time.sleep(random.choice([2, 3, 4]))
        # get_resume_url = 'http://www.rencaiaaa.com/rdetail/recommendDetail.do?ext=1&resumeType=1&rid=%s&pid=0&srcid=%s&thirdId=%s&type=3' % (tmp_rid, srcid, thirdid)
        get_resume_header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cookie': cookie,
            'Host': 'www.jianlika.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30,
                                           proxies=proxy)
        if get_resume_response.status_code in [302, '302'] and get_resume_response.headers.get('Location') == '/':
            logger.info('简历详情返回 302 %s ' % get_resume_url)
            result['code'] = 4
            return result
        if get_resume_response.status_code not in [200, '200']:
            logger.info('获取简历详情返回非 200 code ' + str(get_resume_response.status_code))
            result['code'] = 2
            return result

        result['data'] = get_resume_response.text
        return result

    except Exception, e:
        logger.info('获取简历详情异常 ' + str(traceback.format_exc()))
        result['code'] = 1
        return result


def awake_one_task(task):
    """
        搜索简历程序入口
        :param task:
        :return:
        """
    logger = utils.get_logger()
    logger.info('开始执行任务')
    relogin_time = 3
    redis_client = get_redis_client()
    result = {'code': 0, 'executeParam': task}
    proxy = None
    if common_settings.USE_PROXY:
        proxy = settings.get_proxy()

    # account, cookie = get_one_account()

    # logger.info(str(cookie))
    logger.info('接受的任务数据 :' + json.dumps(task, ensure_ascii=False))

    page_now = 1
    download_day = str(time.localtime().tm_mon) + '-' + str(time.localtime().tm_mday)
    account, cookie = get_one_account()
    search_token = ''
    while page_now != -1:
        logger.info('当前页码:' + str(page_now))
        if task.get('use_keyword', '') == '1':
            list_result = get_list_with_keyword(cookie, page_now, search_token, task, proxy)
        else:
            list_result = get_list(cookie, page_now, search_token, task, proxy)
        # #time.sleep(2)
        if list_result['code'] == 4:
            # set_unavaliable_account(account)
            result['code'] = 1
            return result
        # elif list_result['code'] == 6:
        #     set_forbidden_account(account)
        #     continue
        if list_result['code']:
            logger.info('列表页面获取失败 :' + str(list_result))
            page_now = -1
            continue
        search_token = list_result.get('token') if page_now == 1 else search_token
        logger.info('当前页面1 ' + str(page_now))
        for resume_one in list_result['data']:
            time.sleep(3)
            resume_url, resume = resume_one
            # logger.info('sleep 5')
            # time.sleep(5)
            # if not account:
            """
            redis 去重
            """
            has_find_in_redis = False
            resume_key = 'jianlika_resume_' + str(resume)
            try:
                resume_redis_value = redis_client.get(resume_key)
                if resume_redis_value == download_day:
                    has_find_in_redis = True
                # else:
                #     pass
                # if resume_redis_value_list and resume_redis_value_list[0] == download_day:
                #     has_find_in_redis=True
                # else:
                #     real_rid = resume_redis_value_list[1]
                #     read_thirdid = resume_redis_value_list[2]
                # redis_client.set(resume_key, download_day)
            except Exception, e:
                logger.info(str(traceback.format_exc()))
                # redis_client.set(resume_key, download_day)
            if has_find_in_redis:
                logger.info('redis 存在了 %s' % resume_key)
                continue
            else:
                logger.info('redis 不存在，可以搜索 %s ' % resume_key)
            save_resumeid(resumeid=resume, task=task)
            # for x in xrange(3):
            #     # account, cookie = get_one_account()
            #     # 获取简历详情
            #     resume_result = get_resume(resume_url, cookie, proxy=proxy)
            #     # update_refresh_score(account)
            #     if resume_result['code'] == 4:
            #         # cookie失效
            #         set_unavaliable_account(account)
            #         account = None
            #         # redis_client.delete(resume_key)
            #         result['code'] = 2
            #         return result
            #         # continue
            #     # if resume_result['code'] == 7:
            #     #     set_forbidden_account(account)
            #     #     account = None
            #     #     # redis_client.delete(resume_key)
            #     #     continue
            #     if resume_result['code']:
            #         logger.info('简历详情获取异常 ' + str(resume_result))
            #         # redis_client.delete(resume_key)
            #         continue
            #     redis_client.set(resume_key, download_day)
            #     break
            # else:
            #     continue
            #
            # save_data(resume_result=resume_result, task=task, resume=resume, account=account)
            # return

        page_now = page_now + 1 if list_result['has_next_page'] else -1

    logger.info('任务处理完成:' + str(task))
    time.sleep(3)
    result['code'] = 0
    return result


def save_resumeid(resumeid, task):
    extendContent = {'emailJobType': task['keywords'],
                     'emailCity': task['areas_name']}
    sql = '''
        insert into spider.download_record(resumeId,dogFood,createTime,updateTime,valid,source,extendContent)values(
        '%s',1,now(),now(),0,11,'%s'
        )
    ''' % (resumeid, json.dumps(extendContent, ensure_ascii=False))
    result = utils.update_by_sql(sql)
    logger.info('简历id入库成功 %s %s' % (resumeid, result))


def save_data(resume_result, task, resume, account):
    resume_uuid = uuid.uuid1()
    try:
        content = json.dumps({'name': '', 'email': '', 'phone': '', 'html': resume_result['data'],
                              'resumeId': resume_result['resumeId']},
                             ensure_ascii=False)
        sql = 'insert into spider_search.resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) ' \
              'values (%s, %s, "python", %s, now(), %s, %s, %s, %s)'
        sql_value = (settings.project_settings.get('SOURCE'), content, resume_uuid, str(account['username']),
                     task['keywords'],
                     task['areas_name'], str(resume))

        resume_update_time = ''
        # resume_update_time =  resume_result['json']['updateDate']
        kafka_data = {
            "channelType": "WEB",
            "content": {
                "content": content,
                "id": '',
                "createBy": "python",
                "createTime": int(time.time() * 1000),
                "ip": '',
                "resumeSubmitTime": '',
                "resumeUpdateTime": resume_update_time,
                "source": settings.project_settings.get('SOURCE'),
                "trackId": str(resume_uuid),
                "avatarUrl": '',
                "email": str(account['username']),
                'emailJobType': task['keywords'],
                'emailCity': task['areas_name'],
                'subject': str(resume)
            },
            "interfaceType": "PARSE",
            "resourceDataType": "RAW",
            "resourceType": "RESUME_SEARCH",
            "source": settings.project_settings.get('SOURCE'),
            "trackId": str(resume_uuid),
            'traceID': str(resume_uuid),
            'callSystemID': settings.project_settings.get('CALLSYSTEMID'),
        }
        utils.save_data(sql, sql_value, kafka_data)
    except Exception, e:
        logger.info('get error when write mns, exit!!!' + str(traceback.format_exc()))
        # return
    time.sleep(1)


def download_resume(resume_id, cookie, proxy=None):
    if not proxy:
        proxy = settings.get_proxy()
    download_url = 'http://www.jianlika.com/Resume/downResume/token/%s.html' % resume_id
    logger.info('开始下载简历：%s' % download_url)
    refer = ('http://www.jianlika.com/Resume/view/token/%s.html' % resume_id).replace(":", "%3A").replace("/", "%2F")
    request_header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
        'Cache-Control': 'max-age=0',
        'Cookie': cookie + ";referer=" + refer,
        'Host': 'www.jianlika.com',
        'Proxy-Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    }
    result = {}
    response_data = requests.get(url=download_url, headers=request_header, proxies=proxy, allow_redirects=True,
                                 timeout=30).content
    response_data_json = json.loads(response_data, encoding='utf-8')

    if response_data_json.get('status') == 0:
        if '搜索浏览时间过期，请重新搜索' in response_data_json.get('data'):
            logger.error('简历id已经失效 %s ' % resume_id)
        result['code'] = 0
    else:
        result['name'] = response_data_json.get('name')
        result['phone'] = response_data_json.get('phone')
        result['email'] = response_data_json.get('email')
        result['code'] = 1
    detail_resume = requests.get(url='http://www.jianlika.com/Resume/view/token/%s.html' % resume_id,
                                 headers=request_header, proxies=proxy, allow_redirects=True,
                                 timeout=30).content
    result['content'] = detail_resume
    return result


def charge_resume(resume_id, cookie, proxy=None):
    time.sleep(3)
    """
    下载简历
    :param resume_id: 简历id
    :param cookie: 账户cookie
    :param proxy: 代理
    :return:
    """
    logger = utils.get_logger()
    logger.info('使用代理 ' + str(proxy) + '下载简历')
    result = {'code': 0, 'charge_json': {}}

    try:
        search_url = 'http://www.jianlika.com/Search/id.html'
        search_header = {
            'Host': 'www.jianlika.com',
            'Origin': 'http://www.jianlika.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://www.jianlika.com/Search/id.html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cookie': cookie,
        }
        search_data = 'id%5B%5D=' + resume_id + '&id%5B%5D=&id%5B%5D=&id%5B%5D=&id%5B%5D='
        search_response = requests.post(search_url, headers=search_header, data=search_data, allow_redirects=False,
                                        proxies=proxy, timeout=30)
        logger.info(search_response.status_code)
        logger.info(search_response.headers['Location'])
        logger.info(search_response.text)
        if search_response.status_code not in [302, '302'] or not search_response.headers.get('Location',
                                                                                              '').startswith(
            '/Resume/view/token/'):
            logger.info('简历下载-根据简历id获取简历详情失败 :' + search_response.text)
            result['code'] = 1
            return result

        # get resume info
        # time.sleep(random.choice([2, 3, 4]))
        get_resume_url = 'http://www.jianlika.com' + search_response.headers.get('Location', '')
        get_resume_header = {
            'Host': 'www.jianlika.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'http://www.jianlika.com/Search/id.html',
            'Cookie': cookie,
        }
        get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30,
                                           proxies=proxy)
        # if get_resume_response.status_code in [302, '302'] and get_resume_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
        #     logger.info('get resume response status headers:'+str(get_resume_response.headers))
        #     result['code'] = 9
        #     return result
        if get_resume_response.status_code not in [200, '200']:
            logger.info('简历下载-重定向获取返回非200' + str(get_resume_response.status_code))
            result['code'] = 4
            return result
        if u'下载联系方式' in get_resume_response.text:
            charge_url = 'http://www.jianlika.com/Resume/downResume/token/' + \
                         search_response.headers.get('Location', '').split('/')[-1]
            charge_header = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Origin': 'http://www.jianlika.com',
                'Referer': get_resume_url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }

            charge_data = {}
            charge_response = requests.post(charge_url, headers=charge_header, data=charge_data, proxies=proxy,
                                            allow_redirects=False)
            if charge_response.status_code not in [200, '200']:
                logger.info('简历下载-获取联系方式返回非200 ' + str(charge_response.status_code))
                result['code'] = 5
                return result
            logger.info('简历下载-获取联系方式返回 %s 内容:%s' % (resume_id, charge_response.text))
            if not charge_response.text:
                result['code'] = 10
                return result
            charge_json = charge_response.json()
            # if charge_json.get('status', -1) in [0, '0'] and charge_json.get('data', '') == u'简历已被下载':
            #     logger.info('get a has download resume!!!')
            #     result['charge_json'] = {}
            if charge_json.get('status', -1) not in [1, '1']:
                logger.info('简历下载-简历正文status异常 :' + charge_response.text)
                result['code'] = 8
                return result
            result['charge_json'] = charge_json.get('data', {})

        result['data'] = get_resume_response.text
        return result

    except Exception, e:
        logger.info('简历下载异常 :' + str(traceback.format_exc()))
        result['code'] = 1
        return result


def get_coin_number(cookie, proxy):
    logger = utils.get_logger()
    logger.info('开始获取账户')

    for x in xrange(3):
        try:
            result = {'code': 0}
            get_coin_url = 'http://www.jianlika.com/Search.html'
            get_coin_header = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cookie': cookie,
                'Host': 'www.jianlika.com',
                'Referer': 'http://www.jianlika.com/Search.html',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            }
            get_coin_response = requests.get(get_coin_url, headers=get_coin_header, allow_redirects=False,
                                             proxies=proxy, timeout=20)
            if get_coin_response.status_code not in [200, '200']:
                logger.info('获取下载点失败')
                continue
            coin_number_list = get_coin_re.findall(get_coin_response.text)
            if not coin_number_list:
                logger.info('下载点获取失败-没有返回内容')
                result['code'] = 2
                return result
            # get_coin_json = get_coin_response.json()
            # if get_coin_json['errorCode'] in [100, '100']:
            #     logger.info('the account is not avaliable')
            #     result['code'] = 3
            #     return result
            # if get_coin_json['errCode'] not in [100, '100']:
            #     logger.info('get error when get coin number:'+str(get_coin_json))
            #     result['code'] = 2
            #     return result
            result['code'] = 0
            result['coin'] = int(coin_number_list[0])
            return result
        except Exception, e:
            logger.info(str(traceback.format_exc()))

    else:
        logger.info('账户信息请求异常')
        result['code'] = 1
    return result


def download_thread():
    """
    简历下载线程
    :return:
    """
    logger = utils.get_logger()
    logger.info('=' * 20 + '\n 开始下载')
    global numbers_left
    global sleep_tag

    redis_client = get_redis_client()

    mysql_pool = PersistentDB(
        MySQLdb,
        host=common_settings.MYSQL_HOST,
        user=common_settings.MYSQL_USER,
        passwd=common_settings.MYSQL_PASSWD,
        db=common_settings.MYSQL_DOWNLOAD_DB,
        port=common_settings.MYSQL_PORT,
        charset='utf8'
    )
    mysql_conn = mysql_pool.connection()
    mysql_cursor = mysql_conn.cursor()
    mysql_cursor.execute('update download_record set valid=0 where valid=1 and source=11')
    mysql_conn.commit()
    proxy = None
    if common_settings.USE_PROXY:
        proxy = settings.get_proxy()
    task_list = []
    mysql_cursor.execute('select count(*) from download_record where updateTime>date(now()) and valid=2 and source=11')
    number_today = mysql_cursor.fetchall()[0][0]
    numbers_left -= number_today
    numbers_left = 0 if numbers_left < 0 else numbers_left

    while True:
        while not sleep_tag:
            logger.info('非下载时间，睡眠1小时')
            time.sleep(3600)
        if not numbers_left:
            logger.info('超过当日限额，睡眠0.5小时')
            time.sleep(1800)
            continue
        logger.info('当天剩余下载限额为:' + str(numbers_left))
        while not task_list:
            while not sleep_tag:
                logger.info('非下载时间，睡眠1小时')
                time.sleep(3600)
            task_number = mysql_cursor.execute(
                'select * from download_record where valid=0 and source=11 order by updateTime desc limit 1')
            if not task_number:
                logger.info('没有需要下载的任务了,睡眠5分钟')
                time.sleep(300)
                continue
            task_list = list(mysql_cursor.fetchall())
            break
        task = task_list.pop()
        if task[8]:
            try:
                extend_content = json.loads(task[8])
                extend_content['emailJobType'] = '' if 'emailJobType' not in extend_content else extend_content[
                    'emailJobType']
                extend_content['emailCity'] = '' if 'emailCity' not in extend_content else extend_content['emailCity']
            except Exception, e:
                logger.info('not find extend_content in task:' + str(task))
                extend_content = {"emailJobType": "", "emailCity": ""}
        else:
            extend_content = {"emailJobType": "", "emailCity": ""}

        # download
        get_null_text_count = 0
        for charge_count in xrange(3):
            time.sleep(4)
            account, cookie = get_one_account(download=True)
            charge_result = charge_resume(task[1], cookie, proxy)
            # if charge_result['code'] == 9:
            #     set_forbidden_account(account)
            #     continue
            # if charge_result['code'] == 10:
            #     get_null_text_count += 1
            #     continue
            if charge_result['code']:
                # set_unavaliable_account(account)
                continue
            break
        else:
            logger.info('当前简历重试超过3次 %s ' % str(task[0]))
            if get_null_text_count == 3:
                try:
                    mysql_cursor.execute('update download_record set valid=3 where id=%s' % str(task[0]))
                    mysql_conn.commit()
                    logger.info('get 3 null text of resume:' + task[1])
                except Exception, e:
                    logger.info(str(traceback.format_exc()))
            continue
        # 简历正文入库
        resume_uuid = uuid.uuid1()
        try:
            content = {'html': charge_result['data'], 'email': charge_result['charge_json'].get('email'),
                       'mobile': charge_result['charge_json'].get('phone'),
                       'name': charge_result['charge_json'].get('name')}
            content = json.dumps(content, ensure_ascii=False)
            mysql_cursor.execute(
                u'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values ("RESUME_KA", %s, "python", %s, now(), %s, %s, %s, %s)',
                (content, resume_uuid, account['username'], extend_content['emailJobType'], extend_content['emailCity'],
                 task[1]))
            mysql_conn.commit()
            numbers_left -= 1
            mysql_cursor.execute('select last_insert_id()')
            save_mysql_ids = mysql_cursor.fetchall()
            if not save_mysql_ids or not save_mysql_ids[0]:
                logger.info('insert into mysql error!!!')
                raise Exception
            save_mysql_id = save_mysql_ids[0][0]
        except Exception, e:
            # print str(traceback.format_exc())
            logger.info(str(traceback.format_exc()))
            continue
        # 下载简历推送mns
        kafka_data = {
            "channelType": "WEB",
            "content": {
                "content": content,
                "id": save_mysql_id,
                "createBy": "python",
                "createTime": int(time.time() * 1000),
                "ip": '',
                "resumeSubmitTime": '',
                # "resumeUpdateTime": resume.get('refDate', ''),
                "resumeUpdateTime": '',
                "source": "RESUME_KA",
                "trackId": str(resume_uuid),
                "avatarUrl": '',
                'emailJobType': extend_content['emailJobType'],
                'emailCity': extend_content['emailCity'],
                'email': account['username'],
                'subject': task[1],
            },
            "interfaceType": "PARSE",
            "resourceDataType": "RAW",
            "resourceType": "RESUME_INBOX",
            "source": "RESUME_KA",
            "trackId": str(resume_uuid),
        }
        logger.info('rawid为:' + str(kafka_data['content']['id']))
        try:
            buf = StringIO()
            f = gzip.GzipFile(mode='wb', fileobj=buf)
            f.write(json.dumps(kafka_data))
            f.close()
            msg_body = base64.b64encode(buf.getvalue())
            msg = Message(msg_body)
            push_mns_error_tag = False
            for send_message_count in range(settings.project_settings.get('MNS_SAVE_RETRY_TIME')):
                try:
                    mns_client = get_mns_client()
                    mns_client.send_message(msg)
                    break
                except Exception, e:
                    logger.info('mns推送异常:' + str(send_message_count) + ':' + str(e))
                    if 'The length of message should not be larger than MaximumMessageSize.' == e.message:
                        logger.info('mns推送异常-简历正文太长超过最大限制:' + task[1])
                        try:
                            mysql_cursor.execute('update download_record set valid=3, downloadBy="%s" where id=%s' % (
                                str(account['username']), str(task[0])))
                            mysql_conn.commit()
                        except Exception, e:
                            logger.info(str(traceback.format_exc()))
                            time.sleep(600)
                        push_mns_error_tag = True
                        break
            else:
                raise Exception
            if push_mns_error_tag:
                continue
        except Exception, e:
            logger.info('推送mns异常 ' + str(traceback.format_exc()))
            send_dingding_text('推送mns异常,rawid为 %s ' % str(kafka_data['content']['id']))
            return 3
        try:
            mysql_cursor.execute('update download_record set valid=2, downloadBy="%s" where id=%s' % (
                str(account['username']), str(task[0])))
            mysql_conn.commit()
            # del task_list[index]
        except Exception, e:
            logger.info(str(traceback.format_exc()))
            time.sleep(600)
            continue
        # time.sleep(2)

        coin_number_result = get_coin_number(cookie, proxy)
        if not coin_number_result['code']:
            update_coin_number_left(account, coin_number_result['coin'])
            if coin_number_result['coin'] < 10:
                logger.info('下载点少于10个了 :' + str(account))
        else:
            logger.info('未知错误:' + str(coin_number_result))

    logger.info('quit')
    mysql_cursor.close()
    mysql_conn.close()


if __name__ == '__main__':
    utils.set_setting(settings.project_settings)
    logger = utils.get_logger()
    logger.info('=' * 50 + 'start main')

    global numbers_left, get_task_queue
    numbers_left = settings.project_settings.get('NUMBERS_ERVERYDAY')
    get_task_queue = Queue.Queue(maxsize=settings.project_settings.get('QUEUE_MAX_SIZE'))

    change_time_thread_one = threading.Thread(target=change_time_thread, name="Change_Time_Thread")
    change_time_thread_one.start()

    dowload_number = settings.project_settings.get('SEARCH_THREAD_NUMBER')

    search_thread_list = []
    for x in xrange(dowload_number):
        search_thread = threading.Thread(target=awake_thread, name='Thread-' + str(x))
        search_thread.start()
        search_thread_list.append(search_thread)

    download_thread_one = threading.Thread(target=download_thread, name='Download_Thread')
    download_thread_one.start()
    #
    download_thread_one.join()

    for i in search_thread_list:
        i.join()
    change_time_thread_one.join()

    logger.info('处理完毕')
