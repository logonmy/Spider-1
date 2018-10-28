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
import create_task

stop_tag = False
buy_tag = True
get_task_queue = None
push_task_time = None
push_task_keyword_tag = '0'
push_task_lock = threading.Lock()


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
    if not push_task_time or (datetime.datetime.now() - push_task_time).seconds > 14400:
        send_dingding_text(u'开始推送纷简历简历任务.')
        create_task.create_task_from_mysql()
        # create_task.create_task_from_mysql(push_task_keyword_tag)
        # push_task_keyword_tag = '0' if push_task_keyword_tag == '1' else '1'
        push_task_time = datetime.datetime.now()
    push_task_lock.release()


def get_one_account(download=False):
    # return {'username': '18310399539', 'passwd': 'jinqian4611', 'id': 805}, 'JSESSIONID=77D0FA6068D0953277260B9C50838B6A'
    logger = utils.get_logger()
    logger.info('start to get a search account.')
    if download:
        url = common_settings.ACCOUNT_URL % ('RESUME_FEN', 'RESUME_INBOX')
    else:
        url = common_settings.ACCOUNT_URL % ('RESUME_FEN', 'RESUME_FETCH')
    while True:
        try:
            response = requests.get(url, timeout=10)
            response_json = response.json()
            if response_json['code'] in [200, '200'] and response_json['data']:
                account = {'username': response_json['data']['userName'], 'passwd': response_json['data']['password'],
                           'id': response_json['data']['id']}
                cookie = response_json['data']['cookie']
                # cookie = json.loads(response_json['data']['cookie'])
                if not cookie:
                    logger.info('not get cookie in result, set to relogin and try again.')
                    set_unavaliable_account(account)
                    continue
                return account, cookie
        except Exception, e:
            logger.info('get error when get search account:' + str(traceback.format_exc()))
        time.sleep(3600)


def set_unavaliable_account(account):
    logger = utils.get_logger()
    logger.info('set unavaliable :' + str(account))
    url = common_settings.SET_INVALID_URL % (account['username'], account['passwd'], common_settings.SOURCE)
    try:
        response = requests.get(url)
        logger.info('set unavaliable account response:' + response.text)
    except Exception, e:
        logger.info(str(traceback.format_exc()))


redis_client = None


def get_redis_client():
    global redis_client
    if not redis_client:
        # redis_pool = redis.ConnectionPool(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
        # redis_client = redis.Redis(redis_pool)
        redis_client = redis.Redis(host='127.0.0.1', port='6379', db=0)
    return redis_client


def awake_thread():
    logger = utils.get_logger()
    logger.info('process_thread start!!!')
    global stop_tag
    while not stop_tag:
        task_traceid = str(uuid.uuid1())
        params = {'traceID': task_traceid, 'callSystemID': common_settings.CALLSYSTEMID,
                  'taskType': common_settings.TASK_TYPE, 'source': common_settings.SOURCE, 'limit': 1}
        param_str = '&'.join([str(i) + '=' + str(params[i]) for i in params])
        task_url = common_settings.TASK_URL + common_settings.GET_TASK_PATH + param_str
        task_result = utils.download(url=task_url, is_json=True)
        if task_result['code'] or task_result['json']['code'] not in [200, '200']:
            logger.info('get error task, sleep... url is:' + task_url + ' return is:' + str(task_result))
            time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        logger.info('=' * 30 + 'get task!!!' + str(task_result))
        if not task_result['json']['data']:
            logger.info('did not get task_result data:' + str(task_result))
            push_task()
            # time.sleep(common_settings.SERVER_SLEEP_TIME)
            time.sleep(120)
            continue
        process_result = {'code': -1, 'executeParam': task_result['json']['data'][0]['executeParam']}
        try:
            process_result = awake_one_task(json.loads(task_result['json']['data'][0]['executeParam']))
            print '---------------the process_result:', process_result
        except Exception, e:
            logger.info('error when process:' + str(traceback.format_exc()))
        return_task_url = common_settings.TASK_URL + common_settings.RETURN_TASK_PATH
        return_task_traceid = str(uuid.uuid1())
        return_data = {}
        return_data['traceID'] = return_task_traceid
        return_data['callSystemID'] = common_settings.CALLSYSTEMID
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
                print return_task_result
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


