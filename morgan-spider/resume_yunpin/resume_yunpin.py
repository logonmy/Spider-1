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

stop_tag = False
sleep_tag = True
get_task_queue = None
push_task_time = None
push_task_keyword_tag = '0'
push_task_lock = threading.Lock()

def login(username, passwd, safe_code, proxy=None):
    logger = utils.get_logger()
    result = {'code': 0, 'cookie': ''}
    try:
        login_session = requests.Session()
        login_url1 = 'http://www.job1001.com/companyServe/vLoginAjax.php?ajaxformflag=1'
        login_headers1 = {
            'Accept':'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'Host':'www.job1001.com',
            'Origin':'http://www.job1001.com',
            'Referer':'http://www.job1001.com/companyServe/login.php?out=true&jumpurl=',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'X-Requested-With':'XMLHttpRequest',
        }
        login_data1 = {
            'uname': username,
            'password': passwd,
            'hh':'0',
            'jump_url':'',
            'safe_code': safe_code,
            'fromtype':'',
            'autoLogin':'0',
            'checkcode':'',
            'login_num':'1',
        }
        login_response1 = login_session.post(login_url1, headers=login_headers1, data=login_data1, allow_redirects=False, timeout=30, proxies=proxy)
        # logger.info(login_response1.text)
        if login_response1.status_code not in [200, '200']:
            logger.info('not get 200 when login:'+str(login_response1.status_code))
            result['code'] = 2
            return result
        login_json1 = login_response1.json()
        if login_json1.get('status', '')!='OK' and login_json1.code not in ['100', 100]:
            logger.info('error login response1:'+login_response1.text)

        login_url2 = u'http://yp.yl1001.com/yp_sso.php?callback=jQuery183032099134727358924_%s&status=OK&status_code=100&code=100&status_desc=&jump_url%s&info[company_id]=%s&info[uname]=%s&info[pwd]=%s&info[synergy_id]=%s&_=%s' % (int(time.time()*1000), login_json1.get('status_desc'), login_json1.get('info', {}).get('company_id'), login_json1.get('info', {}).get('username'), login_json1.get('info', {}).get('pwd'), login_json1.get('info', {}).get('synergy_id'), int(time.time()*1000))
        login_headers2 = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Host':'yp.yl1001.com',
            'Referer':'http://www.job1001.com/companyServe/login.php?out=true&jumpurl=',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }

        login_response2 = login_session.get(login_url2, headers=login_headers2, allow_redirects=False, timeout=30, proxies=proxy)
        if login_response2.status_code not in [200, '200']:
            logger.info('not get 200 when get login response 2:'+str(login_response2.status_code))
            result['code'] = 3
            return result
        login_url3 = 'http://www.job1001.com/admincompanyNew/yp/admin/'
        login_headers3 = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Host':'www.job1001.com',
            'Referer':'http://www.job1001.com/companyServe/login.php?out=true&jumpurl=',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        login_response3 = login_session.get(login_url3, headers=login_headers3, timeout=30, proxies=proxy, allow_redirects=False)
        if login_response3.status_code not in [302, '302'] or not login_response3.headers.get('Location'):
            logger.info('not get 302 when request login url3:'+str(login_response3.status_code))
            result['code'] = 4
            return result
        login_url4 = 'http:' + login_response3.headers.get('Location')
        login_headers4 = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Host':'yp.yl1001.com',
            'Referer':'http://www.job1001.com/companyServe/login.php?out=true&jumpurl=',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        login_response4 = login_session.get(login_url4, headers=login_headers4, allow_redirects=False, proxies=proxy, timeout=30)
        if login_response4.status_code not in [302, '302']:
            logger.info('not get 302 when requests login url4:'+str(login_response4.status_code))
            result['code'] = 5
            return result
        cookie_dict = {}
        for i in login_session.cookies:
            if i.domain == 'yp.yl1001.com':
                cookie_dict[i.name] = i.value
        # logger.info(login_response2.text)
        # cookie_dict = dict(login_session.cookies)
        # logger.info(login_session.cookies)
        result['cooie'] = '; '.join([i+'='+cookie_dict[i] for i in cookie_dict])
        return result
    except Exception, e:
        logger.info(str(traceback.format_exc()))
        result['code'] = 1
        return result

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
            traceback.print_exc(e)
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
            traceback.print_exc(e)
            return None

    def send_action_card(self, title, content, hide_avatar="0", btn_oriengtation="0", single_title="阅读全文", single_url="#"):
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
            traceback.print_exc(e)
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
            traceback.print_exc(e)
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
    if not push_task_time or (datetime.datetime.now()-push_task_time).seconds>14400:
        send_dingding_text(u'开始推送云聘简历任务.')
        create_task.create_task_from_mysql(push_task_keyword_tag)
        push_task_keyword_tag = '0' if push_task_keyword_tag == '1' else '1'
        push_task_time = datetime.datetime.now()
    push_task_lock.release()

def get_one_account(download=False):
    # return {'username': 'test130279237', 'passwd': 'jinqian4611', 'id': 805}, 'PHPSESSID=fafcca9b377c5e11aa2f8abe459b646b; my_url=www.job1001.com; cookieflag=1510715494594102845; cookieflagall=1510715494594741101; cookiesession=15107154945950.13136548345425192'
    logger = utils.get_logger()
    logger.info('start to get a search account.')
    if download:
        url = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'RESUME_INBOX')
    else:
        url = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'RESUME_FETCH')
    while True:
        try:
            response = requests.get(url, timeout=10)
            response_json = response.json()
            if response_json['code'] in [200, '200'] and response_json['data']:
                account = {'username': response_json['data']['userName'], 'passwd': response_json['data']['password'], 'id': response_json['data']['id'], 'downloadScore': response_json['data']['downloadScore'], 'freshScore': response_json['data']['freshScore']}
                cookie = response_json['data']['cookie']
                # cookie = json.loads(response_json['data']['cookie'])
                if not cookie:
                    logger.info('not get cookie in result, set to relogin and try again.')
                    set_unavaliable_account(account)
                    continue
                logger.info('using account:'+response.text)
                return account, cookie
        except Exception, e:
            logger.info('get error when get search account:'+str(traceback.format_exc()))
        time.sleep(3600)

