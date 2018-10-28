#!coding:utf8
# 本程序共分三种线程，入口分别为以下三个方法，其他方法均被此三个方法调用
#
# download_thread（一个）：简历购买线程。主要流程：从spider库中的download_resume表中根据updateTime排序拿取最近的，valid为0的任务，并下载，下载完成，将valid置为2，并设置downloadBy参数为下载使用的账号，如果下载三次失败，则设置此任务的valid为3，以后不再下载
#
# awake_thread（若干）：简历搜索唤醒线程。主要流程：从调度拿取任务，搜索列表页，去重后拿取详情页，并推送mysql和mns进行唤醒
#
# change_time_thread（一个）：心跳线程，每次sleep一个小时，之后更改一次全局变量，如numbers_left（更新每天购买简历数上限），buy_tag（可控制购买线程在晚上22点至早上8点停止购买）
#
# 其他方法均为被调用方法

import sys

sys.path.append('../common')
import requests
import time
import traceback
import json
import random
import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import uuid
import re
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
import create_task

from mf_utils.extend.dingding_robot import DingDingRobot
from mf_utils.data.RedisHash import RedisHash
from mf_utils.queue.RedisQueue import RedisQueue
from mf_utils.common import datetime2str, cookie2str
from create_task import city_dict, use_static_proxy_list

resume_update_re = re.compile(r'更新时间：([\d\-])*')
coin_number_re = re.compile(u'如需联络方式，仅需<span>(\d+)')
stop_tag = False  # 未用，勿删
buy_tag = True  # True：当前能购买简历；False：当前不能购买简历，用于控制8：00-22：00购买简历
coin_warning_dict = {}  # key账号名，value：是否已经报警，用于控制当天该购买账号的下载点是否已经报警过
dogfood_warning_dict = {}  # key账号名，value：是否已经报警，用于控制当天该购买账号的狗粮数是否已经报警过

push_task_time = None  # 上一次推送任务时间
push_task_keyword_tag = '0'  # 推送关键字搜索还是只能搜索任务
push_task_lock = threading.Lock()  # 推送任务锁

# 记录每个帐号每天的搜索数量
search_use_record = RedisHash('zhao_pin_gou_resume_search_use_record',
                              host='172.16.25.36',
                              port='6379',
                              password='',
                              db=1)

download_queue = RedisQueue('zhao_pin_gou_download_queue',
                            host='172.16.25.36',
                            port='6379',
                            password='',
                            db=1)
download_lock = threading.Lock()
download_task_time = ''

# 钉钉机器人，发送钉钉消息使用，在send_dingding_text方法中被调用
# 调用此方法发送钉钉消息
dingding_robot = None


def send_dingding_text(text):
    global dingding_robot
    if not dingding_robot:
        dingding_robot = DingDingRobot(
            'eb749abfe9080a69da6524b77f589b8f6ddbcc182c7a41bf095b095336edb0a1')
    dingding_robot.send_text(text)


def is_account_limited(username, search_limit):
    """
    用于更新当日进入详情页的次数
    :param username: 当前使用的帐号
    :param search_limit: 使用上限
    :return:
    """
    global search_use_record
    today = datetime2str(datetime.datetime.now(), fmt='%Y-%m-%d')

    count = search_use_record.hget(username + '_' + today)

    if not count:
        count = 0
    else:
        count = int(count)
        if count > search_limit:
            logger.warning('%s 该帐号已达到当天进入详情页上限: %s'
                           % (username, search_limit))
            return True
    count += 1
    logger.info('%s 当前已进入详情页%s次，剩余%s次'
                % (username, count, search_limit - count))
    search_use_record.hset(username + '_' + today, count)
    return False


# 推送任务
def push_task():
    """
    若调度中拿不到唤醒任务时，会调用此方法重新推送任务
    每次只有一个线程在推送任务，推送完毕将推送时间记录下来，并在14400秒之内不再推送第二轮
    """
    logger = utils.get_logger()
    global push_task_time
    global push_task_lock
    global push_task_keyword_tag
    if push_task_lock.locked():
        return
    # 为程序加锁
    push_task_lock.acquire()
    if not push_task_time or (
            datetime.datetime.now() - push_task_time).seconds > 14400:
        # 发送钉钉消息
        send_dingding_text(u'开始推送招聘狗简历任务.')
        # 调用create_task.py中的方法推送任务
        create_task.create_task_from_mysql(push_task_keyword_tag)
        push_task_keyword_tag = '0' if push_task_keyword_tag == '1' else '1'
        push_task_time = datetime.datetime.now()
    push_task_lock.release()


# 从account中获取一个账号
def get_one_account(download=False):
    """
    从account模块获取账号
    args:
        download
            True:获取可购买账号
            False:获取搜索账号
    """
    logger = utils.get_logger()
    logger.info('start to get a search account.')
    if download:
        url = common_settings.ACCOUNT_URL % ('ZHAO_PIN_GOU', 'RESUME_INBOX')
    else:
        url = common_settings.ACCOUNT_URL % ('ZHAO_PIN_GOU', 'RESUME_FETCH')
    account_sleep_tag = 10
    while True:
        try:
            response = requests.get(url, timeout=30)
            response_json = response.json()
            if response_json['code'] in [200, '200'] and response_json['data']:
                account = {'username': response_json['data']['userName'],
                           'passwd': response_json['data']['password'],
                           'id': response_json['data']['id']}
                cookie = json.loads(response_json['data']['cookie'])
                token = cookie.get('hrkeepToken', '')
                try:
                    proxy_origin = json.loads(
                        response_json['data']['proxy'])
                    proxy = {
                        'http': 'http://%s:%s' % (proxy_origin['ip'],
                                                  proxy_origin['port']),
                        'https': 'https://%s:%s' % (proxy_origin['ip'],
                                                    proxy_origin['port']),
                    }
                except Exception as e:
                    logger.exception("error:" + str(e))

                try:
                    extra = json.loads(response_json['data']['extraContent'])
                except ValueError:
                    extra = None

                if not cookie or not token:
                    logger.info(
                        'not get cookie or token in result, set to relogin and try again.')
                    set_unavaliable_account(account)
                    time.sleep(random.randint(1, 5))
                    continue

                try:
                    update_last_city(cookie=cookie, proxies=proxy)
                except Exception as e:
                    logger.exception('切换城市失败： %s' % str(e))
                    continue

                logger.info('thread using account: ' + account['username'])
                return account, cookie, token, proxy, extra
            else:
                logger.info(response.text)
        except Exception as e:
            logger.exception('get error when get search account:' + str(e))
        logger.info('not get cookie from account, account_sleep_tag is:' + str(
            account_sleep_tag))
        if not account_sleep_tag:
            send_dingding_text(u'招聘狗下载没有获取到账号')
            account_sleep_tag = 10
            time.sleep(600)
        else:
            time.sleep(20)
            account_sleep_tag -= 1


