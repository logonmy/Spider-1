#!coding:utf8
# 本程序共两种线程，入口函数分别为awake_thread和buy_thread，
#
# awake_thread：唤醒线程。处理流程：从调度获取任务，下载列表页，从redis去重简历，下载详情页，推送mysql和mns唤醒
#
# buy_thread：购买线程。处理流程：从redis获取可用账号，从spider下的downkoad_record表中获取任务，拿取账号下载简历，下载失败三次，将该简历valid置为3，以后不再下载；下载成功，将任务valid置为2，推送mns和mysql，并将简历id写入resume_download表
#

import sys

sys.path.append('../common')
import requests
import json
import time
import settings
import util
import datetime
import re
import MySQLdb
import traceback
import uuid
import random
import threading
from DBUtils.PersistentDB import PersistentDB
import urllib
from mns.account import Account
from mns.queue import Message
import gzip
from cStringIO import StringIO
import base64
import redis
import common_settings
import utils
import create_task

stop_tag = False
uid_re = re.compile('buid=([^&]+)&')
# 去除emoji表情的正则表达式
emoji_pattern = re.compile(
    u"(\ud83d[\ude00-\ude4f])|(\ud83c[\udf00-\uffff])|(\ud83d[\u0000-\uddff])|(\ud83d[\ude80-\udeff])|(\ud83c[\udde0-\uddff])+",
    flags=re.UNICODE)
redis_account_lock = threading.Lock()
redis_account = []
citys_dict = {
    '34,398': u'北京',
    '36,400': u'上海',
    '23,264': u'武汉',
    '27,312': u'成都',
    '35,399': u'天津',
    '25,291': u'广州',
    '25,292': u'深圳',
    '11,111': u'石家庄',
    '16,178': u'扬州',
    '11,115': u'邢台',
    '11,121': u'衡水',
    '11,116': u'保定',
    '11,119': u'沧州',
    '16,179': u'镇江',
    '16,176': u'淮安',
    '16,180': u'泰州',
    '16,169': u'南京',
    '13,134': u'大连',
    '25,296': u'佛山',
    '13,133': u'沈阳',
    '17,182': u'杭州',
    '21,231': u'青岛',
    '37,401': u'重庆',
    '21,230': u'济南',
    '30,358': u'西安',
    '25,308': u'中山',
    '19,211': u'厦门',
    '25,307': u'东莞',
    '18,193': u'合肥',
    u'南京': '16,169',
    u'淮安': '16,176',
    u'泰州': '16,180',
    u'镇江': '16,179',
    u'邢台': '11,115',
    u'衡水': '11,121',
    u'保定': '11,116',
    u'沧州': '11,119',
    u'扬州': '16,178',
    u'石家庄': '11,111',
    u'北京': '34,398',
    u'上海': '36,400',
    u'武汉': '23,264',
    u'成都': '27,312',
    u'天津': '35,399',
    u'广州': '25,291',
    u'深圳': '25,292',
    u'大连': '13,134',
    u'佛山': '25,296',
    u'沈阳': '13,133',
    u'杭州': '17,182',
    u'青岛': '21,231',
    u'重庆': '37,401',
    u'济南': '21,230',
    u'西安': '30,358',
    u'中山': '25,308',
    u'厦门': '19,211',
    u'东莞': '25,307',
    u'合肥': '18,193',
}
push_task_time = None
push_task_keyword_tag = '0'
push_task_lock = threading.Lock()


# 钉钉机器人，在send_dingding_text中被调用
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


# 调用该方法向钉钉发送消息
dingding_robot = None


def send_dingding_text(text):
    global dingding_robot
    if not dingding_robot:
        dingding_robot = DingDingRobot('eb749abfe9080a69da6524b77f589b8f6ddbcc182c7a41bf095b095336edb0a1')
    dingding_robot.send_text(text)