def set_unavaliable_account(account):
    logger = utils.get_logger()
    logger.info('set unavaliable :'+str(account))
    time.sleep(2)
    url = common_settings.SET_INVALID_URL % (account['username'], account['passwd'], common_settings.SOURCE)
    try:
        response = requests.get(url)
        logger.info('set unavaliable account response:'+ response.text)
    except Exception, e:
        logger.info(str(traceback.format_exc()))

def set_forbidden_account(account):
    logger = utils.get_logger()
    logger.info('set forbidden :'+str(account))
    time.sleep(2)
    url = common_settings.SET_FORBIDDEN_URL % (account['username'], account['passwd'])
    try:
        # pass
        response = requests.get(url)
        send_dingding_text(u'云聘账号异常:%s' % account['username'])
        logger.info('set forbidden account response:'+ response.text)
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

# def update_coin_number_left(account, coin_number):
#     logger = utils.get_logger()
#     logger.info('update coin number:'+str(account)+' '+str(coin_number))
#     url = common_settings.UPDATE_DOWNLOAD_SCORE
#     data = {
#         # 'id': account['id'],
#         'downloadRecord': coin_number,
#         'userName': account['username'],
#         'password': account['passwd'],
#         'source': common_settings.SOURCE,
#     }
#     try:
#         response = requests.post(url, data=data)
#     except Exception, e:
#         logger.info(str(traceback.format_exc()))

# def update_refresh_score(account):
#     logger = utils.get_logger()
#     logger.info('update coin number:'+str(account))
#     url = common_settings.UPDATE_DOWNLOAD_SCORE
#     data = {
#         # 'id': account['id'],
#         'freshScore': account['freshScore']-1,
#         'userName': account['username'],
#         'password': account['passwd'],
#         'source': common_settings.SOURCE,
#     }
#     try:
#         response = requests.post(url, data=data)
#     except Exception, e:
#         logger.info(str(traceback.format_exc()))

def awake_thread():
    logger = utils.get_logger()
    logger.info('process_thread start!!!')
    global stop_tag
    global sleep_tag
    while not stop_tag:
        while not sleep_tag:
            logger.info('not the correct time to search resume, wait.')
            time.sleep(3600)
        task_traceid = str(uuid.uuid1())
        params = {'traceID': task_traceid, 'callSystemID': common_settings.CALLSYSTEMID,
                  'taskType': common_settings.TASK_TYPE, 'source': common_settings.SOURCE, 'limit': 1}
        param_str = '&'.join([str(i) + '=' + str(params[i]) for i in params])
        task_url = common_settings.TASK_URL + common_settings.GET_TASK_PATH + param_str
        logger.info(task_url)
        task_result = utils.download(url=task_url, is_json=True)
        if task_result['code'] or task_result['json']['code'] not in [200, '200']:
            logger.info('get error task, sleep... url is:' + task_url + ' return is:' + str(task_result))
            time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        logger.info('='*30 +'get task!!!' + str(task_result))
        if not task_result['json']['data']:
            logger.info('did not get task_result data:' + str(task_result))
            push_task()
            time.sleep(120)
            continue
        process_result = {'code': -1, 'executeParam':task_result['json']['data'][0]['executeParam']}
        try:
            process_result = awake_one_task(json.loads(task_result['json']['data'][0]['executeParam']))
        except Exception, e:
            logger.info('error when process:' + str(traceback.format_exc()))
        return_task_url = common_settings.TASK_URL + common_settings.RETURN_TASK_PATH
        return_task_traceid = str(uuid.uuid1())
        return_data = {}
        return_data['traceID'] = return_task_traceid
        return_data['callSystemID'] = common_settings.CALLSYSTEMID
        return_data['uuid'] = task_result['json']['data'][0]['uuid']
        #return_data['executeResult'] = process_result.get('executeResult', '')
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
                        'callSystemID': common_settings.CALLSYSTEMID,
                        'taskType': common_settings.TASK_TYPE, 
                        'source': common_settings.SOURCE,
                        'executeParam': task_result['json']['data'][0]['executeParam'],
                        'parentUuid': task_result['json']['data'][0]['uuid'], 
                        # 'deadline': task_result['json']['data'][0]['deadline'],
                    }
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    }
                    insert_result = utils.download(url=insert_url, is_json=True, headers=headers, method='post', data=insert_data)
                    logger.info('insert result:'+str(insert_result))
                    if not insert_result['code'] and insert_result['json']['code'] in [200, '200']:
                        break
                except Exception, e:
                    logger.info('error when create task:' + str(traceback.format_exc()))

        # time.sleep(5)

def get_mns_client():
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY, common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client

def change_time_thread():
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
            numbers_left = common_settings.NUMBERS_ERVERYDAY
            logger.info('has change day, start_day is '+str(start_day))
        # if hour_now > 4 and hour_now < 23:
        #     sleep_tag = True
        # else:
        #     sleep_tag = False
        time.sleep(3600)