# 设置账号无效
def set_unavaliable_account(account):
    """
    设置账号无效，重新登录
    """
    logger = utils.get_logger()
    logger.info('set unavaliable :' + str(account))
    url = common_settings.SET_INVALID_URL % (
        account['username'], account['passwd'], common_settings.SOURCE)
    try:
        response = requests.get(url, timeout=30)
    except Exception as e:
        logger.info(str(e))


def update_last_city(cookie, proxies):
    url = 'http://qiye.zhaopingou.com/zhaopingou_interface/update_last_city' \
          '?timestamp=%s' % str(int(time.time()))
    headers = {
        'Accept': 'multipart/form-data',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-type': 'application/x-www-form-urlencoded',
        'Host': 'qiye.zhaopingou.com',
        'Origin': 'http://qiye.zhaopingou.com',
        'Pragma': 'no-cache',
        'Referer': 'http://qiye.zhaopingou.com/resume?update_time=1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
        'Cookie': cookie2str(cookie)
    }
    data = {
        'cityId': '-1',
        'clientNo': '',
        'userToken': cookie['hrkeepToken'],
        'clientType': '2'
    }

    res = requests.post(url, headers=headers, data=data, proxies=proxies,
                        timeout=30)

    if res.json().get('errorCode') == 1:
        logger.info('成功切换到全国站')
    else:
        logger.warning('切换搜索站点失败.')


# 更新account中账号的下载点数
def update_coin_number_left(account, coin_number):
    """
    更新账号可用下载数
    """
    logger = utils.get_logger()
    logger.info('update coin number:' + str(account) + ' ' + str(coin_number))
    url = common_settings.UPDATE_DOWNLOAD_SCORE
    data = {
        'id': account['id'],
        'downloadRecord': coin_number,
        'userName': account['username'],
        'password': account['passwd'],
        'source': common_settings.SOURCE,
    }
    try:
        response = requests.post(url, data=data, timeout=30)
    except Exception as e:
        logger.exception(str(e))


redis_client = None


def get_redis_client():
    """
    获取redis连接客户端
    """
    global redis_client
    if not redis_client:
        redis_client = redis.Redis(host=common_settings.REDIS_IP,
                                   port=common_settings.REDIS_PORT, db=1)
    return redis_client


def get_mns_client():
    """
    获取mns客户端接口
    """
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID,
                          common_settings.ACCKEY, common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client


# 心跳线程入口
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
            coin_warning_dict = {}
            dogfood_warning_dict = {}
            logger.info('has change day, start_day is ' + str(start_day))
        if hour_now > 7 and hour_now < 22:
            buy_tag = True
        else:
            buy_tag = False
        time.sleep(3600)


# 按职能获取列表页
def get_list(cookie, page_numner, params, proxy=None, token=''):
    """
    args:
        cookie: 账号的cookie
        page_numner：要下载列表页的页数
        params：下载列表页的参数，职能、城市
        proxy：下载使用的代理
        token：cookie中的hrToken
    return：
        {'code':0, 'json': []}
        code为0：成功
        code为5：需要重新登录
        code非0：下载失败
    """
    time.sleep(3)
    logger = utils.get_logger()
    result = {'code': 0}

    logger.info('use proxy ' + str(proxy) + 'to download list')

    # logger.info(cookie)

    list_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/find_warehouse_by_position_new?timestamp=' + str(
        int(time.time() * 1000))
    list_data = {
        # 'pageSize': page_numner - 1,
        # 'pageNo': 25,
        # 'keyStr': '',
        # 'keyStrPostion': int(params['pId']),
        # 'postionStr': params['positionName'].encode('utf8'),
        # 'startDegrees': -1,
        # 'endDegress': -1,
        # 'startAge': 0,
        # 'endAge': 35,
        # 'gender': -1,
        # 'region': '',
        # 'timeType': 1,
        # 'startWorkYear': -1,
        # 'endWorkYear': -1,
        # 'beginTime': '',
        # 'endTime': '',
        # # -1 any, 0 free, 1 money
        # 'isMember': -1,
        # 'hopeAdressStr': int(params['hopeAdressStr']),
        # # 'hopeAdressStr':2,
        # # 'cityId': int(params['hopeAdressStr']),
        # 'cityId': -1,
        # 'updateTime': '',
        # 'tradeId': '',
        # 'clientNo': '',
        # # 'userToken':login_result['cookie']['hrkeepToken'],
        # 'userToken': token,
        # 'clientType': 2,
        'pageSize': page_numner - 1,
        'pageNo': '25',
        'keyStr': '',
        'companyName': '',
        'schoolName': '',
        'keyStrPostion': int(params['pId']),
        'postionStr': params['positionName'].encode('utf8'),
        'startDegrees': '-1',
        'endDegress': '-1',
        'startAge': '0',
        'endAge': '35',
        'gender': '-1',
        'region': '',
        'timeType': '1',
        'startWorkYear': '-1',
        'endWorkYear': '-1',
        'beginTime': '',
        'endTime': '',
        'isMember': '-1',
        'hopeAdressStr': str(int(params['hopeAdressStr'])),
        'cityId': '-1',
        'updateTime': '',
        'tradeId': '',
        'startDegreesName': '',
        'endDegreesName': '',
        'tradeNameStr': '',
        'regionName': '',
        'isC': '1',
        'is211_985_school': '0',
        'clientNo': '',
        'userToken': token,
        'clientType': '2',
    }

    referer_url = 'http://qiye.zhaopingou.com/resume?key='
    if page_numner not in [0, '0']:
        referer_url = 'http://qiye.zhaopingou.com/resume/free?hopeAdressStr' \
                      '=%s&startAge=0&endAge=30&update_time=1&pn=%s' \
                      % (str(int(params['hopeAdressStr'])),
                         str(page_numner - 1))

    list_headers = {
        'Accept': 'multipart/form-data',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-type': 'application/x-www-form-urlencoded',
        'Host': 'qiye.zhaopingou.com',
        'Origin': 'http://qiye.zhaopingou.com',
        'Referer': referer_url,
        # 'Referer': 'http://qiye.zhaopingou.com/resume/free?key=Java&beginDegreesType=3&endDegreesType=100&startAge=20&endAge=30&update_time=1&pn=4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Cookie': '; '.join([i[0] + '=' + i[1] for i in cookie.items()])
    }
    for x in xrange(common_settings.DOWNLOAD_RETRY_TIME):
        try:
            list_response = requests.post(list_url, headers=list_headers,
                                          data=list_data,
                                          allow_redirects=False, proxies=proxy,
                                          timeout=30)

            if list_response.status_code not in [200, '200']:
                logger.info('did not get 200 when download list:' + str(
                    list_response.status_code))
                result['code'] = 2
                return result
            list_json = list_response.json()
            if 'Set-Cookie' in list_response.headers and 'JSESSIONID=' in \
                    list_response.headers['Set-Cookie']:
                cookie.update({'JSESSIONID':
                                   list_response.headers['Set-Cookie'].split(
                                       'JSESSIONID=')[1].split(';')[0]})
            logger.info(str(list_json))
            if list_json.get('errorCode', 0) in [2, '2']:
                logger.info('cookie is avaliable, need to login again:' + str(
                    list_json))

                if not list_json.get('message', ''):
                    result['code'] = 5
                    return result

                result['code'] = 6
                return result
            elif list_json.get('errorCode', 0) != 1:
                logger.info('did not get list success:' + list_response.text)
                result['code'] = 3
                return result
            result['code'] = 0
            result['json'] = list_json
            break

        except Exception as e:
            logger.exception('get exception when download list:' + str(e))
            result['code'] = 4

    return result