def login(username, passwd, proxy):
    logger = utils.get_logger()
    result = {'code': 0, 'cookie': ''}
    if not username or not passwd:
        logger.info('the username or passwd is None.')
        result['code'] = 2
        return result
    logger.info('start to login ' + username)
    session = requests.Session()
    for x in xrange(3):
        try:
            login_url = 'http://www.fenjianli.com/login/login.htm'
            login_header = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Host': 'www.fenjianli.com',
                'Origin': 'http://www.fenjianli.com',
                'Referer': 'http://www.fenjianli.com/login/home.htm',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }
            login_data = {
                'username': username,
                'password': passwd,
            }
            login_response = session.post(login_url, headers=login_header, data=login_data, allow_redirects=False,
                                          proxies=proxy)
            if login_response.status_code not in [200, '200']:
                logger.info('login response status code:' + str(login_response.status_code))
                continue
            if '登录IP异常' in login_response.content:
                logger.error('代理异常 %s %s' % (login_response.content, proxy))
                continue
            if '登录次数或IP超限' in login_response.content:
                logger.error('当前登录次数到达上限 %s' % proxy)
                continue
            login_json = login_response.json()
            if login_json.get('success', '') != '/search/home.htm':
                logger.info('login  error response:' + str(login_response.text))
            result['cookie'] = dict(session.cookies)
            result['code'] = 0
            return result
        except Exception, e:
            logger.info(str(traceback.format_exc()))
            continue
    result['code'] = 1
    return result


def change_time_thread():
    logger = utils.get_logger()
    logger.info('start check time!!!')
    # global change_time_tag
    global stop_tag
    global numbers_left
    global buy_tag
    start_day = datetime.datetime.now().day
    while not stop_tag:
        hour_now = datetime.datetime.now().hour
        # if not change_time_tag and start_day != datetime.datetime.now().day:
        if start_day != datetime.datetime.now().day:
            start_day = datetime.datetime.now().day
            numbers_left = common_settings.NUMBERS_ERVERYDAY
            logger.info('has change day, start_day is ' + str(start_day))
        if hour_now > 7 and hour_now < 22:
            buy_tag = True
        else:
            buy_tag = False
        time.sleep(3600)


def get_list(cookie, page_numner, params, proxy=None):
    logger = utils.get_logger()
    result = {'code': 0, 'data': []}
    logger.info('use proxy ' + str(proxy) + ' to download list')

    for x in xrange(3):
        time.sleep(2)
        try:
            list_header = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': cookie,
                'Host': 'www.fenjianli.com',
                'Origin': 'http://www.fenjianli.com',
                # 'Referer':'http://www.fenjianli.com/search/home.htm',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }

            if params['model_name'] == 'zhilian':
                list_url = 'http://www.fenjianli.com/search/search.htm'
                list_data = {
                    'jobs': params['job_code'],
                    'updateDate': '7',
                    'hareas': params['area_code'],
                    'rows': '30',
                    'sortBy': '1',
                    'sortType': '1',
                    'offset': 30 * (page_numner - 1),
                    '_random': str(random.random()),
                }
                list_header['Referer'] = 'http://www.fenjianli.com/search/home.htm'
            elif params['model_name'] == 'liepin':
                list_url = 'http://www.fenjianli.com/search/liepinSearch.htm'
                list_data = {
                    'searchNear': 'on',
                    'areas': params['area_code'],
                    'hJobs': params['job_code'] + ',',
                    'rows': '30',
                    'sortBy': '1',
                    'sortType': '1',
                    'degree': '0-0',
                    'offset': 30 * (page_numner - 1),
                    '_random': str(random.random()),
                }
                list_header['Referer'] = 'http://www.fenjianli.com/search/liepinHome.htm'
            else:
                logger.info('unkoen model_name:' + model_name)
                result['code'] = 4
                continue
            list_response = requests.post(list_url, headers=list_header, data=list_data, proxies=proxy,
                                          allow_redirects=False, timeout=30, verify=False)
            if list_response.status_code in [302, '302'] and list_response.headers.get('Location',
                                                                                       '') == 'http://www.fenjianli.com/login/home.htm':
                logger.info('invalid cookie, need login.')
                result['code'] = 5
                continue
            elif list_response.status_code not in [200, '200']:
                logger.info('list response status code:' + str(list_response.status_code))
                result['code'] = 1
                continue
            list_json = list_response.json()
            if 'totalSize' not in list_json or 'list' not in list_json:
                logger.info('error retun of list response:' + str(list_response.text))
                result['code'] = 2
                continue
            result['ids'] = []
            for resume in list_json['list']:
                result['ids'].append([resume['id'], resume['updateDate']])
            result['total'] = list_json['totalSize']
            logger.info(str(result))
            return result
        except Exception, e:
            logger.info(str(traceback.format_exc()))
            result['code'] = 6
            continue
    else:
        logger.info('get error after 3 times retry when download list.')
        result['code'] = result['code'] if not result['code'] else 3
        return result