def get_list(cookie, page_numner, params, proxy=None):
    logger = utils.get_logger()
    result = {'code': 0, 'data': [], 'has_next_page': False}
    logger.info('use proxy '+str(proxy) + ' to download list')

    try:
        list_url = u'http://yp.yl1001.com/admin/index.php?m=search&a=search_result&p=&pp=&engineKey=请输入简历关键词，多个词可以用空格隔开&searchway=index&company=请输入公司名称&jtzw=请输入职位名称&joblist=%s&regionid=%s&target_area=&gznum1=不限&gznum2=不限&education1=&education2=&age1=岁&age2=不限&searcherName=&naxian_search_flag=&page=%s' % (params['joblist'], params['regionid'], str(page_numner-1))
        list_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie':cookie,
            'Host':'yp.yl1001.com',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        if page_numner == 1:
            list_header['Referer'] = u'http://yp.yl1001.com/admin/index.php?m=search&a=search_result&p=&pp=&engineKey=请输入简历关键词，多个词可以用空格隔开&searchway=index&company=请输入公司名称&jtzw=请输入职位名称&joblist=%s&regionid=%s&target_area=&gznum1=不限&gznum2=不限&education1=&education2=&age1=岁&age2=不限&searcherName=&naxian_search_flag=&page=%s' % (params['joblist'], params['regionid'], '1')
        else:
            list_header['Referer'] = u'http://yp.yl1001.com/admin/index.php?m=search&a=search_result&p=&pp=&engineKey=请输入简历关键词，多个词可以用空格隔开&searchway=index&company=请输入公司名称&jtzw=请输入职位名称&joblist=%s&regionid=%s&target_area=&gznum1=不限&gznum2=不限&education1=&education2=&age1=岁&age2=不限&searcherName=&naxian_search_flag=&page=%s' % (params['joblist'], params['regionid'], str(page_numner-2))

        list_response = requests.get(list_url, headers=list_header, proxies=proxy, allow_redirects=False, timeout=30)
        if list_response.status_code in [302, '302'] and list_response.headers.get('Location') == 'http://www.job1001.com/companyServe/login.php?out=true':
            logger.info('get 302 when get list, header:'+str(list_response.headers))
            result['code'] = 4
            return result
        if list_response.status_code not in [200, '200']:
            logger.info('list response status code:'+str(list_response.status_code))
            result['code'] = 1
            return result
        list_root = etree.HTML(list_response.text)
        table = list_root.xpath('//table[@class="f_resume_tab  "]')
        ids = []
        if table:
            tr_list = table[0].xpath('./tbody//tr')
            for tr in tr_list:
                td_list = tr.xpath('./td')
                if len(td_list) != 10:
                    continue
                a_list = td_list[1].xpath('./a')
                resume_update_time = td_list[9].text
                if not a_list or len(resume_update_time.split('-'))!=3:
                    continue
                a_href = a_list[0].attrib.get('href')
                a_id = a_list[0].attrib.get('data-id')
                if not a_href or not a_id:
                    continue
                ids.append([str(a_id), a_href, resume_update_time])

        result['data'] = ids
        all_resume_number_list = list_root.xpath('//span[@class="active"]')
        if all_resume_number_list and all_resume_number_list[0].text:
            try:
                resume_all_number_str = all_resume_number_list[0].text
                if '+' in resume_all_number_str:
                    resume_all_number_str = resume_all_number_str[:-1]
                resume_all_number_int = int(resume_all_number_str)
                if page_numner*20 < resume_all_number_int:
                    result['has_next_page'] = True
            except Exception, e:
                logger.info('get error resume number from page:'+all_resume_number_list[0].text)
        return result
    except Exception, e:
        logger.info(str(traceback.format_exc()))
    result['code'] = 3
    return result

def get_list_with_keyword(cookie, page_numner, params, proxy=None):
    logger = utils.get_logger()
    result = {'code': 0, 'data': [], 'has_next_page': False}
    logger.info('use proxy '+str(proxy) + ' to download list with keyword')

    try:
        list_url = u'http://yp.yl1001.com/admin/index.php?m=search&a=search_result&p=&pp=&engineKey=%s&searchway=index&company=请输入公司名称&jtzw=请输入职位名称&joblist=&regionid=&target_area=%s&gznum1=不限&gznum2=不限&education1=&education2=&age1=岁&age2=不限&searcherName=&naxian_search_flag=&page=%s' % (params['joblist'], params['regionid'], str(page_numner-1))
        list_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie':cookie,
            'Host':'yp.yl1001.com',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        if page_numner == 1:
            list_header['Referer'] = u'http://yp.yl1001.com/admin/index.php?m=search&a=search_result&p=&pp=&engineKey=%s&searchway=index&company=请输入公司名称&jtzw=请输入职位名称&joblist=&regionid=&target_area=%s&gznum1=不限&gznum2=不限&education1=&education2=&age1=岁&age2=不限&searcherName=&naxian_search_flag=&page=%s' % (params['joblist'], params['regionid'], '1')
        else:
            list_header['Referer'] = u'http://yp.yl1001.com/admin/index.php?m=search&a=search_result&p=&pp=&engineKey=%s&searchway=index&company=请输入公司名称&jtzw=请输入职位名称&joblist=&regionid=&target_area=%s&gznum1=不限&gznum2=不限&education1=&education2=&age1=岁&age2=不限&searcherName=&naxian_search_flag=&page=%s' % (params['joblist'], params['regionid'], str(page_numner-2))

        list_response = requests.get(list_url, headers=list_header, proxies=proxy, allow_redirects=False, timeout=30)
        if list_response.status_code in [302, '302'] and list_response.headers.get('Location') == 'http://www.job1001.com/companyServe/login.php?out=true':
            logger.info('get 302 when get list, header:'+str(list_response.headers))
            result['code'] = 4
            return result
        if list_response.status_code not in [200, '200']:
            logger.info('list response status code:'+str(list_response.status_code))
            result['code'] = 1
            return result
        list_root = etree.HTML(list_response.text)
        table = list_root.xpath('//table[@class="f_resume_tab  "]')
        ids = []
        if table:
            tr_list = table[0].xpath('./tbody//tr')
            for tr in tr_list:
                td_list = tr.xpath('./td')
                if len(td_list) != 10:
                    continue
                a_list = td_list[1].xpath('./a')
                resume_update_time = td_list[9].text
                if not a_list or len(resume_update_time.split('-'))!=3:
                    continue
                a_href = a_list[0].attrib.get('href')
                a_id = a_list[0].attrib.get('data-id')
                if not a_href or not a_id:
                    continue
                ids.append([str(a_id), a_href, resume_update_time])

        result['data'] = ids
        all_resume_number_list = list_root.xpath('//span[@class="active"]')
        if all_resume_number_list and all_resume_number_list[0].text:
            try:
                resume_all_number_str = all_resume_number_list[0].text
                if '+' in resume_all_number_str:
                    resume_all_number_str = resume_all_number_str[:-1]
                resume_all_number_int = int(resume_all_number_str)
                if page_numner*20 < resume_all_number_int:
                    result['has_next_page'] = True
            except Exception, e:
                logger.info('get error resume number from page:'+all_resume_number_list[0].text)
        return result
    except Exception, e:
        logger.info(str(traceback.format_exc()))
    result['code'] = 3
    return result