# 按关键字获取列表页
def get_list_from_keyword(cookie, page_numner, params, proxy=None, token=''):
    """
    args:
        cookie: 账号的cookie
        page_numner：要下载列表页的页数
        params：下载列表页的参数，职能、城市
        proxy：下载使用的代理
        token：cookie中的hrToken
    return：
        {'code':0, 'json': []}
        code为0：成功
        code为5：需要重新登录
        code非0：下载失败
    """
    time.sleep(3)
    logger = utils.get_logger()
    result = {'code': 0}
    # if not proxy:
    #     logger.info('there has no proxy!!!')
    #     result['code'] = 1
    #     return result
    logger.info('use proxy ' + str(proxy) + 'to download list')

    list_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/find_warehouse_by_position_new?timestamp=' + str(
        int(time.time() * 1000))
    list_data = {
        'pageSize': page_numner - 1,
        'pageNo': 25,
        'keyStr': params['positionName'].encode('utf8'),
        'companyName': '',
        'schoolName': '',
        'keyStrPostion': '',
        'postionStr': '',
        'startDegrees': -1,
        'endDegress': -1,
        'startAge': 0,
        'endAge': 35,
        'gender': -1,
        'region': '',
        'timeType': 1,
        'startWorkYear': -1,
        'endWorkYear': -1,
        'beginTime': '',
        'endTime': '',
        # -1 any, 0 free, 1 money
        'isMember': -1,
        'hopeAdressStr': int(params['hopeAdressStr']),
        # 'hopeAdressStr':2,
        # 'cityId': int(params['hopeAdressStr']),
        'cityId': -1,
        'updateTime': '',
        'tradeId': '',
        'clientNo': '',
        # 'userToken':login_result['cookie']['hrkeepToken'],
        'userToken': token,
        'clientType': 2,
    }
    # if int(params['hopeAdressStr']) not in [ 1, 5, 2, 3]:
    #         list_data['cityId'] = '-1'
    # cookie['zhaopingou_select_city'] = params['hopeAdressStr']

    referer_url = 'http://qiye.zhaopingou.com/resume?key='
    if page_numner not in [0, '0']:
        referer_url = 'http://qiye.zhaopingou.com/resume/free?key=%s&startAge=0&endAge=35&update_time=1&pn=%s' % (
            params['positionName'].encode('utf8'), str(page_numner - 1),)
    # cookie['']

    list_headers = {
        'Accept': 'multipart/form-data',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-type': 'application/x-www-form-urlencoded',
        'Host': 'qiye.zhaopingou.com',
        'Origin': 'http://qiye.zhaopingou.com',
        'Referer': referer_url,
        # 'Referer': 'http://qiye.zhaopingou.com/resume/free?key=Java&beginDegreesType=3&endDegreesType=100&startAge=20&endAge=30&update_time=1&pn=4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Cookie': '; '.join([i[0] + '=' + i[1] for i in cookie.items()])
    }
    for x in xrange(common_settings.DOWNLOAD_RETRY_TIME):
        try:
            list_response = requests.post(list_url, headers=list_headers,
                                          data=list_data,
                                          allow_redirects=False, proxies=proxy,
                                          timeout=30)

            if list_response.status_code not in [200, '200']:
                logger.warning('did not get 200 when download list:' + str(
                    list_response.status_code))
                result['code'] = 2
                return result
            list_json = list_response.json()
            if 'Set-Cookie' in list_response.headers and 'JSESSIONID=' in \
                    list_response.headers['Set-Cookie']:
                cookie.update({'JSESSIONID':
                                   list_response.headers['Set-Cookie'].split(
                                       'JSESSIONID=')[1].split(';')[0]})
            logger.info(str(list_json))
            if list_json.get('errorCode', 0) in [2, '2']:
                logger.warning(
                    'cookie is avaliable, need to login again:' + str(
                        list_json))
                result['code'] = 5
                return result
            elif list_json.get('errorCode', 0) != 1:
                logger.warning(
                    'did not get list success:' + list_response.text)
                result['code'] = 3
                return result
            result['code'] = 0
            result['json'] = list_json
            break

        except Exception as e:
            logger.exception('get exception when download list:' + str(e))
            result['code'] = 4

    return result