def get_resume(resume_id, cookie, model_name, proxy=None):
    time.sleep(1)
    logger = utils.get_logger()
    result = {'code': 0}
    if not proxy:
        proxy = {'http': 'http://H463CA16CA05YUUD:952FCA274D3C9DB2@http-dyn.abuyun.com:9020',
                 'https': 'https://H463CA16CA05YUUD:952FCA274D3C9DB2@http-dyn.abuyun.com:9020', }

    resume_url = 'http://www.fenjianli.com/search/getDetail.htm'
    logger.info('use proxy ' + str(proxy) + 'to download resume')
    resume_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cookie': cookie,
        'Host': 'www.fenjianli.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    }

    if model_name == 'liepin':
        resume_headers['Referer'] = 'http://www.fenjianli.com/search/liepinDetail.htm?ids=' + base64.b64encode(
            resume_id)
    elif model_name == 'zhilian':
        resume_headers['Referer'] = 'http://www.fenjianli.com/search/detail.htm?ids=' + base64.b64encode(resume_id)
    else:
        logger.info('unkown model_name:' + model_name)
        result['code'] = 5
        return result
    resume_data = {
        'id': resume_id,
        '_random': str(random.random()),
    }

    for i in xrange(3):
        try:
            resume_response = requests.post(resume_url, headers=resume_headers, data=resume_data, allow_redirects=False,
                                            proxies=proxy, timeout=30, verify=False)
            if resume_response.status_code in [302, '302'] and resume_response.headers.get('Location',
                                                                                           '') == 'http://www.fenjianli.com/login/home.htm':
                logger.info('invalid cookie, need login.')
                result['code'] = 1
                return result
            elif resume_response.status_code not in [200, '200']:
                logger.info('did not get 200 when download resume:' + str(resume_response.status_code))
                result['code'] = 2
                return result
            resume_json = resume_response.json()
            if 'id' not in resume_json:
                logger.info('did not get resume success!!!' + resume_response.text)
                result['code'] = 3
                return result
            result['code'] = 0
            result['json'] = resume_json
            break
        except Exception, e:
            logger.info('get exception when download resume:' + str(traceback.format_exc()))
            result['code'] = 4
            # time.sleep(3)

    return result