def get_resume(get_resume_url, cookie=None, proxy=None):
    # time.sleep(1)
    logger = utils.get_logger()
    logger.info('use proxy '+str(proxy)+'to download resume')
    result = {'code': 0}

    try:
        get_resume_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Host':'www.job1001.com',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        logger.info('start to get resume')
        get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30, proxies=proxy)
        if get_resume_response.status_code not in [200, '200']:
            logger.info('not get 200 when get resume response:'+str(get_resume_response.status_code))
            result['code'] = 3
            return result

        result['data'] = get_resume_response.content.decode('gbk')
        return result

    except Exception, e:
        logger.info('get error when download resume:'+str(traceback.format_exc()))
        result['code'] = 1
        return result

def awake_one_task(task):
    logger = utils.get_logger()
    logger.info('start aweak one task')
    relogin_time = 3
    redis_client = get_redis_client()
    result = {'code': 0, 'executeParam':task}
    proxy = None
    if common_settings.USE_PROXY:
        proxy = settings.get_proxy()

    # account, cookie = get_one_account()

    # logger.info(str(cookie))
    logger.info('deal with:'+str(task))

    page_now = 1
    download_day = str(time.localtime().tm_mon)+'-'+str(time.localtime().tm_mday)
    datetime_now = datetime.datetime.now()
    while page_now != -1:
        logger.info('start download page:'+str(page_now))
        # if not account:
        account, cookie = get_one_account()
        if task.get('use_keyword', '') == '1':
            list_result = get_list_with_keyword(cookie, page_now, task, proxy)
        else:
            list_result = get_list(cookie, page_now, task, proxy)
        #time.sleep(2)
        if list_result['code'] == 4:
            set_unavaliable_account(account)
            continue
        # if list_result['code'] == 4:
        #     set_forbidden_account(account)
        #     continue
        elif list_result['code']:
            logger.info('get error list result:'+str(list_result))
            page_now = -1
            continue
        logger.info('page number of now is '+str(page_now))
        for resume_one in list_result['data']:
            resume, resume_url, resume_update_time = resume_one
            has_find_in_redis = False
            resume_key = 'yunpin_resume_'+str(resume)
            try:
                # check resume_update_time
                datetime_update = datetime.datetime.strptime(resume_update_time, '%Y-%m-%d')
                if (datetime_now - datetime_update).days:
                    logger.info('get 1 days before resume, continue.'+resume_update_time)
                    logger.info('get 1 days before resume, continue.')
                    list_result['has_next_page'] = False
                    continue
                # find in redis
                resume_redis_value=redis_client.get(resume_key)
                if resume_redis_value:
                    if resume_redis_value == download_day:
                        has_find_in_redis = True
            except Exception, e:
                logger.info(str(traceback.format_exc()))
            if has_find_in_redis:
                logger.info('has find %s in redis' % resume_key)
                continue
            else:
                logger.info('not find %s in redis' % resume_key)

            for x in xrange(3):
                # account, cookie = get_one_account()
                resume_result = get_resume(resume_url, proxy=proxy)
                # update_refresh_score(account)
                if resume_result['code']:
                    logger.info('get error resume:'+str(resume_result))
                    # redis_client.delete(resume_key)
                    continue
                redis_client.set(resume_key, download_day)
                break
            else:
                continue

            resume_uuid = uuid.uuid1()
            try:
                content = json.dumps({'resume_update_time': resume_update_time, 'html':resume_result['data']}, ensure_ascii=False)
                sql = 'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values (%s, %s, "python", %s, now(), %s, %s, %s, %s)'
                sql_value = (common_settings.SOURCE, content, resume_uuid, str(account['username']), task['joblist'], task['region_name'], str(resume))

                kafka_data = {
                    "channelType": "WEB",
                    "content": {
                        "content": content,
                        "id": '',
                        "createBy": "python",
                        "createTime": int(time.time()*1000),
                        "ip": '',
                        "resumeSubmitTime": '',
                        "resumeUpdateTime": resume_update_time,
                        "source": common_settings.SOURCE,
                        "trackId": str(resume_uuid),
                        "avatarUrl": '',
                        "email": str(account['username']),
                        'emailJobType': task['joblist'],
                        'emailCity': task['region_name'],
                        'subject': str(resume)
                    },
                    "interfaceType": "PARSE",
                    "resourceDataType": "RAW",
                    "resourceType": "RESUME_SEARCH",
                    "source": common_settings.SOURCE,
                    "trackId": str(resume_uuid),
                    'traceID': str(resume_uuid),
                    'callSystemID': common_settings.CALLSYSTEMID,
                }
                utils.save_data(sql, sql_value, kafka_data)
            except Exception, e:
                logger.info('get error when write mns, exit!!!'+str(traceback.format_exc()))
                # return
            time.sleep(1)
            #return

        page_now = page_now+1 if list_result['has_next_page'] else -1

    logger.info('has finish deal with:'+str(task))
    time.sleep(3)
    result['code'] = 0
    return result