# 获取唤醒简历详情页
def get_resume(resume_id, token='', cookie={}, proxy=None):
    """
    args:
        resume_id：简历id
        token：cookie中的hrToken
        cookie：账号cookie
        proxy：代理
    result:
        {'code': 0, 'json': {}}
        code：0，成功；非0，失败
        json：详情页
    """
    time.sleep(1)
    logger = utils.get_logger()
    result = {'code': 0}
    # if not proxy:
    #    logger.info('did not get proxy when download resume!!!')
    #    result['code'] = 1
    #    return result
    resume_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/zpg_find_resume_html_details?timestamp=%s' % int(
        time.time() * 1000)
    logger.info('use proxy ' + str(proxy) + 'to download resume')
    resume_headers = {
        'Accept': 'multipart/form-data',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-type': 'application/x-www-form-urlencoded',
        'Host': 'qiye.zhaopingou.com',
        'Origin': 'http://qiye.zhaopingou.com',
        'Referer': 'http://qiye.zhaopingou.com/resume/detail?resumeId=%s' % resume_id,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        # 'Cookie': '; '.join([i+'='+login_result['cookie'][i] for i in login_result['cookie']]),
    }

    if cookie:
        resume_headers['Cookie'] = '; '.join(
            [i[0] + '=' + i[1] for i in cookie.items()])

    resume_data = {
        'resumeHtmlId': str(resume_id),
        'keyStr': '',
        'keyPositionName': '',
        'tradeId': '',
        'postionStr': '',
        'jobId': '0',
        'clientNo': '',
        'userToken': token,
        'clientType': '2',
        'companyName': '',
        'schoolName': '',
    }

    for i in xrange(common_settings.DOWNLOAD_RETRY_TIME):
        try:
            resume_response = requests.post(resume_url, headers=resume_headers,
                                            data=resume_data,
                                            allow_redirects=False,
                                            proxies=proxy, timeout=30)
            if resume_response.status_code not in [200, '200']:
                logger.info('did not get 200 when download resume:' + str(
                    resume_response.status_code))
                result['code'] = 2
                return result
            resume_json = resume_response.json()

            if resume_json['errorCode'] == 2:
                # 请稍后重试，别太急了
                logger.warning('did not get resume '
                               'success!!!' + resume_response.text)
                result['code'] = 3
                time.sleep(random.randrange(30, 60))
                return result

            if u'请您登录后查看简历' in resume_json['message']:
                result['code'] = 5
                logger.warning('帐号需要重新登录.')
                return result

            if resume_json['errorCode'] != 1:
                logger.warning('did not get resume '
                               'success!!!' + resume_response.text)
                result['code'] = 3
                return result

            # 进入简历详情成功后，随机sleep几秒
            time.sleep(random.randrange(10, 30))

            result['code'] = 0
            result['json'] = resume_json
            break
        except Exception as e:
            logger.exception('get exception when download resume:' + str(e))
            result['code'] = 4
            time.sleep(3)

    return result


# 处理一个唤醒任务
def awake_one_task(task):
    logger = utils.get_logger()
    logger.info('start aweak_thread')
    relogin_time = 3
    redis_client = get_redis_client()
    result = {'code': 0, 'executeParam': task}

    account, cookie, token, proxy, extra = get_one_account()

    logger.info(str(cookie) + str(token))
    logger.info('deal with:' + str(json.dumps(task, ensure_ascii=False)))

    page_now = 1
    download_day = str(time.localtime().tm_mon) + '-' + str(
        time.localtime().tm_mday)

    # 开始下载列表页
    while page_now != -1:
        logger.info('start download page:' + str(page_now))
        if not account:
            account, cookie, token, proxy, extra = get_one_account()

        if not extra:
            logger.warning('%s 该帐号未设置搜索上限。'
                           % account['username'].encode('utf-8'))
            result['code'] = 1
            return result

        logger.info('当前使用帐号为: %s' % account)
        # 根据task中的use_keyword参数选择关键字搜索还是只能搜索
        if task.get('use_keyword', '') == '1':
            list_result = get_list_from_keyword(cookie, page_now, task, proxy,
                                                token)
        else:
            list_result = get_list(cookie, page_now, task, proxy, token)
        # 列表页下载异常
        if list_result['code'] == 5:
            # set_unavaliable_account(account)
            account = None
            time.sleep(random.randint(1, 5))
            continue

        if list_result['code'] == 6:
            # set_unavaliable_account(account)
            logger.info('该任务搜索结果异常: %s'
                        % str(json.dumps(task, ensure_ascii=False)))
            result['code'] = 2
            return result

        elif list_result['code']:
            logger.info('get error list result:' + str(list_result))
            page_now = -1
            continue
        # 列表页下载成功
        logger.info('number of in this page is ' + str(len(
            list_result['json']['warehouseList'])) + ' all number is:' + str(
            list_result['json'].get('total', '')))
        # 若首页未搜出结果，打印日志
        if page_now == 1 and str(list_result['json'].get('total', '')) in ['',
                                                                           '0']:
            # {"fenleiName": "客服", "pFenLeiName": "销售 | 客服 | 售后", "positionName": "客户关系/投诉协调人员", "hopeAdressStr": "7", "fId": 63, "pFId": 6, "pId": 254, "id": 245}
            logger.info('not get resume in city:' + city_dict[
                int(task['hopeAdressStr'])] + ' function1:' + task[
                            'pFenLeiName'] + ' function2:' + str(
                task['fenleiName']) + ' function3:' + str(
                task['positionName']))
        # 逐个下载详情页
        for resume in list_result['json']['warehouseList']:
            if not account:
                account, cookie, token, proxy, extra = get_one_account()
            resume_key = 'zpg_resume_' + str(resume['resumeHtmlId'])
            try:
                resume_download_time = redis_client.get(resume_key)
                if resume_download_time == download_day:
                    # 在redis中检查今天是否已经下过唤醒详情页
                    logger.info('has find %s in redis' % resume_key)
                    continue
                else:
                    redis_client.set(resume_key, download_day)
                    logger.info('has find %s in redis, update' % resume_key)
            except Exception as e:
                redis_client.set(resume_key, download_day)
                logger.info('not find %s in redis' % resume_key)

            resume_result = get_resume(resume['resumeHtmlId'], token,
                                       cookie, proxy=proxy)

            if list_result['code'] == 5:
                # set_unavaliable_account(account)
                account = None
                time.sleep(random.randint(1, 5))
                continue

            if resume_result['code']:
                logger.info('get error resume:' + str(resume_result))
                continue

            if is_account_limited(account['username'].encode('utf-8'),
                                  int(extra['search_limit'])) is True:
                result['code'] = 1
                return result

            # 保存详情页到mns和mysql中
            resume_uuid = uuid.uuid1()
            try:
                sql = 'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values ("ZHAO_PIN_GOU", %s, "python", %s, now(), %s, %s, %s, %s)'
                sql_value = (
                    json.dumps(resume_result['json'], ensure_ascii=False),
                    resume_uuid, str(account['username']),
                    task['positionName'],
                    city_dict[int(task['hopeAdressStr'])],
                    str(resume['resumeHtmlId']))

                resume_update_list = resume_update_re.findall(
                    resume_result['json'].get('jsonHtml'))
                resume_update_time = '' if not resume_update_list else \
                    resume_update_list[0]

                kafka_data = {
                    "channelType": "WEB",
                    "content": {
                        "content": json.dumps(resume_result['json'],
                                              ensure_ascii=False),
                        "id": '',
                        "createBy": "python",
                        "createTime": int(time.time() * 1000),
                        "ip": '',
                        "resumeSubmitTime": '',
                        "resumeUpdateTime": resume_update_time,
                        "source": "ZHAO_PIN_GOU",
                        "trackId": str(resume_uuid),
                        "avatarUrl": '',
                        "email": str(account['username']),
                        'emailJobType': task['positionName'],
                        'emailCity': city_dict[int(task['hopeAdressStr'])],
                        'subject': str(resume['resumeHtmlId'])
                    },
                    "interfaceType": "PARSE",
                    "resourceDataType": "RAW",
                    "resourceType": "RESUME_SEARCH",
                    "source": "ZHAO_PIN_GOU",
                    "trackId": str(resume_uuid),
                    'traceID': str(resume_uuid),
                    'callSystemID': common_settings.CALLSYSTEMID,
                }
                utils.save_data(sql, sql_value, kafka_data)
            except Exception as e:
                logger.exception('get error when write mns, exit!!!' + str(e))
            time.sleep(1)

        page_now = -1 if page_now * 25 >= list_result['json'].get('total',
                                                                  0) else page_now + 1

    logger.info('has finish deal with:' + str(json.dumps(task,
                                                         ensure_ascii=False)))
    time.sleep(3)
    result['code'] = 0
    return result