def awake_one_task(task):
    logger = utils.get_logger()
    logger.info('start aweak one task')
    relogin_time = 3
    redis_client = get_redis_client()
    result = {'code': 0, 'executeParam': task}
    proxy = None
    if common_settings.USE_PROXY:
        proxy = settings.get_proxy()

    account, cookie = get_one_account()

    logger.info(str(cookie))
    logger.info('deal with:' + str(task))

    page_now = 1
    download_day = str(time.localtime().tm_mon) + '-' + str(time.localtime().tm_mday)
    download_day_datetime = datetime.datetime.today()
    while page_now != -1:
        logger.info('start download page:' + str(page_now))
        # if not account:
        account, cookie = get_one_account()
        list_result = get_list(cookie, page_now, task, proxy)
        # time.sleep(2)
        if list_result['code'] == 5:
            set_unavaliable_account(account)
            account = None
            continue
        elif list_result['code']:
            logger.info('get error list result:' + str(list_result))
            page_now = -1
            continue
        logger.info('page number of now is ' + str(page_now) + ' all number is:' + str(list_result['total']))
        for resume in list_result['ids']:
            # logger.info('sleep 5')
            # time.sleep(5)
            list_resume_update_time = datetime.datetime.strptime(resume[1], '%Y-%m-%d')
            if (download_day_datetime - list_resume_update_time).days > 7:
                logger.info("find resume who's update time before 3 days.")
                page_now = -1
                continue
            if not account:
                account, cookie = get_one_account()
            has_find_in_redis = False
            resume_key = 'fenjianli_resume_' + str(resume[0])
            try:
                resume_download_time = redis_client.get(resume_key)
                if resume_download_time == download_day:
                    has_find_in_redis = True
                else:
                    redis_client.set(resume_key, download_day)
            except Exception, e:
                redis_client.set(resume_key, download_day)
            if has_find_in_redis:
                logger.info('has find %s in redis' % resume_key)
                continue
            else:
                logger.info('not find %s in redis' % resume_key)

            resume_result = get_resume(resume[0], cookie, task['model_name'], proxy=proxy)
            if resume_result['code'] == 1:
                set_unavaliable_account(account)
                account = None
                continue
            if resume_result['code'] == 3:
                logger.info('need set valid=0 of account:' + str(account))
            if resume_result['code']:
                logger.info('get error resume:' + str(resume_result))
                continue

            resume_uuid = uuid.uuid1()
            try:
                sql = 'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values (%s, %s, "python", %s, now(), %s, %s, %s, %s)'
                sql_value = (common_settings.SOURCE, json.dumps(resume_result['json'], ensure_ascii=False), resume_uuid,
                             str(account['username']), task['job_name'], task['area_name'], str(resume[0]))

                resume_update_time = resume_result['json']['updateDate']
                kafka_data = {
                    "channelType": "WEB",
                    "content": {
                        "content": json.dumps(resume_result['json'], ensure_ascii=False),
                        "id": '',
                        "createBy": "python",
                        "createTime": int(time.time() * 1000),
                        "ip": '',
                        "resumeSubmitTime": '',
                        "resumeUpdateTime": resume_update_time,
                        "source": common_settings.SOURCE,
                        "trackId": str(resume_uuid),
                        "avatarUrl": '',
                        "email": str(account['username']),
                        'emailJobType': task['job_name'],
                        'emailCity': task['area_name'],
                        'subject': str(resume[0])
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
                logger.info('get error when write mns, exit!!!' + str(traceback.format_exc()))
                # return
            time.sleep(1)
            # return

        page_now = -1 if (page_now - 1) * 30 >= list_result['total'] or page_now == -1 else page_now + 1

    logger.info('has finish deal with:' + str(task))
    time.sleep(3)
    result['code'] = 0
    return result


def test():
    task = {"area_name": u"天津", "job_code": "918", "area_code": "120000", "model_name": "zhilian", "job_name": u"其他"}
    cookie = {'code': 0, 'cookie': {'SERVERID': '70356234b78238645df699ef52f30d81|1522806241|1522806241',
                                    'JSESSIONID': 'A3CF43A5891596C98EDE1C2D5E5BE76A'}}
    cookie_str = cookie = 'SERVERID=' + cookie.get('cookie').get('SERVERID') + ';JSESSIONID=' + cookie.get(
        'cookie').get(
        'JSESSIONID')
    # awake_one_task(task)
    print get_list(cookie=cookie_str
                   , page_numner=1, task=task, proxy=settings.get_proxy())
    # print get_resume('1015973541', cookie, 'zhilian', {'http': 'http://47.93.115.141:3128', 'https': 'http://47.93.115.141:3128'})
    account = {'username': '18310399539', 'passwd': 'jinqian4611', 'id': 805}
    set_unavaliable_account(account)


if __name__ == '__main__':
    utils.set_setting(settings.project_settings)
    logger = utils.get_logger()
    logger.info('=' * 50 + 'start main')
    # result = login(username='18629947965', passwd='l56441193', proxy=settings.get_proxy())
    # print result

    test()

    # global numbers_left, get_task_queue
    # numbers_left= common_settings.NUMBERS_ERVERYDAY
    # get_task_queue = Queue.Queue(maxsize=common_settings.QUEUE_MAX_SIZE)

    # change_time_thread_one = threading.Thread(target=change_time_thread, name="Change_Time_Thread")
    # change_time_thread_one.start()
    #
    # dowload_number = common_settings.SEARCH_THREAD_NUMBER
    #
    # search_thread_list = []
    # for x in xrange(dowload_number):
    #     search_thread = threading.Thread(target=awake_thread, name='Thread-'+str(x))
    #     search_thread.start()
    #     search_thread_list.append(search_thread)
    #
    # # download_thread_one = threading.Thread(target=download_thread, name='Download_Thread')
    # # download_thread_one.start()
    #
    # # download_thread_one.join()
    #
    # for i in search_thread_list:
    #     i.join()
    # change_time_thread_one.join()
    #
    # logger.info('done.')