# def charge_resume(rid, thirdid, srcid, cookie, proxy=None):
#     # time.sleep(1)
#     logger = utils.get_logger()
#     logger.info('use proxy '+str(proxy)+'to download resume')
#     result = {'code': 0}
    
#     try:
#         # add resume into unhandle
#         # add_url = 'http://www.rencaiaaa.com/resume/addCandidate.do'
#         # add_header = {
#         #     'Accept':'*/*',
#         #     'Accept-Encoding':'gzip, deflate',
#         #     'Accept-Language':'zh-CN,zh;q=0.8',
#         #     'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
#         #     'Cookie':cookie,
#         #     'Host':'www.rencaiaaa.com',
#         #     'Origin':'http://www.rencaiaaa.com',
#         #     'Referer':'http://www.rencaiaaa.com/main.do',
#         #     'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
#         #     'X-Requested-With':'XMLHttpRequest',
#         # }
#         # add_data = {
#         #     'rid': rid,
#         #     'srcid':'1',
#         #     'thirdId': thirdid,
#         #     'resumeType':'1',
#         #     'canContact':'0',
#         #     'rpid':'0',
#         #     'rStage':'1',
#         #     'recommandType':'3',
#         #     'ifMoveRecommendCv':'0',
#         # }
#         # add_response = requests.post(add_url, headers=add_header, data=add_data, proxies=proxy, allow_redirects=False, timeout=30)
#         # if add_response.status_code not in [200, '200']:
#         #     logger.info('not get 200 when add url:'+str(add_response.status_code))
#         #     result['code'] = 2
#         #     return result
#         # add_json = add_response.json()
#         # tmp_rid = add_json.get('result', {}).get('rid', '')
#         # if add_json.get('errCode', 0) not in [100, '100'] or add_json.get('ok', 0) not in [True, 'true'] or not tmp_rid:
#         #     logger.info('add resume to Candidate failed:'+add_response.text)
#         #     result['code'] = 3
#         #     return result

#         # get resume info
#         time.sleep(random.choice([2, 3, 4]))
#         get_resume_url = 'http://www.rencaiaaa.com/rdetail/recommendDetail.do?ext=1&resumeType=1&rid=%s&pid=0&srcid=%s&thirdId=%s&type=3' % (rid, srcid, thirdid)
#         get_resume_header = {
#             'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Encoding':'gzip, deflate',
#             'Accept-Language':'zh-CN,zh;q=0.8',
#             'Cookie':cookie,
#             'Host':'www.rencaiaaa.com',
#             'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
#         }
#         get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30, proxies=proxy)
#         if get_resume_response.status_code in [302, '302'] and get_resume_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
#             logger.info('get resume response status headers:'+str(get_resume_response.headers))
#             result['code'] = 9
#             return result
#         elif get_resume_response.status_code not in [200, '200']:
#             logger.info('not get 200 when get resume response:'+str(get_resume_response.status_code))
#             result['code'] = 4
#             return result

#         charge_url = 'http://www.rencaiaaa.com/rdetail/rencaiContact.do?fromPoints=0'
#         charge_header = {
#             'Accept':'*/*',
#             'Accept-Encoding':'gzip, deflate',
#             'Accept-Language':'zh-CN,zh;q=0.8',
#             'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
#             'Cookie':cookie,
#             'Host':'www.rencaiaaa.com',
#             'Origin':'http://www.rencaiaaa.com',
#             'Referer':get_resume_url,
#             'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
#             'X-Requested-With':'XMLHttpRequest',
#         }

#         input_keys = ['major', 'thirdId', 'talentInvitePid', 'talentInviteMailTitle', 'bindEmail_ssl', 'salaryMaxInvite', 'interviewStr', 'resumeType', 'candidate', 'inurl', 'ppid', 'type', 'salaryMinInvite', 'ageMin', 'purchaseByExternalAccount', 'contactNo','shortId', 'pname', 'groupId', 'reviewName', 'school', 'sexId', 'keyword', 'recommandType', 'ageMax', 'rids', 'pid', 'puid', 'contactEmail', 'talentInviteTemplateId', 'candidateName', 'rid', 'candidateEmail', 'reviewEmail', 'interviewerMail', 'sms', 'thirdIdForDownload', 'positionInfo', 'state', 'interviewAddress', 'linkedPerson', 'positionName', 'companyName', 'srcid', 'ifMoveRecommendCv', 'workPlace', 'address', 'resume_pname', 'url','ext']

#         resume_root = etree.HTML(get_resume_response.text)
#         charge_data = {}
#         for data_key in input_keys:
#             data_list = resume_root.xpath('//input[@name="%s"]' % data_key)
#             if data_list:
#                 charge_data[data_key] = data_list[0].attrib.get('value', '')
#             else:
#                 charge_data[data_key] = ''
#         charge_data['emailContent'] = resume_root.xpath('//textarea[@name="emailContent"]')[0].text
#         charge_data['talentInviteMailTxt'] = resume_root.xpath('//textarea[@name="talentInviteMailTxt"]')[0].text