# 唤醒线程入口， 该方法和调度交互，基本无需更改，每个任务的处理可直接更改awake_one_task方法
def awake_thread():
    logger = utils.get_logger()
    logger.info('process_thread start!!!')
    global stop_tag
    while not stop_tag:
        hour = datetime.datetime.now().hour
        if hour < 7 or hour >= 23:
            logger.info("当前程序不再执行时间段内， sleep...")
            time.sleep(600)
            continue

        task_traceid = str(uuid.uuid1())
        params = {'traceID': task_traceid,
                  'callSystemID': common_settings.CALLSYSTEMID,
                  'taskType': common_settings.TASK_TYPE,
                  'source': common_settings.SOURCE, 'limit': 1}
        param_str = '&'.join([str(i) + '=' + str(params[i]) for i in params])
        task_url = common_settings.TASK_URL + common_settings.GET_TASK_PATH + param_str
        # 从调度中获取一条任务
        task_result = utils.download(url=task_url, is_json=True)
        if task_result['code'] or task_result['json']['code'] not in [200,
                                                                      '200']:
            logger.info(
                'get error task, sleep... url is:' + task_url + ' return is:' + str(
                    task_result))
            time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        logger.info('get task!!!' + str(task_result))
        # 若返回成功，但没有任务，sleep后重新获取任务
        if not task_result['json']['data']:
            logger.info('did not get task_result data:' + str(task_result))
            push_task()
            time.sleep(120)
            # time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        process_result = {'code': -1,
                          'executeParam': task_result['json']['data'][0][
                              'executeParam']}
        # 处理任务
        try:
            process_result = awake_one_task(
                json.loads(task_result['json']['data'][0]['executeParam']))
        except Exception as e:
            logger.exception('error when process:' + str(e))
        # 返回任务
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
            logger.warning('get a failed return of task!!!')
        for x in xrange(3):
            try:
                logger.info('send return task time ' + str(x))
                return_task_result = utils.download(url=return_task_url,
                                                    is_json=True,
                                                    method='post',
                                                    data=return_data)
                # print return_task_result
                if not return_task_result['code'] and \
                        return_task_result['json']['code'] in [200,
                                                               '200']:
                    break
            except Exception as e:
                logger.exception('error when send return task:' + str(e))

        if process_result.get('code', True) and process_result.get(
                'executeParam', '') and process_result.get('code') != 2:
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
                        'executeParam': task_result['json']['data'][0][
                            'executeParam'],
                        'parentUuid': task_result['json']['data'][0]['uuid'],
                        # 'deadline': task_result['json']['data'][0]['deadline'],
                    }
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    }
                    insert_result = utils.download(url=insert_url,
                                                   is_json=True,
                                                   headers=headers,
                                                   method='post',
                                                   data=insert_data)
                    logger.info('insert result:' + str(insert_result))
                    if not insert_result['code'] and insert_result['json'][
                        'code'] in [200, '200']:
                        break
                except Exception as e:
                    logger.exception('error when create task:' + str(e))

                    # time.sleep(5)