# 推送新一轮任务
def push_task():
    '''
    若调度中拿取不到任务，调用此方法重新推送任务
    通过线程锁控制每个时刻只有一个线程在推送任务
    每14400秒内只推送一轮
    中华英才任务不分职能任务和关键字任务
    '''
    logger = utils.get_logger()
    global push_task_time
    global push_task_lock
    global push_task_keyword_tag
    if push_task_lock.locked():
        return
    push_task_lock.acquire()
    if not push_task_time or (datetime.datetime.now() -
                                  push_task_time).seconds > 3600:
        send_dingding_text(u'开始推送中华英才简历任务.')
        logger.info('开始推送中华英才简历任务.')
        create_task.create_task_from_mysql()
        push_task_time = datetime.datetime.now()
    push_task_lock.release()


# 从account模块获取唤醒账号
def get_one_account_from_api(source_type='RESUME_INBOX'):
    '''
    从account模块获取一个随机的唤醒搜索的账号（此处source_type使用RESUME_INBOX）
    return:
        {'code':0, 'cookie':{}, 'device_id': '', 'username': '', 'passwd':'', 'uid':''}
        code: 0，成功；非0，失败
        cookie: 账号cookie
        device_id: 账号绑定的device_id
        username: 账号的username
        passwd: 账号的passwd
        uid: 账号的uid，从cookie中匹配
    '''
    logger = utils.get_logger()
    logger.info('get one account from api.')
    get_account_url = common_settings.ACCOUNT_URL % ('CH_HR', source_type)
    cookie_result = {'code': 0, 'cookie': []}
    proxy = None
    try:
        logger.info('start to get cookie:' + get_account_url)
        cookie_response = requests.get(url=get_account_url, timeout=10)
        logger.info(cookie_response.text)
        cookie_json = cookie_response.json()
        cookie = json.loads(cookie_json.get('data', {}).get('cookie') or '{}')

        cookie_result['cookie'] = cookie
        cookie_result['device_id'] = json.loads(cookie_json['data'].get('extraContent', '{}')).get('device_id')
        cookie_result['passwd'] = cookie_json['data'].get('password', '')
        cookie_result['username'] = cookie_json['data'].get('userName', '')
        if not cookie:
            logger.info('get error cookie!!!' + str(cookie_json))
            set_account_invalid(cookie_result['username'], cookie_result['passwd'])
            cookie_result['code'] = 3
            return cookie_result
        uid_list = uid_re.findall(cookie.get('bps', ''))
        if not uid_list or not cookie_result['device_id']:
            raise Exception
        cookie_result['uid'] = uid_list[0]
    except Exception, e:
        logger.info('get error when download cookie_result:' + str(traceback.format_exc()))
        cookie_result['code'] = 2
    return cookie_result


# 设置账号cookie失效，重新登录
def set_account_invalid(username, passwd):
    logger = utils.get_logger()
    logger.info('set_account_invalid:' + username)
    invalid_url = common_settings.SET_INVALID_URL % (username, passwd, common_settings.SOURCE)
    try:
        requests.get(invalid_url, timeout=10)
    except Exception, e:
        logger.info('get error when set account ' + username + ' invalid:' + str(traceback.format_exc()))


# 设置账号禁用
def set_account_forbidden(username, passwd):
    logger = utils.get_logger()
    logger.info('set_account_forbidden:' + username)
    forbidden_url = common_settings.SET_FORBIDDEN_URL % (username, passwd, common_settings.SOURCE)
    send_dingding_text(u'CH_HR app resume 账号异常：' + username)
    try:
        requests.get(forbidden_url, timeout=10)
    except Exception, e:
        logger.info('get error when set account ' + username + ' forbidden:' + str(traceback.format_exc()))


# 获取mns客户端
def get_mns_client():
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY,
                          common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client
    # global mns_client
    # if not mns_client:
    #     mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY, common_settings.TOKEN)
    #     mns_client = mns_account.get_topic(setcommon_settingtings.MNS_TOPIC)
    # return mns_client