#         charge_response = requests.post(charge_url, headers=charge_header, data=charge_data, proxies=proxy, allow_redirects=False)
#         if charge_response.status_code not in [200, '200']:
#             logger.info('charge failed!!!'+str(charge_response.status_code))
#             result['code'] = 7
#             return result
#         logger.info('charge reusme %s response:%s' %(rid, charge_response.text))
#         if not charge_response.text:
#             result['code'] = 10
#             return result
#         charge_json = charge_response.json()
#         if charge_json.get('errCode', -1) not in [100, '100'] :
#             logger.info('get error charge response:'+charge_response.text)
#             result['code'] = 8
#             return result

#         result['data'] = get_resume_response.text
#         result['charge_json'] = charge_json

#         # try:
#         #     # set resume unavaliable
#         #     time.sleep(random.choice([2, 3, 4]))
#         #     set_resume_unavaliable_url = 'http://www.rencaiaaa.com/resume/changeStage.do'
#         #     set_resume_unavaliable_header = {
#         #         'Accept':'*/*',
#         #         'Accept-Encoding':'gzip, deflate',
#         #         'Accept-Language':'zh-CN,zh;q=0.8',
#         #         'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
#         #         'Cookie':cookie,
#         #         'Host':'www.rencaiaaa.com',
#         #         'Origin':'http://www.rencaiaaa.com',
#         #         'Referer':'http://www.rencaiaaa.com/main.do',
#         #         'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
#         #         'X-Requested-With':'XMLHttpRequest',
#         #     }
#         #     set_resume_unavaliable_data = {
#         #         'rid': tmp_rid,
#         #         'pid':'0',
#         #         'stage':'6',
#         #         'status':'2',
#         #     }
#         #     set_resume_unavaliable_response = requests.post(set_resume_unavaliable_url, headers=set_resume_unavaliable_header, data=set_resume_unavaliable_data, proxies=proxy, allow_redirects=False, timeout=30)
#         #     if set_resume_unavaliable_response.status_code not in [200, '200']:
#         #         logger.info('not get 200 when set resume unavaliable:'+str(set_resume_unavaliable_response.status_code))
#         #         # result['code'] = 5
#         #         # return result
#         #     set_json= set_resume_unavaliable_response.json()
#         #     if set_json.get('errCode', '') not in [100, '100'] or set_json.get('msg', 'error') or set_json.get('ok', '') not in [True, 'true']:
#         #         logger.info('set resume unavaliable failed:'+set_resume_unavaliable_response.text)
#         #         # result['code'] = 6
#         #         # return result
#         # except Exception, e:
#         #     logger.info('get error when set resume in avaliable:'+str(traceback.format_exc()))
        

#         result['data'] = get_resume_response.text
#         return result

#     except Exception, e:
#         logger.info('get error when download resume:'+str(traceback.format_exc()))
#         result['code'] = 1
#         return result

# def get_coin_number(cookie, proxy):
#     logger = utils.get_logger()
#     logger.info('start to download user info.')

#     for x in xrange(3):
#         try:
#             result = {'code': 0}
#             get_coin_url = 'http://www.rencaiaaa.com/rdetail/buyInfo.do'
#             get_coin_header = {
#                 'Accept':'*/*',
#                 'Accept-Encoding':'gzip, deflate',
#                 'Accept-Language':'zh-CN,zh;q=0.8',
#                 'Cookie':cookie,
#                 'Host':'www.rencaiaaa.com',
#                 'Referer':'http://www.rencaiaaa.com/rdetail/searchRencaiDetail.do?ext=1&resumeType=1&rid=80792770&updateDate=2017-10-30&updateDateFlag=0',
#                 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
#                 'X-Requested-With':'XMLHttpRequest',
#             }
#             get_coin_response = requests.get(get_coin_url, headers=get_coin_header, allow_redirects=False, proxies=proxy, timeout=20)
#             if get_coin_response.status_code not in [200, '200']:
#                 logger.info('not get 200 when get coin.')
#                 continue
#             get_coin_json = get_coin_response.json()
#             # if get_coin_json['errorCode'] in [100, '100']:
#             #     logger.info('the account is not avaliable')
#             #     result['code'] = 3
#             #     return result
#             if get_coin_json['errCode'] not in [100, '100']:
#                 logger.info('get error when get coin number:'+str(get_coin_json))
#                 result['code'] = 2
#                 return result
#             result['code'] = 0
#             result['coin'] = get_coin_json['result'].get('reward', 0)
#             return result
#         except Exception, e:
#             logger.info(str(traceback.format_exc()))

#     else:
#         logger.info('error when get_user_info.')
#         result['code'] = 1
#     return result

# def download_thread():
#     logger = utils.get_logger()
#     logger.info('='*50+'\nstart main!!!')
#     global numbers_left
#     global sleep_tag

#     redis_client = get_redis_client()

#     mysql_pool = PersistentDB(
#         MySQLdb, 
#         host=common_settings.MYSQL_HOST, 
#         user=common_settings.MYSQL_USER,
#         passwd=common_settings.MYSQL_PASSWD, 
#         db=common_settings.MYSQL_DOWNLOAD_DB,
#         port=common_settings.MYSQL_PORT, 
#         charset='utf8'
#     )
#     mysql_conn = mysql_pool.connection()
#     mysql_cursor = mysql_conn.cursor()
#     mysql_cursor.execute('update download_record set valid=0 where valid=1 and source=22')
#     mysql_conn.commit()
#     # proxy = {'http': 'http://HD1W5PS9852Y078D:88659F653E98575E@proxy.abuyun.com:9020', 'https': 'http://HD1W5PS9852Y078D:88659F653E98575E@proxy.abuyun.com:9020'}
#     proxy = None
#     if common_settings.USE_PROXY:
#         proxy = settings.get_proxy()
#     # sqlite_conn = sqlite3.connect('zhaopingou.db')
#     # sqlite_cursor = sqlite_conn.cursor()
#     task_list = []
#     mysql_cursor.execute('select count(*) from download_record where updateTime>date(now()) and valid=2 and source=22')
#     number_today = mysql_cursor.fetchall()[0][0]
#     numbers_left -= number_today
#     numbers_left = 0 if numbers_left<0 else numbers_left