# 购买一份简历
def charge_resume(resumeid, token, cookie, proxy):
    logger = utils.get_logger()
    logger.info('start to charge resume:' + str(resumeid))
    result = {'code': 0}

    try:

        for x in xrange(3):
            get_resume_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/zpg_find_resume_html_details?timestamp=%s' % str(
                int(time.time()))

            get_resume_header = {
                'Accept': 'multipart/form-data',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-type': 'application/x-www-form-urlencoded',
                'Host': 'qiye.zhaopingou.com',
                'Origin': 'http://qiye.zhaopingou.com',
                'Referer': 'http://qiye.zhaopingou.com/resume/detail?resumeId=%s' % resumeid,
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Cookie': '; '.join(
                    [i[0] + '=' + i[1] for i in cookie.items()]),
            }
            get_resume_data = {
                'resumeHtmlId': resumeid,
                'keyStr': '',
                'keyPositionName': '',
                'tradeId': '',
                'postionStr': '',
                'jobId': '0',
                'clientNo': '',
                'userToken': token,
                'clientType': '2',
                'companyName': '',
                'schoolName': '',
            }
            get_resume_response = requests.post(get_resume_url,
                                                headers=get_resume_header,
                                                data=get_resume_data,
                                                allow_redirects=False,
                                                proxies=proxy, timeout=30)

            # print get_resume_response.text
            if get_resume_response.status_code not in [200, '200']:
                logger.warning('did not get resume!!!' + str(resumeid))
                continue

            # 进入简历详情成功后，随机sleep几秒
            time.sleep(random.randrange(10, 30))

            # check_if_download_list = coin_number_re.findall(get_resume_response.content)
            # if not check_if_download_list:
            if u'请您登录后查看简历' in json.dumps(get_resume_response.json(),
                                          ensure_ascii=False):
                logger.info('0.1简历详情：%s' % json.dumps(
                    get_resume_response.content, ensure_ascii=False))
                result['code'] = 5
                result['data'] = get_resume_response.text
                result['json'] = get_resume_response.json()
                return result

            if u'如需联络方式' not in json.dumps(get_resume_response.json(),
                                           ensure_ascii=False):
                result['code'] = 0
                result['data'] = get_resume_response.text
                result['json'] = get_resume_response.json()
                return result
            # logger.info('0.1简历详情：%s' % json.dumps(
            #     get_resume_response.content, ensure_ascii=False))
            break
        else:
            logger.warning('did not get resume success:' + resumeid)
            result['code'] = 3
            return result

        for x in xrange(3):

            get_folder_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/get_candidate_folder_list?timestamp=%s' % str(
                int(time.time() * 1000))
            get_folder_header = {
                'Accept': 'multipart/form-data',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-type': 'application/x-www-form-urlencoded',
                'Host': 'qiye.zhaopingou.com',
                'Origin': 'http://qiye.zhaopingou.com',
                'Referer': 'http://qiye.zhaopingou.com/resume/detail?resumeId=%s' % resumeid,
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
                'Cookie': '; '.join(
                    [i[0] + '=' + i[1] for i in cookie.items()]),
            }
            get_folder_data = {
                'type': '1',
                'keyStr': '',
                'clientNo': '',
                'userToken': token,
                'clientType': '2',
            }
            get_folder_response = requests.post(get_folder_url,
                                                headers=get_folder_header,
                                                data=get_folder_data,
                                                proxies=proxy,
                                                allow_redirects=False,
                                                timeout=30)
            if get_folder_response.status_code not in [200, '200']:
                logger.info('not get folder success!!!')
                continue
            get_folder_json = get_folder_response.json()
            if get_folder_json.get('errorCode', -1) not in [1,
                                                            '1'] or not get_folder_json.get(
                'dataList', []):
                logger.info('get error folder:' + get_folder_response.text)
                continue
            folder_id = get_folder_json['dataList'][0]['id']
            # print 'folder_id', folder_id
            # break
            logger.info('获取folder_id成功： %s' % folder_id)

            charge_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/zpg_charge_example_unlock_new?timestamp=%s' % str(
                int(time.time() * 1000))
            charge_headers = {
                'Accept': 'multipart/form-data',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-type': 'application/x-www-form-urlencoded',
                'Host': 'qiye.zhaopingou.com',
                'Origin': 'http://qiye.zhaopingou.com',
                'Referer': 'http://qiye.zhaopingou.com/resume/detail?resumeId=%s' % resumeid,
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Cookie': '; '.join(
                    [i[0] + '=' + i[1] for i in cookie.items()]),
            }
            charge_data = {
                'htmlCode': resumeid,
                'mFolderId': folder_id,
                'notes': '',
                'clientNo': '',
                'userToken': token,
                'clientType': '2',
            }
            charge_response = requests.post(charge_url, headers=charge_headers,
                                            data=charge_data,
                                            allow_redirects=False,
                                            proxies=proxy, timeout=30)
            # print charge_response.text
            if charge_response.status_code not in [200, '200']:
                logger.warning('not get 200 when charge:' + str(resumeid))
                continue

            if charge_response.json().get('errorCode') != 1:
                if charge_response.json().get('errorCode') == 7:
                    logger.warning('charge failed %s'
                                   % charge_response.json().get(
                        'message').encode('utf-8'))
                    result['code'] = 7
                    return result

                logger.warning('charge failed %s'
                               % json.dumps(charge_response.content,
                                            ensure_ascii=False))
                time.sleep(random.randint(1, 5))
                continue

            logger.info('charge success: %s'
                        % json.dumps(charge_response.content,
                                     ensure_ascii=False))
            # 调用购买接口成功后，随机sleep几秒
            time.sleep(random.randrange(10, 30))
            break
        else:
            logger.warning('did not charge success:' + resumeid)
            result['code'] = 1
            return result

        for x in xrange(3):
            get_resume_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/zpg_find_resume_html_details?timestamp=%s' % str(
                int(time.time()))

            get_resume_header = {
                'Accept': 'multipart/form-data',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-type': 'application/x-www-form-urlencoded',
                'Host': 'qiye.zhaopingou.com',
                'Origin': 'http://qiye.zhaopingou.com',
                'Referer': 'http://qiye.zhaopingou.com/resume/detail?resumeId=%s' % resumeid,
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Cookie': '; '.join(
                    [i[0] + '=' + i[1] for i in cookie.items()]),
            }
            get_resume_data = {
                'resumeHtmlId': resumeid,
                'keyStr': '',
                'keyPositionName': '',
                'tradeId': '',
                'postionStr': '',
                'jobId': '0',
                'clientNo': '',
                'userToken': token,
                'clientType': '2',
                'companyName': '',
                'schoolName': '',
            }
            get_resume_response = requests.post(get_resume_url,
                                                headers=get_resume_header,
                                                data=get_resume_data,
                                                allow_redirects=False,
                                                proxies=proxy, timeout=30)
            if get_resume_response.status_code not in [200, '200']:
                logger.info('did not get resume!!!' + str(resumeid))
                continue
            # 进入简历详情成功后，随机sleep几秒
            time.sleep(random.randrange(10, 30))

            result['code'] = 0
            result['data'] = get_resume_response.text
            result['json'] = get_resume_response.json()
            logger.info('the length of resume text is:' + str(
                len(get_resume_response.text)))
            return result
        else:
            logger.warning('did not get resume success:' + resumeid)
            result['code'] = 2
        return result
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError, requests.exceptions.SSLError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.TooManyRedirects) as e:
        logger.exception('get timeout when charge resume! %s' % str(e))
        result['code'] = 5
        return result
    except Exception as e:
        logger.exception(
            'get error when charge resume:%s' % str(e))
        result['code'] = 4
        return result