# 获取redis客户端
redis_client = None


def get_redis_client():
    global redis_client
    if not redis_client:
        # redis_pool = redis.ConnectionPool(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
        # redis_client = redis.Redis(redis_pool)
        redis_client = redis.Redis(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
    return redis_client


# 获取购买简历的账号成都cookie，在get_account_from_redis中被调用
def get_cookie(username, source_type='RESUME_INBOX'):
    logger = utils.get_logger()
    logger.info('get url fo get_account!')
    get_account_url = common_settings.ACCOUNT_URL % ('CH_HR', source_type) + '&userName=' + username
    cookie_result = {'code': 0, 'cookie': {}}
    proxy = {}
    try:
        logger.info('start to get cookie:' + get_account_url)
        cookie_response = requests.get(url=get_account_url, timeout=10)
        cookie_json = cookie_response.json()
        cookie = json.loads(cookie_json.get('data', {}).get('cookie', '{}'))
        if not cookie:
            logger.info('get error cookie!!!' + str(cookie_json))
            cookie_result['code'] = 3
            return cookie_result
        cookie_result['cookie'] = cookie
        cookie_result['device_id'] = json.loads(cookie_json['data'].get('extraContent', '{}')).get('device_id')
        cookie_result['passwd'] = cookie_json['data'].get('password', '')
        uid_list = uid_re.findall(cookie.get('bps', ''))
        if not uid_list or not cookie_result['device_id']:
            raise Exception
        cookie_result['uid'] = uid_list[0]
    except Exception, e:
        logger.info('get error when download cookie_result:' + str(traceback.format_exc()))
        cookie_result['code'] = 2
    return cookie_result


# awake_thread中被调用
def awake_one_task(task):
    logger = utils.get_logger()
    global citys_dict, emoji_pattern
    has_find_count = 0
    not_find_count = 0
    redis_client = get_redis_client()
    kafka_client = None
    kafka_producer = None
    mns_client = None
    result = {'code': 0}
    user_now = {}
    logger.info('start to get data ' + str(task))
    mysql_error_time = 10
    list_page = int(task.get('page_now', 0))
    # 开始处理任务
    while list_page > 0:
        try:
            # 获取账号，若获取不到账号则sleep，直到可以拿到账号为止
            while not user_now:
                user_now = get_one_account_from_api()
                if not user_now['code']:
                    break
                else:
                    logger.info('get account failed:' + str(user_now))
                    user_now = {}
        except Exception, e:
            logger.info(str(traceback.format_exc()))
            continue

        time.sleep(1)
        # 开始下载列表页
        download_day_str = str(time.localtime().tm_year) + '-' + str(time.localtime().tm_mon) + '-' + str(
            time.localtime().tm_mday)
        download_day = datetime.datetime.today()
        while list_page >= 0:
            list_result = util.get_list(user_now, task, settings.get_proxy(), list_page)
            if list_result['code'] == 1:
                logger.info('get 800 code, to change accounts!!!')
                user_now = []
                break
            elif list_result['code'] == 3:
                logger.info('get 100 code, to change accounts!!!')
                set_account_invalid(user_now['username'], user_now['passwd'])
                user_now = []
                break
            elif list_result['code']:
                logger.info('get error list ,continue!!!' + str(list_result))
                user_now = {}
                break
            logger.info('has get the list of' + str(list_page))
            resume_list = list_result.get('data', {}).get('cvList', [])

            if len(resume_list) == 0 and list_page == 1:
                logger.info('not get resume in city:' + task['zone'] + ' keyword:' + task['keyword'])

            # 循环列表页中的详情页
            for resume in resume_list:
                resume_key = 'chinahr_resume_' + resume.get('cvid', '')
                # 在redis中检查RESUME_DELAY_DAYS天内是不是已经下载过了
                try:
                    resume_download_time = redis_client.get(resume_key)
                    if resume_download_time:
                        datetime_last_download = datetime.datetime.strptime(resume_download_time, '%Y-%m-%d')
                        if (download_day - datetime_last_download).days <= common_settings.RESUME_DELAY_DAYS:
                            logger.info('has find %s in redis' % (
                                resume_key,) + ' and the city is:' + task['zone'])
                            has_find_count += 1
                            continue
                        else:
                            redis_client.set(resume_key, download_day_str)
                            logger.info('has find %s in redis, update ' % (
                                resume_key,) + ' and the city is:' + task[
                                            'zone'])
                    else:
                        redis_client.set(resume_key, download_day_str)
                        logger.info('not find %s in reids' % (
                            resume_key,) + ' and the city is:' + task['zone'])
                except Exception as e:
                    logger.exception('get error when use redis.' + str(e))
                    # redis_client.set(resume_key, download_day_str)
                    raise e

                # 开始下载唤醒详情页
                time.sleep(1)
                resume_result = util.get_resume(user_now, str(resume.get('cvid', '')), settings.get_proxy())
                # 保存详情页到mns和mysql
                if resume_result['code'] in [0, '0']:
                    resume_uuid = uuid.uuid1()
                    try:
                        content = json.dumps(resume_result, ensure_ascii=False)
                        content = emoji_pattern.sub(r'', content)
                        sql = 'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity) values ("CH_HR", %s, "python", %s, now(), %s, %s, %s)'
                        sql_value = (content, resume_uuid, user_now['username'], task['keyword'], task['zone'])

                        kafka_data = {
                            "channelType": "APP",
                            "content": {
                                "content": content,
                                "createBy": "python",
                                "createTime": int(time.time() * 1000),
                                "ip": '',
                                "resumeSubmitTime": '',
                                "resumeUpdateTime": resume.get('refDate', ''),
                                "source": "CH_HR",
                                "trackId": str(resume_uuid),
                                "avatarUrl": '',
                                "email": user_now['username'],
                                'emailJobType': task['keyword'],
                                'emailCity': task['zone'],
                            },
                            "interfaceType": "PARSE",
                            "resourceDataType": "RAW",
                            "resourceType": "RESUME_SEARCH",
                            "source": "CH_HR",
                            "trackId": str(resume_uuid),
                            "callSystemID": common_settings.PROJECT_NAME,
                            "traceID": str(resume_uuid),
                        }
                        utils.save_data(sql, sql_value, kafka_data)
                        logger.info('the cvid is:' + resume.get('cvid', '') + ' the lenght of data is:' + str(
                            len(kafka_data['content']['content'])))
                    except Exception, e:
                        logger.info('mysql error ' + str(mysql_error_time) + ' time:' + str(traceback.format_exc()))
                        mysql_error_time -= 1
                        if not mysql_error_time:
                            # return
                            logger.info('there has no mysql_error_time')
                        continue
                elif resume_result['code'] == 6:
                    user_now = {}
                    # list_page = -1
                    break
                elif resume_result['code'] == 8:
                    set_account_invalid(account['username'], account['passwd'])
                    user_now = {}
                    # list_page = -1
                    break
                elif resume_result['code'] == 9:
                    set_account_invalid(account['username'], account['passwd'])
                    user_now = {}
                    # list_page = -1
                    break
                elif resume_result['code'] == 10:
                    user_now = {}
                    # list_page = -1
                    break
                else:
                    user_now = {}
                    break
                not_find_count += 1
            # time.sleep(2)
            if list_result.get('data', {}).get('hasNextPage', False):
                list_page += 1
                # i_dict['page_now'] += 1
            else:
                list_page = -1
            time.sleep(1)
        logger.info('list_page:%d' % list_page)
        time.sleep(1)
    logger.info('task:' + str(task) + 'has find:' + str(has_find_count) + ' not find:' + str(not_find_count))
    return result


# 唤醒线程入口方法，从调度中获取任务，本方法基本不用更改，具体任务处理流程请参考awake_one_task
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
            time.sleep(600)
            # time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        logger.info('get task!!!' + str(task_result))
        if not task_result['json']['data']:
            logger.info('did not get task_result data:' + str(task_result))
            push_task()
            time.sleep(120)
            # time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        process_result = {'code': -1, 'executeParam': task_result['json']['data'][0]['executeParam']}
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
        return_data['executeResult'] = process_result.get('executeResult', '')
        if not process_result.get('code', True):
            return_data['executeStatus'] = 'SUCCESS'
        else:
            return_data['executeStatus'] = 'FAILURE'
            logger.info('get a failed return of task!!!')
        for x in xrange(3):
            try:
                logger.info('send return task time ' + str(x))
                return_task_result = utils.download(url=return_task_url, is_json=True, method='post', data=return_data)
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
                        'executeParam': process_result.get('executeParam', ''),
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

        time.sleep(5)


# 获取购买简历的账号
def get_account_from_redis():
    logger = utils.get_logger()
    global redis_account
    redis_client = get_redis_client()
    result = {}
    redis_account_lock.acquire()
    while not redis_account:
        redis_account = redis_client.keys(time.strftime("%Y-%m-%d") + '_*_chinahr_0')
        logger.info('redis account' + str(redis_account))
        if not redis_account:
            time.sleep(180)
    account_key = redis_account.pop()
    account_key_list = account_key.split('_')
    account_number = redis_client.get(account_key)
    account_key_set = '_'.join(account_key_list[:-1]) + '_1'
    try:
        redis_client.rename(account_key, account_key_set)
    except Exception as e:
        logger.exception('%s : %s' % (account_key, e))
        pass
    redis_account_lock.release()
    cookie = get_cookie(account_key_list[1])
    result.update(cookie)
    result['username'] = account_key_list[1]
    result['account_key'] = account_key_set
    result['number'] = int(account_number)
    return result


# 购买的账号使用后从redis中释放账号
def release_account_from_redis(account_key, number=0):
    logger = utils.get_logger()
    redis_client = get_redis_client()
    redis_account_lock.acquire()
    if number < 1:
        redis_client.delete(account_key)
    else:
        redis_client.set(account_key, number)
        account_key_list = account_key.split('_')
        account_key_set = '_'.join(account_key_list[:-1]) + '_0'
        redis_client.rename(account_key, account_key_set)
    redis_account_lock.release()


# 购买简历的入口函数
def buy_thread():
    logger = utils.get_logger()
    logger.info('====================================================\nstart buy thread!!!')
    global emoji_pattern
    kafka_producer = None
    mns_client = None
    redis_client = None

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

    mysql_cursor.execute('update download_record set valid=0 where valid=1 and source=6')
    mysql_conn.commit()
    # proxy = {'http': 'http://HD1W5PS9852Y078D:88659F653E98575E@proxy.abuyun.com:9020', 'https': 'http://HD1W5PS9852Y078D:88659F653E98575E@proxy.abuyun.com:9020'}
    proxy = settings.get_proxy()

    task_list = []

    while True:
        try:
            while not task_list:
                task_number = mysql_cursor.execute(
                    'select * from download_record where valid=0 and source=6 order by updateTime desc limit 30')
                if not task_number:
                    logger.info('there has no avaliable task in mysql ,sleep!!!')
                    time.sleep(600)
                    mysql_conn = mysql_pool.connection()
                    mysql_cursor = mysql_conn.cursor()
                    continue
                task_list = list(mysql_cursor.fetchall())
                break
            task = task_list.pop()
            if task[8]:
                try:
                    extend_content = json.loads(task[8])
                    extend_content['emailJobType'] = '' if 'emailJobType' not in extend_content else extend_content[
                        'emailJobType']
                    extend_content['emailCity'] = '' if 'emailCity' not in extend_content else extend_content[
                        'emailCity']
                except Exception, e:
                    logger.info('not find extend_content in task:' + str(task))
                    extend_content = {"emailJobType": "", "emailCity": ""}
            else:
                extend_content = {"emailJobType": "", "emailCity": ""}

            get_null_text = 3
            for i in xrange(get_null_text):
                get_account_tag = True
                while get_account_tag:
                    account = get_account_from_redis()
                    if account['code']:
                        logger.info('get error account:' + str(account))
                        continue
                    cookie = account['cookie']
                    uid = account['uid']
                    device_id = account['device_id']
                    get_download_bean_result = util.get_download_beans(cookie, uid, proxy, device_id)
                    if not get_download_bean_result['code'] and not get_download_bean_result['coin_number']:
                        logger.info('get a account whos bean number is 0:' + account['username'] + ' result:' + str(
                            get_download_bean_result))
                        release_account_from_redis(account['account_key'], 0)
                    else:
                        get_account_tag = False

                resume_result = util.buy_resume(cookie, uid, str(task[1]), settings.get_proxy(), device_id)
                if resume_result['code'] in [0, '0']:
                    resume_uuid = uuid.uuid1()
                    try:
                        content = json.dumps(resume_result, ensure_ascii=False)
                        content = emoji_pattern.sub(r'', content)
                        mysql_cursor.execute(
                            u'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity) values ("CH_HR", %s, "python", %s, now(), %s, %s, %s)',
                            (content, resume_uuid, account['username'], extend_content['emailJobType'],
                             extend_content['emailCity']))
                        mysql_conn.commit()
                        mysql_cursor.execute('select last_insert_id()')
                        save_mysql_ids = mysql_cursor.fetchall()
                        if not save_mysql_ids or not save_mysql_ids[0]:
                            logger.info('insert into mysql error!!!:' + sql + '    ' + str(sql_value))
                            raise Exception
                        save_mysql_id = save_mysql_ids[0][0]
                    except Exception, e:
                        logger.info('mysql error:' + str(traceback.format_exc()))
                        time.sleep(60)
                        continue

                    kafka_data = {
                        "channelType": "APP",
                        "content": {
                            "content": content,
                            "id": save_mysql_id,
                            "createBy": "python",
                            "createTime": int(time.time() * 1000),
                            "ip": '',
                            "resumeSubmitTime": '',
                            "resumeUpdateTime": '',
                            "source": "CH_HR",
                            "trackId": str(resume_uuid),
                            "avatarUrl": '',
                            "email": account['username'],
                            'emailJobType': extend_content['emailJobType'],
                            'emailCity': extend_content['emailCity'],
                        },
                        "interfaceType": "PARSE",
                        "resourceDataType": "RAW",
                        "resourceType": "RESUME_INBOX",
                        "externalInfo": "BUY",
                        "source": "CH_HR",
                        "trackId": str(resume_uuid),
                    }
                    if common_settings.SAVE_TYPE:
                        try:
                            if common_settings.SAVE_TYPE == 'kafka':
                                kafka_producer.produce(json.dumps(kafka_data))
                            elif common_settings.SAVE_TYPE == 'mns':
                                buf = StringIO()
                                f = gzip.GzipFile(mode='wb', fileobj=buf)
                                f.write(json.dumps(kafka_data))
                                f.close()
                                msg_body = base64.b64encode(buf.getvalue())
                                msg = Message(msg_body)
                                for send_message_count in range(common_settings.MNS_SAVE_RETRY_TIME):
                                    try:
                                        mns_client = get_mns_client()
                                        mns_client.send_message(msg)
                                        break
                                    except Exception, e:
                                        logger.info(
                                            'error when mns send message, time:' + str(send_message_count) + ':' + str(
                                                e))
                                else:
                                    raise Exception
                            else:
                                logger.info('did not support save type:' + common_settings.SAVE_TYPE)
                        except Exception, e:
                            logger.info(
                                'get error when produce data to ' + common_settings.SAVE_TYPE + ', exit!!!' + str(
                                    traceback.format_exc()))
                    else:
                        logger.info('msg_queue maybe down, not save to kafka!!!')
                    mysql_cursor.execute('update download_record set valid=2, downloadBy=%s where id=%s',
                                         (account['username'], task[0]))
                    mysql_conn.commit()
                    logger.info('the cvid is:' + task[1])
                    logger.info('the raw id is:' + str(save_mysql_id) + ' and the city is:' + task[1])
                    mysql_cursor.execute('select count(*) from resume_download where resume_id="%s"' % task[1])
                    cvid_number = mysql_cursor.fetchall()
                    if cvid_number[0] and cvid_number[0][0] == 0:
                        mysql_cursor.execute(
                            'insert into resume_download (resume_id, source, mobile, account_mobile) values(%s, 6, %s, %s)',
                            (task[1], resume_result.get('data', {}).get('mobile', ''), account['username']))
                        mysql_conn.commit()
                        logger.info('has add %s to resume_download' % task[1])
                    else:
                        # logger.info('not add %s into resume_download' % task[1])
                        logger.info('not add %s into resume_download %s' % (task[1], str(cvid_number)))

                    release_account_from_redis(account['account_key'], account['number'] - 1)
                    break
                elif resume_result['code'] in [6, ]:
                    set_account_forbidden(account['username'], account['passwd'])
                    release_account_from_redis(account['account_key'], 0)
                elif resume_result['code'] in [8, 9, 10]:
                    release_account_from_redis(account['account_key'], 0)
                elif resume_result['code'] in [7, ]:
                    logger.info('cannot download resume %s with account %s' % (str(task[1]), account['username']))
                    release_account_from_redis(account['account_key'], 0)
                    # task_list.append(task)
                    # time.sleep(5)
                elif resume_result['code'] in [12, ]:
                    logger.info('cannot download resume %s with account %s' % (str(task[1]), account['username']))
                elif resume_result['code'] in [11, ]:
                    set_account_invalid(account['username'], account['passwd'])
                    release_account_from_redis(account['account_key'], 0)
                elif resume_result['code'] in [13, ]:
                    logger.info(u'get 暂时没有可用于下载此城市简历的点数,请选择其它简历下载 when use account %s to download %s' % (
                        account['username'], str(task[1])))
                    # set_account_invalid(account['username'], account['passwd'])
                    # release_account_from_redis(account['account_key'], 0)
                else:
                    release_account_from_redis(account['account_key'], 0)
            else:
                logger.info('get error when buy 3 times of resume:' + str(task[1]))
                mysql_cursor.execute('update download_record set valid=3 where id=%s', (task[0],))
                mysql_conn.commit()
        except Exception as e:
            logger.exception(e)
            continue

    logger.info('quit')
    mysql_cursor.close()
    mysql_conn.close()


# def test():
#     cookie = {'bps': 'buid=21553717031426', 'blt': '196327490886', 'blts': 'ca466f676ff792f3b8f', 'bst': '194551490886',
#               'bsts': 'a8bf09e630b3df80065', 'deviceID': '355340903541582'}
#     uid = '21553717031426'
#     proxy = None
#     device_id = '355340903541582'
#     print util.get_download_beans(cookie, uid, proxy, device_id)


if __name__ == '__main__':
    utils.set_setting(settings.project_settings)
    logger = utils.get_logger()
    global stop_tag
    # test()

    buy_resume_thread = threading.Thread(target=buy_thread, name='Buy_Thread')
    buy_resume_thread.start()

    awake_threads = []
    for x in xrange(common_settings.DOWNLOAD_THREAD_NUMBER):
        new_thread = threading.Thread(target=awake_thread, name='Thread-' + str(x))
        new_thread.start()
        awake_threads.append(new_thread)
        time.sleep(3)

    for i in awake_threads:
        i.join()

    stop_tag = True
    buy_resume_thread.join()