#     while True:
#         while not sleep_tag:
#             logger.info('not the correct time to buy resume, wait.')
#             time.sleep(3600)
#         if not numbers_left:
#             logger.info('the number of today not left, sleep')
#             time.sleep(1800)
#             continue
#         logger.info('the number left today is:'+str(numbers_left))
#         while not task_list:
#             while not sleep_tag:
#                 logger.info('not the correct time to buy resume, wait.')
#                 time.sleep(3600)
#             task_number = mysql_cursor.execute('select * from download_record where valid=0 and source=22 order by updateTime desc limit 1')
#             if not task_number:
#                 logger.info('there has no avaliable task in mysql ,sleep!!!')
#                 time.sleep(300)
#                 continue
#             task_list = list(mysql_cursor.fetchall())
#             break
#         task = task_list.pop()
#         if task[8]:
#             try:
#                 extend_content = json.loads(task[8])
#                 extend_content['emailJobType'] = '' if 'emailJobType'  not in extend_content else extend_content['emailJobType']
#                 extend_content['emailCity'] = '' if 'emailCity'  not in extend_content else extend_content['emailCity']
#             except Exception, e:
#                 logger.info('not find extend_content in task:'+str(task))
#                 extend_content = {"emailJobType":"","emailCity":""}
#         else:
#             extend_content = {"emailJobType":"","emailCity":""}


#         logger.info('start to deal with task:'+task[1])
#         redis_value = redis_client.get('rencaia_resume_'+task[1])
#         if not redis_value:
#             logger.info('did not get resume in redis:'+task[1])
#             mysql_cursor.execute('update download_record set valid=3 where id=%s' % str(task[0]))
#             mysql_conn.commit()
#             time.sleep(10)
#             continue
#         redis_value_list = redis_value.split('_')
#         crawl_time = redis_value_list[0]
#         real_rid = redis_value_list[1]
#         real_thirdid = redis_value_list[2]
#         srcid = '1'
#         if len(redis_value_list) > 3:
#             srcid = redis_value_list[3]
#         # crawl_time, real_rid, real_thirdid = redis_value.split('_')

#         # download

#         get_null_text_count = 0
#         for charge_count in xrange(3):
#             account, cookie = get_one_account(download=True)
#             charge_result = charge_resume(real_rid, real_thirdid, srcid, cookie, proxy)
#             if charge_result['code'] == 9:
#                 set_forbidden_account(account)
#                 continue
#             if charge_result['code'] == 10:
#                 get_null_text_count += 1
#                 continue
#             if charge_result['code']:
#                 set_unavaliable_account(account)
#                 continue
#             break
#         else:
#             logger.info('get error after 3 times try to charge resume')
#             if get_null_text_count == 3:
#                 try:
#                     mysql_cursor.execute('update download_record set valid=3 where id=%s' %  str(task[0]))
#                     mysql_conn.commit()
#                     logger.info('get 3 null text of resume:'+task[1])
#                 except Exception, e:
#                     logger.info(str(traceback.format_exc()))
#             continue

#         # if u'存在被盗用的风险' in charge_result['data']:
#         #     logger.info(u'find 存在被盗用的风险 in page:'+str(account))
#         #     set_forbidden_account(account)
#         #     continue

#         if u'该用户暂无求职意向，已在外网设置简历不公开' in charge_result['data']:
#                 # logger.info('un publish resume:'+str(resume)+ 'account:'+account['username'])
#                 # set_forbidden_account(account)
#                 continue
#         # elif charge_result['code']:
#         #     logger.info('get error when charge!!!'+str(charge_result))
#         #     account_coin = 0
#         #     break

#         resume_uuid = uuid.uuid1()
#         try:
#             content = {'html':charge_result['data']}
#             content['email'] = charge_result['charge_json'].get('mail')
#             content['phone'] = charge_result['charge_json'].get('phone')
#             content['name'] = charge_result['charge_json'].get('name')
#             content = json.dumps(content, ensure_ascii=False)
#             mysql_cursor.execute(u'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values ("REN_CAI", %s, "python", %s, now(), %s, %s, %s, %s)' , (content, resume_uuid, account['username'], extend_content['emailJobType'], extend_content['emailCity'],  task[1]))
#             mysql_conn.commit()
#             numbers_left -= 1
#             mysql_cursor.execute('select last_insert_id()')
#             save_mysql_ids = mysql_cursor.fetchall()
#             if not save_mysql_ids or not save_mysql_ids[0]:
#                 logger.info('insert into mysql error!!!')
#                 raise Exception
#             save_mysql_id = save_mysql_ids[0][0]
#         except Exception, e:
#             print str(traceback.format_exc())
#             continue