# 获取账号当前下载点数
def get_coin_number(cookie, token, proxy):
    logger = utils.get_logger()
    logger.info('start to download user info.')

    for x in xrange(3):
        try:
            result = {'code': 0}
            get_coin_url = 'http://qiye.zhaopingou.com/zhaopingou_interface/user_information?timestamp=%s' % str(
                int(time.time() * 1000))
            get_coin_header = {
                'Accept': 'multipart/form-data',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Content-type': 'application/x-www-form-urlencoded',
                'Host': 'qiye.zhaopingou.com',
                'Origin': 'http://qiye.zhaopingou.com',
                'Referer': 'http://qiye.zhaopingou.com/resume',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Cookie': '; '.join(
                    [i[0] + '=' + i[1] for i in cookie.items()]),
            }
            get_coin_data = {
                'isAjax': '1',
                'clientNo': '',
                'userToken': token,
                'clientType': '2',
            }

            get_coin_response = requests.post(get_coin_url,
                                              headers=get_coin_header,
                                              data=get_coin_data,
                                              allow_redirects=False,
                                              proxies=proxy, timeout=30)
            if get_coin_response.status_code not in [200, '200']:
                logger.info('not get 200 when get coin.')
                continue
            get_coin_json = get_coin_response.json()
            if get_coin_json['errorCode'] in [10, '10']:
                logger.info('the account is not avaliable')
                result['code'] = 3
                return result
            elif get_coin_json['errorCode'] not in [1, '1']:
                logger.info(
                    'get error when get coin number:' + str(get_coin_json))
                result['code'] = 4
                return result
            result['code'] = 0
            # result['coin'] = get_coin_response.json()['memberEvents'].get(
            #     'free_count', 0)
            result['coin'] = get_coin_response.json()['account'].get(
                'free_count', 0)
            # result['dogfood'] = get_coin_response.json()['members'].get(
            #     'balance', 0)
            result['dogfood'] = get_coin_response.json()['account'].get(
                'balance', 0)
            return result
        except Exception as e:
            logger.exception(str(e))


    else:
        logger.warning('error when get_user_info.')
        result['code'] = 1
    return result


def init_download_task():
    global download_queue
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
    mysql_cursor.execute(
        'update download_record set valid=0 where valid=1 and source=17')
    mysql_conn.commit()
    mysql_conn.close()
    download_queue.clean()
    logger.info("初始化下载任务成功: %s" % download_queue.qsize())


def create_download_task():
    try:
        while True:
            if download_queue.empty():
                global download_task_time
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
                download_task_time = datetime2str(datetime.datetime.now())
                mysql_cursor.execute(
                    'select * from download_record where valid=0 and '
                    'source=17 order by updateTime desc limit 300')
                task_list = mysql_cursor.fetchall()
                if not task_list:
                    logger.info('没有更多的下载任务. sleep60s')
                    time.sleep(60)
                for task in task_list:
                    download_queue.put(task)
                logger.info("添加任务成功: %s" % download_queue.qsize())
                time.sleep(300)
                continue
    except Exception as e:
        logger.exception(str(e))


# 购买简历线程入口
def download_thread():
    logger = utils.get_logger()
    logger.info('=' * 50 + '\nstart main!!!')
    global numbers_left
    global buy_tag
    global coin_warning_dict
    global dogfood_warning_dict
    global download_queue
    global download_task_time

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

    # sqlite_conn = sqlite3.connect('zhaopingou.db')
    # sqlite_cursor = sqlite_conn.cursor()
    task_list = []
    # 检查今天已经下载了多少，同步到numbers_left变量中
    mysql_cursor.execute(
        'select count(*) from download_record where updateTime>date(now()) and valid=2 and source=17')
    number_today = mysql_cursor.fetchall()[0][0]
    numbers_left -= number_today
    numbers_left = 0 if numbers_left < 0 else numbers_left

    while True:
        # 22:00 - 8:00之间只sleep，不购买
        while not buy_tag:
            logger.info('not the correct time to buy resume, wait.')
            coin_warning_dict = {}
            dogfood_warning_dict = {}
            time.sleep(3600)
        if not numbers_left:
            logger.info('the number of today not left, sleep')
            time.sleep(1800)
            continue
        logger.info('the number left today is:' + str(numbers_left))
        # 从mysql中获取任务，根据updateTime排序，优先拿取更新时间最新的，若无任务则sleep

        while not task_list:
            while not buy_tag:
                logger.info('not the correct time to buy resume, wait.')
                time.sleep(3600)
            if download_queue.empty():
                logger.warning("没有更多的下载任务. sleep60s")
                time.sleep(60)
                continue

            # if not task_number:
            #     logger.info('there has no avaliable task in mysql ,sleep!!!')
            #     time.sleep(300)
            #     continue
            # task_list = list(mysql_cursor.fetchall())
            break
        task = eval(download_queue.get())
        logger.info("当前队列[%s]剩余任务%s个, 当前任务ID： %s"
                    % (download_task_time, download_queue.qsize(), task[0]))
        # task = task_list.pop()
        # 解析任务的地点、职位类型

        # exit()

        if task[8]:
            try:
                extend_content = json.loads(task[8])
                extend_content[
                    'emailJobType'] = '' if 'emailJobType' not in extend_content else \
                    extend_content['emailJobType']
                extend_content[
                    'emailCity'] = '' if 'emailCity' not in extend_content else \
                    extend_content['emailCity']
            except Exception as e:
                logger.exception('not find extend_content in task: %s %s' %
                                 (str(task), e))
                extend_content = {"emailJobType": "", "emailCity": ""}
        else:
            extend_content = {"emailJobType": "", "emailCity": ""}

        # 如果需要狗粮，则将任务valid置为4，并跳过该任务
        if extend_content.get('externalInfo', '0') in [1, '1', 'COLLECT']:
            logger.info('get a externalInfo=1 task')
            mysql_cursor.execute(
                'update download_record set valid=4 where id=%s' % str(
                    task[0]))
            mysql_conn.commit()
            continue

        # 随机获取一个账号
        account, cookie, token, proxy, extra = get_one_account(download=True)

        # 将任务状态更改为下载中
        mysql_cursor.execute(
            'update download_record set valid=1, downloadBy="%s" where id=%s' % (
                str(account['username']), str(task[0])))
        mysql_conn.commit()

        # 购买简历，若下载失败，默认账号有问题，重新登录账号
        charge_result = charge_resume(task[1], token, cookie, proxy)

        if charge_result['code'] == 7:
            time.sleep(random.randint(1, 5))
            mysql_cursor.execute(
                'update download_record set valid=5, downloadBy="%s" where '
                'id=%s' % (str(account['username']), str(task[0])))
            mysql_conn.commit()
            logger.warning('简历下载失败： 状态修改为，已达到求职者设定的查阅简历次数上限.')
            continue

        if charge_result['code'] == 5:
            set_unavaliable_account(account)
            time.sleep(random.randint(1, 5))
            mysql_cursor.execute(
                'update download_record set valid=0, downloadBy="%s" where '
                'id=%s' % (str(account['username']), str(task[0])))
            mysql_conn.commit()
            logger.warning('简历下载失败： 状态修改回未下载.')
            continue
        elif charge_result['code']:
            set_unavaliable_account(account)
            time.sleep(random.randint(1, 5))
            mysql_cursor.execute(
                'update download_record set valid=0, downloadBy="%s" where '
                'id=%s' % (str(account['username']), str(task[0])))
            mysql_conn.commit()
            logger.warning('简历下载失败： 状态修改回未下载.')
            continue

        # elif charge_result['code']:
        #     logger.info('get error when charge!!!'+str(charge_result))
        #     account_coin = 0
        #     break

        # 保存数据
        resume_uuid = uuid.uuid1()
        try:
            mysql_cursor.execute(
                u'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values ("ZHAO_PIN_GOU", %s, "python", %s, now(), %s, %s, %s, %s)',
                (json.dumps(charge_result['json'], ensure_ascii=False),
                 resume_uuid, account['username'],
                 extend_content['emailJobType'], extend_content['emailCity'],
                 task[1]))
            mysql_conn.commit()
            numbers_left -= 1
            mysql_cursor.execute('select last_insert_id()')
            save_mysql_ids = mysql_cursor.fetchall()
            if not save_mysql_ids or not save_mysql_ids[0]:
                logger.info('insert into mysql error!!!')
                raise Exception
            save_mysql_id = save_mysql_ids[0][0]
        except Exception as e:
            logger.exception(str(e))
            continue

        kafka_data = {
            "channelType": "WEB",
            "content": {
                "content": json.dumps(charge_result['json'],
                                      ensure_ascii=False),
                "id": save_mysql_id,
                "createBy": "python",
                "createTime": int(time.time() * 1000),
                "ip": '',
                "resumeSubmitTime": '',
                # "resumeUpdateTime": resume.get('refDate', ''),
                "resumeUpdateTime": '',
                "source": "ZHAO_PIN_GOU",
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
            "externalInfo": "BUY",
            "source": "ZHAO_PIN_GOU",
            "trackId": str(resume_uuid),
        }
        logger.info('the raw id is:' + str(kafka_data['content']['id']))
        try:
            buf = StringIO()
            f = gzip.GzipFile(mode='wb', fileobj=buf)
            f.write(json.dumps(kafka_data))
            f.close()
            msg_body = base64.b64encode(buf.getvalue())
            msg = Message(msg_body)
            for send_message_count in range(
                    common_settings.MNS_SAVE_RETRY_TIME):
                try:
                    mns_client = get_mns_client()
                    mns_client.send_message(msg)
                    break
                except Exception as e:
                    logger.exception('error when mns send message, time:' +
                                     str(send_message_count) + ':' + str(e))
            else:
                raise Exception
        except Exception as e:
            logger.exception('get error when produce mns, exit!!!' + str(e))
            send_dingding_text('zhaopingou resume: download thread return.')
            return 3
        try:
            mysql_cursor.execute(
                'update download_record set valid=2, downloadBy="%s" where id=%s' % (
                    str(account['username']), str(task[0])))
            mysql_conn.commit()
            # del task_list[index]
        except Exception as e:
            logger.exception(str(e))
            time.sleep(600)
            continue
        time.sleep(random.choice([2, 3, 4]))

        # 从页面获取剩余下载点数，并更新到account模块
        coin_number_result = get_coin_number(cookie, token, proxy)
        if not coin_number_result['code']:
            update_coin_number_left(account, coin_number_result['coin'])
            if not coin_warning_dict.get(account['username'], False) and \
                    coin_number_result['coin'] < 3000:
                coin_warning_dict[account['username']] = True
                send_dingding_text(u'招聘狗账号%s下载点数%s' % (
                    account['username'], coin_number_result['coin']))
            if not dogfood_warning_dict.get(account['username'], False) and \
                    coin_number_result['dogfood'] < 2000:
                dogfood_warning_dict[account['username']] = True
                send_dingding_text(u'招聘狗账号%s狗粮数%s' % (
                    account['username'], coin_number_result['dogfood']))

        else:
            logger.info('get unkown error:' + str(coin_number_result))

    logger.info('quit')
    mysql_cursor.close()
    mysql_conn.close()


# 测试方法，可在此测试各个方法，上线后此方法无用
# def test():
#     account = {'username': '292115_1', 'passwd': 'leads2017', 'id': 802}
#     set_unavaliable_account(account)


if __name__ == '__main__':

    # 初始化全局变量
    utils.set_setting(settings.project_settings)
    logger = utils.get_logger()
    logger.info('=' * 50 + 'start main')
    # test()

    global numbers_left
    numbers_left = common_settings.NUMBERS_ERVERYDAY

    # 创建并开启心跳线程，线程数一个
    change_time_thread_one = threading.Thread(target=change_time_thread,
                                              name="Change_Time_Thread")
    change_time_thread_one.start()

    # 创建并开启若干搜索唤醒线程，线程数从配置文件中如去
    search_number = common_settings.SEARCH_THREAD_NUMBER
    search_thread_list = []
    for x in xrange(search_number):
        search_thread = threading.Thread(target=awake_thread,
                                         name='Thread-' + str(x))
        search_thread.start()
        search_thread_list.append(search_thread)

    # 创建并开启购买简历线程，线程数一个
    download_number = common_settings.DOWNLOAD_THREAD_NUMBER
    download_thread_list = []

    # 初始化下载队列
    init_download_task()

    # 创建下载Producer
    dl_create_download_task = threading.Thread(target=create_download_task,
                                               name='Download_Producer')
    dl_create_download_task.start()

    # 创建下载Consumer
    for y in xrange(download_number):
        dl_thread = threading.Thread(target=download_thread,
                                     name='Download_Consumer-' + str(y))
        dl_thread.start()
        download_thread_list.append(dl_thread)

    # 等待各线程退出，理论上各线程并不会退出
    for i in search_thread_list:
        i.join()

    dl_create_download_task.join()

    for j in download_thread_list:
        j.join()

    change_time_thread_one.join()

    logger.info('done.')