#         kafka_data = {
#             "channelType": "WEB",
#             "content": {
#                 "content": content,
#                 "id": save_mysql_id,
#                 "createBy": "python",
#                 "createTime": int(time.time()*1000),
#                 "ip": '',
#                 "resumeSubmitTime": '',
#                 # "resumeUpdateTime": resume.get('refDate', ''),
#                 "resumeUpdateTime": '',
#                 "source": "REN_CAI",
#                 "trackId": str(resume_uuid),
#                 "avatarUrl": '',
#                 'emailJobType': extend_content['emailJobType'],
#                 'emailCity': extend_content['emailCity'],
#                 'email': account['username'],
#                 'subject': task[1],
#             },
#             "interfaceType": "PARSE",
#             "resourceDataType": "RAW",
#             "resourceType": "RESUME_INBOX",
#             "source": "REN_CAI",
#             "trackId": str(resume_uuid),
#         }
#         logger.info('the raw id is:'+str(kafka_data['content']['id']))
#         try:
#             buf = StringIO()
#             f = gzip.GzipFile(mode='wb', fileobj=buf)
#             f.write(json.dumps(kafka_data))
#             f.close()
#             msg_body = base64.b64encode(buf.getvalue())
#             msg = Message(msg_body)
#             push_mns_error_tag = False
#             for send_message_count in range(common_settings.MNS_SAVE_RETRY_TIME):
#                 try:
#                     mns_client = get_mns_client()
#                     mns_client.send_message(msg)
#                     break
#                 except Exception, e:
#                    logger.info('error when mns send message, time:'+str(send_message_count)+':'+str(e))
#                    if 'The length of message should not be larger than MaximumMessageSize.' == e.message:
#                         logger.info('resume too long to push to mns:'+task[1])
#                         try:
#                             mysql_cursor.execute('update download_record set valid=3, downloadBy="%s" where id=%s' % (str(account['username']), str(task[0])))
#                             mysql_conn.commit()
#                         except Exception, e:
#                             logger.info(str(traceback.format_exc()))
#                             time.sleep(600)
#                         push_mns_error_tag = True
#                         break
#             else:
#                 raise Exception
#             if push_mns_error_tag:
#                 continue
#         except Exception, e:
#             logger.info('get error when produce mns, exit!!!'+str(traceback.format_exc()))
#             send_dingding_text('rencaia resume: download thread return.')
#             return 3
#         try:
#             mysql_cursor.execute('update download_record set valid=2, downloadBy="%s" where id=%s' % (str(account['username']), str(task[0])))
#             mysql_conn.commit()
#             # del task_list[index]
#         except Exception, e:
#             logger.info(str(traceback.format_exc()))
#             time.sleep(600)
#             continue
#         #time.sleep(2)

#         coin_number_result = get_coin_number(cookie, proxy)
#         if not coin_number_result['code']:
#             update_coin_number_left(account, coin_number_result['coin'])
#             if coin_number_result['coin'] < 10:
#                 logger.info('the coin number of account:'+str(account) + ' is less than 10')
#         else:
#             logger.info('get unkown error:'+ str(coin_number_result))

#     logger.info('quit')
#     mysql_cursor.close()
#     mysql_conn.close()

def test():
    # print login('liuxiao2shf', 'jinqian4611', 'dongdong4611')
    # task = {"area_name": u"天津", "job_code": "918", "area_code": "120000", "model_name": "zhilian", "job_name": u"其他"}
    # cookie='JSESSIONID=C418E9DA2B9FB1051BEE86F19076CE4D'
    # resume_id = '80711980'
    # print charge_resume(resume_id, cookie, None)
    # awake_one_task(task)
    # task = {'residence_ids': '1', 'residence_name': u'北京', 'function_ids3':'293', 'function3_strs': u'IT技术/研发经理/主管', 'function_id_name': u'IT技术/研发经理/主管'}
    # awake_one_task(task)
    # print get_list(cookie, 3, param, {'http': 'http://47.93.115.141:3128', 'https': 'http://47.93.115.141:3128'})
    # print get_resume('51036212', cookie, {'http': 'http://47.93.115.141:3128', 'https': 'http://47.93.115.141:3128'})
    # account = {'username': '17056385969', 'passwd': 'uQlTn6Bv', 'id': 824}
    # set_unavaliable_account(account)
    # set_forbidden_account(account)
    cookie = 'PHPSESSID=24b353966c5189c0ce13865c64f79d0d; my_url=www.job1001.com'
    task = {'joblist': u'总经理/总裁/首席执行官CEO', 'regionid': '110000', 'region_name': u'北京', 'use_keyword': '1'}
    # awake_one_task(task)
    print get_list(cookie, 1, task, None)
    # print get_list_with_keyword(cookie, 1, task, None)
    # url = 'http://www.job1001.com/myNew/resume/ResumePreview.php?ResumeId=job1001928425808&r=8dbfb7d039a7eb769d20fc99e59d740d4e242&zw=&jobid=&readsourceflag=3&cmxid=&gjTag=2&SearchKey=%C7%EB%CA%E4%C8%EB%BC%F2%C0%FA%B9%D8%BC%FC%B4%CA%A3%AC%B6%E0%B8%F6%B4%CA%BF%C9%D2%D4%D3%C3%BF%D5%B8%F1%B8%F4%BF%AA'
    # a=  get_resume(url)
    # a = get_resume_has_real_rid('2567308023', '117659691', cookie)
    # a = charge_resume('2675500768', '101764320', cookie)
    # f=open('123', 'w')
    # f.write(json.dumps(a, ensure_ascii=False))
    # f.close()

if __name__ == '__main__':
    
    utils.set_setting(settings.project_settings)
    logger = utils.get_logger()
    logger.info('='*50 + 'start main')
    # test()

    global numbers_left, get_task_queue
    numbers_left= common_settings.NUMBERS_ERVERYDAY
    get_task_queue = Queue.Queue(maxsize=common_settings.QUEUE_MAX_SIZE)

    change_time_thread_one = threading.Thread(target=change_time_thread, name="Change_Time_Thread")
    change_time_thread_one.start()

    dowload_number = common_settings.SEARCH_THREAD_NUMBER

    search_thread_list = []
    for x in xrange(dowload_number):
        search_thread = threading.Thread(target=awake_thread, name='Thread-'+str(x))
        search_thread.start()
        search_thread_list.append(search_thread)

    # download_thread_one = threading.Thread(target=download_thread, name='Download_Thread')
    # download_thread_one.start()

    # download_thread_one.join()

    for i in search_thread_list:
        i.join()
    change_time_thread_one.join()

    logger.info('done.')
