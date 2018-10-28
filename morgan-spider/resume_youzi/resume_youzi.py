#!coding:utf8
# 本程序共分四种线程，入口分别为以下四个方法，其他方法均被此四个方法调用
#
# get_download_task_thread（一个）：简历购买任务处理线程。主要流程：从数据库获取任务，并放到内存队列中，以供购买线程获取，因购买线程为多线程，所以添加此线程，避免多线程下载同一个任务
#
# download_thread（若干）：简历购买线程。主要流程：从spider库中的download_resume表中根据updateTime排序拿取最近的，valid为0的任务，并下载，下载完成，将valid置为2，并设置downloadBy参数为下载使用的账号，如果下载三次失败，则设置此任务的valid为3，以后不再下载
#
# awake_thread（若干）：简历搜索唤醒线程。主要流程：从调度拿取任务，搜索列表页，去重后拿取详情页，并推送mysql和mns进行唤醒
#
# change_time_thread（一个）：心跳线程，每次sleep一个小时，之后更改一次全局变量，如numbers_left（更新每天购买简历数上限）
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
from create_task import CreateTask
import re
import hashlib
from mf_utils.extend.dingding_robot import DingDingRobot

stop_tag = False
sleep_tag = True
get_task_queue = None
push_task_time = None
push_task_keyword_tag = '0'
push_task_lock = threading.Lock()
resumr_id_re = re.compile('seekerid=(\d+)')
random_ids = []

# 钉钉机器人，在send_dingding_text中被调用

# 调用此方法向钉钉群发送消息
dingding_robot = None
def send_dingding_text(text):
    global dingding_robot
    if not dingding_robot:
        dingding_robot = DingDingRobot('eb749abfe9080a69da6524b77f589b8f6ddbcc182c7a41bf095b095336edb0a1')
    dingding_robot.send_text(text)

# 调度中获取不到任务时，会调用此方法向调度推送新一轮的任务，两次任务之间的时间间隔至少28800秒
def push_task():
    logger = utils.get_logger()
    global push_task_time
    global push_task_lock
    global push_task_keyword_tag
    if push_task_lock.locked():
        return
    # 推送任务时加锁，确保每个时刻只有一个线程在推送任务
    push_task_lock.acquire()
    if not push_task_time or (datetime.datetime.now()-push_task_time).seconds>28800:
        send_dingding_text(u'开始推送柚子招聘简历任务.')
        runner = CreateTask()
        runner.create_task_from_mysql('1')
        push_task_time = datetime.datetime.now()
    push_task_lock.release()

# 从account模块随机获取一个账号，搜索唤醒和购买购汇用到此方法
def get_one_account(download=False):
    '''
    从account模块随机获取一个账号，若连续三次获取不到账号则sleep十分钟，直至获取到账号为止
    '''
    # return {'username': 'test130279237', 'passwd': 'jinqian4611', 'id': 805}, 'JSESSIONID=C418E9DA2B9FB1051BEE86F19076CE4D'
    logger = utils.get_logger()
    logger.info('start to get a search account.')
    if download:
        url = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'RESUME_INBOX')
    else:
        url = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'RESUME_FETCH')
    get_account_count = 3
    while True:
        try:
            response = requests.get(url, timeout=10)
            response_json = response.json()
            logger.info('get account response ' + str(response_json['code']))
            if response_json['code'] in [200, '200'] and response_json['data']:
                account = {'username': response_json['data']['userName'], 'passwd': response_json['data']['password'], 'id': response_json['data']['id'], 'downloadScore': response_json['data']['downloadScore'], 'freshScore': response_json['data']['freshScore']}
                cookie = response_json['data'].get('cookie', '')
                # cookie = json.loads(response_json['data']['cookie'])
                # if not cookie:
                #     logger.info('not get cookie in result, set to relogin and try again.')
                #     set_unavaliable_account(account)
                #     continue
                logger.info('using account:'+response.text)
                return account, cookie
        except Exception, e:
            logger.info('get error when get search account:'+str(traceback.format_exc()))
        if not get_account_count:
            send_dingding_text(u'柚子没有获取到账号')
            logger.info('not get account sleep...')
            time.sleep(600)
            get_account_count = 3
        else:
            get_account_count -= 1

# 从account模块获取一个账号，用于购买简历，若购买简历有downloadBy字段，则调用此方法，若根据downloadBy没有获取到账号，则随机获取一个账号，若还是无账号，sleep十分钟后重新获取，直至返回账号为止
def get_one_account_with_download_by(download_by, download=False):
    # return {'username': 'test130279237', 'passwd': 'jinqian4611', 'id': 805}, 'JSESSIONID=C418E9DA2B9FB1051BEE86F19076CE4D'
    '''
    根据download_by从account获取账号，若根据download_by未获取到账号，则随机返回一个账号 
    '''
    logger = utils.get_logger()
    logger.info('start to get a search account.')
    url = common_settings.ACCOUNT_WITH_USERNAME_URL % (common_settings.SOURCE, 'RESUME_INBOX', download_by)
    url_default = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'RESUME_INBOX')
    while True:
        try:
            # 根据download_by获取账号
            response = requests.get(url, timeout=10)
            response_json = response.json()
            if response_json['code'] in [200, '200'] and response_json['data']:
                account = {'username': response_json['data']['userName'], 'passwd': response_json['data']['password'], 'id': response_json['data']['id'], 'downloadScore': response_json['data']['downloadScore'], 'freshScore': response_json['data']['freshScore']}
                cookie = response_json['data'].get('cookie', '')
                if not cookie:
                    logger.info('not get cookie in result, set to relogin and try again.')
                    set_unavaliable_account(account)
                    continue
                logger.info('using account:'+response.text)
                return account, cookie
            else:
                # 随机获取一个账号
                response = requests.get(url_default, timeout=10)
                response_json = response.json()
                if response_json['code'] in [200, '200'] and response_json['data']:
                    account = {'username': response_json['data']['userName'], 'passwd': response_json['data']['password'], 'id': response_json['data']['id'], 'downloadScore': response_json['data']['downloadScore'], 'freshScore': response_json['data']['freshScore']}
                    cookie = response_json['data'].get('cookie', '')
                    if not cookie:
                        logger.info('not get cookie in result, set to relogin and try again.')
                        set_unavaliable_account(account)
                        continue
                    logger.info('using account:'+response.text)
                    return account, cookie
        except Exception, e:
            logger.info('get error when get search account:'+str(traceback.format_exc()))
        time.sleep(600)

# 设置账号cookie失效，重新登录
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

# 设置账号禁用
def set_forbidden_account(account):
    logger = utils.get_logger()
    logger.info('set forbidden :'+str(account))
    time.sleep(2)
    url = common_settings.SET_FORBIDDEN_URL % (account['username'], account['passwd'])
    try:
        # pass
        response = requests.get(url)
        send_dingding_text(u'柚子招聘账号异常:%s' % account['username'])
        logger.info('set forbidden account response:'+ response.text)
    except Exception, e:
        logger.info(str(traceback.format_exc()))

# 获取redis客户端
redis_client = None
def get_redis_client():
    global redis_client
    if not redis_client:
        # redis_pool = redis.ConnectionPool(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
        # redis_client = redis.Redis(redis_pool)
        redis_client = redis.Redis(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
    return redis_client

# 更新账号可用下载点数
def update_coin_number_left(account, coin_number):
    logger = utils.get_logger()
    logger.info('update coin number:'+str(account)+' '+str(coin_number))
    url = common_settings.UPDATE_DOWNLOAD_SCORE
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

# 获取mns客户端
def get_mns_client():
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY, common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client

# 心跳线程入口
def change_time_thread():
    logger = utils.get_logger()
    logger.info('start check time!!!')
    global stop_tag
    global numbers_left
    global sleep_tag
    start_day = datetime.datetime.now().day
    while not stop_tag:
        hour_now = datetime.datetime.now().hour
        if start_day != datetime.datetime.now().day:
            start_day = datetime.datetime.now().day
            numbers_left = common_settings.NUMBERS_ERVERYDAY
            logger.info('has change day, start_day is '+str(start_day))
        time.sleep(3600)

# 获取一个列表页
def get_list(random_id, page_numner, params, proxy=None):
    '''
    获取一个列表页
    args:
        random_id: 随机id，在account表中获取
        page_numner: 要获取的页数
        params: 参数，城市、职位，从调度任务中获取
        proxy: 使用的代理
    return:
        {'code': 0, 'data': [], 'has_next_page': False}
        code: 0, 成功; 非0, 失败
        data: 简历数据（简历id、简历更新时间）
        has_next_page: 是否有下一页
    '''
    logger = utils.get_logger()
    result = {'code': 0, 'data': [], 'has_next_page': False}
    logger.info('use proxy '+str(proxy) + ' to download list with keyword')

    try:
        list_url = 'http://www.youzijob.com/resumecenter/list'
        list_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/x-www-form-urlencoded',
            'Cookie': 'youziRecruiter=%s' % random_id,
            'Host':'www.youzijob.com',
            'Origin':'http://www.youzijob.com',
            'Referer':'http://www.youzijob.com/resumecenter/list',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        list_data = {
            'jobTitle': params['jobTitle'],
            'keyword':'',
            'locationid': params['locationid'],
            'companyName':'',
            'company':'0',
            'educationRecord':'0',
            'WorkingYearStart':'',
            'WorkingYearEnd':'',
            'companyType':'0',
            'seekerSex':'0',
            'searchId':'',
            'searchContents': u'+'.join([params['jobTitle'], params['locationname'], u'不限']),
            'searchType':'2',
            'num': str(page_numner),
            'listStatus':u'收起',
        }

        list_response = requests.post(list_url, headers=list_header, data=list_data, proxies=proxy, allow_redirects=False, timeout=30)
        # print cookie
        # if list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/login.jsp?errMsg=':
        #         logger.info('invalid cookie, need login.')
        #         result['code'] = 5
        #         return result
        # elif list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
        #     logger.info('list response status headers:'+str(list_response.headers))
        #     result['code'] = 6
        #     return result
        if list_response.status_code not in [200, '200']:
            logger.info('list response status code:'+str(list_response.status_code))
            result['code'] = 1
            return result
        list_root = etree.HTML(list_response.text)
        div_list = list_root.xpath('//div[@class="UListBoxC clearfix  UonlyLine"]')
        ids = []
        # 解析简历id与简历更新时间
        for div in div_list:
            child_div_list = div.xpath('./div')
            if len(child_div_list)!=9:
                continue
            resume_list = child_div_list[0].xpath('./a')
            resume_update_time = child_div_list[8].text
            if not resume_list or len(resume_update_time.split('.'))!=3:
                continue
            resume_id_list = resumr_id_re.findall(resume_list[0].attrib.get('href', ''))
            if not resume_id_list:
                continue

            ids.append([str(resume_id_list[0]), resume_update_time.strip()])
        result['data'] = ids
        # 检查是否有下一页
        if list_root.xpath('//input[@class="UnextPage Udisable"]'):
            result['has_next_page'] = False
        else:
            result['has_next_page'] = True
        return result
    except Exception, e:
        logger.info(str(traceback.format_exc()))
    result['code'] = 3
    return result

# 获取一个简历详情页
def get_resume(resume_id, random_id, proxy=None):
    '''
    获取一份唤醒的简历
    args:
        resume_id: 简历id
        random_id: 随机id，在account模块中作为账号获取
        proxy: 使用的代理
    result:
        {'code': 0, 'data': ''}
        code: 0，成功; 非0，失败
        data: 简历数据
    '''
    # time.sleep(1)
    logger = utils.get_logger()
    logger.info('use proxy '+str(proxy)+'to download resume')
    result = {'code': 0}

    try:
        # get resume info
        get_resume_url = 'http://www.youzijob.com/resumecenter/resumedetail?seekerid=%s' % resume_id
        get_resume_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie': 'youziRecruiter=%s' % random_id,
            'Host':'www.youzijob.com',
            'Referer':'http://www.youzijob.com/resumecenter/list',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        logger.info('start to get resume')
        get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30, proxies=proxy)
        if get_resume_response.status_code not in [200, '200']:
            logger.info('not get 200 when get resume response:'+str(get_resume_response.status_code))
            result['code'] = 4
            return result

        result['data'] = get_resume_response.text
        return result
    except Exception, e:
        logger.info('get error when download resume:'+str(traceback.format_exc()))
        result['code'] = 1
        return result

def awake_one_task(task):
    logger = utils.get_logger()
    logger.info('start aweak one task')
    global random_ids
    relogin_time = 3
    redis_client = get_redis_client()
    result = {'code': 0, 'executeParam':task}
    proxy = None
    if common_settings.USE_PROXY:
        proxy = settings.get_proxy()

    logger.info('deal with:'+str(task))

    page_now = 1
    download_day = str(time.localtime().tm_mon)+'-'+str(time.localtime().tm_mday)
    datetime_now = datetime.datetime.now()

    # 开始处理任务
    while page_now != -1:
        logger.info('start download page:'+str(page_now))
        # 每个列表页使用一个账号
        account, cookie = get_one_account()
        # 开始下载列表页
        list_result = get_list(account['username'], page_now, task, proxy)
        if list_result['code']:
            logger.info('get error list result:'+str(list_result))
            page_now = -1
            continue
        # 若列表页中没有简历，认为已经翻到最后一页
        if not list_result['data']:
            list_result['has_next_page'] = False
        logger.info('page number of now is '+str(page_now))

        # 逐个处理详情页
        for resume_one in list_result['data']:
            resume, resume_update_time = resume_one

            datetime_update = datetime.datetime.strptime(resume_update_time, '%Y.%m.%d')
            if (datetime_now - datetime_update).days> 7 :
                logger.info('get 1 days before resume, continue.'+resume_update_time)
                list_result['has_next_page'] = False
                continue

            # 在redis中检查今天是否已经下载过
            has_find_in_redis = False
            resume_key = 'youzi_resume_'+str(resume)
            try:
                resume_redis_value=redis_client.get(resume_key)
                if resume_redis_value == download_day:
                    has_find_in_redis = True
            except Exception, e:
                logger.info(str(traceback.format_exc()))
                # redis_client.set(resume_key, download_day)
            if has_find_in_redis:
                logger.info('has find %s in redis' % resume_key)
                continue
            else:
                logger.info('not find %s in redis' % resume_key)

            # 下载简历详情页，尝试三次，三次均下载失败，则跳过此简历
            for x in xrange(3):
                account, cookie = get_one_account()
                resume_result = get_resume(resume, account['username'], proxy=proxy)

                if resume_result['code']:
                    logger.info('get error resume:'+str(resume_result))
                    continue
                redis_client.set(resume_key, download_day)
                break
            else:
                continue

            # 保存简历详情页
            resume_uuid = uuid.uuid1()
            try:
                content = json.dumps({'name': '', 'email': '', 'phone': '', 'html':resume_result['data']}, ensure_ascii=False)
                sql = 'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values (%s, %s, "python", %s, now(), %s, %s, %s, %s)'
                sql_value = (common_settings.SOURCE, content, resume_uuid, str(account['username']), task['jobTitle'], task['locationname'], str(resume))

                resume_update_time = ''
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
                        'emailJobType': task['jobTitle'],
                        'emailCity': task['locationname'],
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
            time.sleep(1)

        # 最多翻200页
        page_now = page_now+1 if list_result['has_next_page'] and page_now<200 else -1

    logger.info('has finish deal with:'+str(task))
    time.sleep(3)
    result['code'] = 0
    return result

# 搜索唤醒线程入口，从调度获取任务，本方法基本无需更改，若要更改任务具体的处理流程，可以更改awake_one_task方法
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

# 购买一个简历
def charge_resume(resume_id, cookie, proxy=None):
    '''
    购买一份简历
    流程：获取简历详情、购买简历、获取简历详情
    args:
        resume_id: 简历id
        cookie: 账户cookie
        proxy: 使用的代理
    result:
        {'code': 0, data:''}
        code: 0, 成功; 1, 无需登录，失败; 其他, 需要登录，失败
        data: 购买后的简历详情页
    '''
    logger = utils.get_logger()
    logger.info('use proxy '+str(proxy)+'to download resume')
    result = {'code': 0}
    time.sleep(2)
    
    try:
        # 获取简历详情页，若含有‘已获取联系方式’，则说明已经下载过，无需再次下载，直接返回这个详情页即可
        timestamp = str(int(time.time()))
        s = "orderno=ZF20179226856N1V03P,secret=96268b5a90304b6f865cf95d4a1082fe,timestamp=" + timestamp
        md5_s = hashlib.md5(s).hexdigest()
        auth_s = "sign=" + md5_s.upper() + "&" + "orderno=ZF20179226856N1V03P&" + "timestamp=" + timestamp
        get_resume_url = 'http://www.youzijob.com/resumecenter/resumedetail?seekerid=%s' % resume_id
        get_resume_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie': cookie,
            'Host':'www.youzijob.com',
            'Referer':'http://www.youzijob.com/resumecenter/list',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Proxy-Authorization': auth_s,
        }
        logger.info('start to get resume')
        get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30, proxies=proxy, verify=False)
        if get_resume_response.status_code not in [200, '200']:
            logger.info('not get 200 when get resume response:'+str(get_resume_response.status_code))
            result['code'] = 1
            return result
        if u'已获取联系方式' in get_resume_response.text:
            result['code'] = 0
            result['data'] = get_resume_response.text
            return result
        get_resume_root = etree.HTML(get_resume_response.text)
        if get_resume_root.xpath('//div[@class="beforeLogin"]'):
            logger.info('account need login.')
            result['code'] = 4
            return result


        # 购买简历
        timestamp = str(int(time.time()))
        s = "orderno=ZF20179226856N1V03P,secret=96268b5a90304b6f865cf95d4a1082fe,timestamp=" + timestamp
        md5_s = hashlib.md5(s).hexdigest()
        auth_s = "sign=" + md5_s.upper() + "&" + "orderno=ZF20179226856N1V03P&" + "timestamp=" + timestamp
        charge_url = 'http://www.youzijob.com/file/getYouZiMobile?customerId=%s' % resume_id
        charge_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie': cookie,
            'Host':'www.youzijob.com',
            'Referer':'http://www.youzijob.com/resumecenter/resumedetail?seekerid=%s' % resume_id,
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Proxy-Authorization': auth_s,
        }

        logger.info('start to charge resume')
        charge_response = requests.get(charge_url, headers=charge_header, proxies=proxy, allow_redirects=False, verify=False, timeout=20)
        if charge_response.status_code not in [302, '302']:
            logger.info('charge failed!!!'+str(charge_response.status_code))
            result['code'] = 1
            return result

        # 购买成功后获取含有联系方式的简历
        timestamp = str(int(time.time()))
        s = "orderno=ZF20179226856N1V03P,secret=96268b5a90304b6f865cf95d4a1082fe,timestamp=" + timestamp
        md5_s = hashlib.md5(s).hexdigest()
        auth_s = "sign=" + md5_s.upper() + "&" + "orderno=ZF20179226856N1V03P&" + "timestamp=" + timestamp
        get_resume_url = 'http://www.youzijob.com/resumecenter/resumedetail?seekerid=%s' % resume_id
        get_resume_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie':cookie,
            'Host':'www.youzijob.com',
            'Referer':'http://www.youzijob.com/resumecenter/resumedetail?seekerid=%s' % resume_id,
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'Proxy-Authorization': auth_s,
        }
        logger.info('start to get resume with contact.')
        get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30, proxies=proxy, verify=False)
        if get_resume_response.status_code not in [200, '200']:
            logger.info('not get 200 when get resume response:'+str(get_resume_response.status_code))
            result['code'] = 1
            return result
        result['data'] = get_resume_response.text
        return result

    except Exception, e:
        logger.info('get error when download resume:'+str(traceback.format_exc()))
        result['code'] = 1
        return result

# 分派购买任务线程入口
def get_download_task_thread():
    logger = utils.get_logger()
    global get_task_queue

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

    # 每次程序重启，需要将之前下载中的任务（valid=1）重置为未下载（valid=0）
    mysql_cursor.execute('update download_record set valid=0 where valid=1 and source=24')
    mysql_conn.commit()

    # 当任务队列中的剩余任务少于一半时，从数据库中获取任务，设置valid=1，添加到内存队列中
    # 若任务队列中任务数大于一半，sleep一分钟
    while True:
        task_len = get_task_queue.qsize()
        if task_len < common_settings.QUEUE_MAX_SIZE/2:
            tasks_number = mysql_cursor.execute('select * from download_record where valid=0 and source=24 order by updateTime desc limit '+str(common_settings.QUEUE_MAX_SIZE/2))
            tasks = mysql_cursor.fetchall()
            for i in tasks:
                get_task_queue.put(i)
                mysql_cursor.execute('update download_record set valid=1 where id='+str(i[0]))
            mysql_conn.commit()
            logger.info('has put %s task to queue' % len(tasks))
        else:
            logger.info('the length of task queue is:'+ str(task_len))
            time.sleep(60)

# 从页面获取账号可用下载点数
def get_coin_number(cookie, proxy):
    '''
    从页面获取账号可用下载点数
    args:
        cookie: 使用的账号cookie
        proxy: 使用的代理
    return:
        {'code': 0, 'coin':0}
        code: 0, 成功; 非0，失败
        coin: 可用下载点数
    '''
    logger = utils.get_logger()
    logger.info('start to download user info.')
    result = {'code': 0}

    try:
        timestamp = str(int(time.time()))
        s = "orderno=ZF20179226856N1V03P,secret=96268b5a90304b6f865cf95d4a1082fe,timestamp=" + timestamp
        md5_s = hashlib.md5(s).hexdigest()
        auth_s = "sign=" + md5_s.upper() + "&" + "orderno=ZF20179226856N1V03P&" + "timestamp=" + timestamp
        get_coin_url = 'http://www.youzijob.com/file/youZiCount?_=' + str(int(time.time()*1000))
        get_coin_header = {
            'Accept':'text/plain, */*; q=0.01',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie':cookie,
            'Host':'www.youzijob.com',
            'Referer':'http://www.youzijob.com/resumecenter/resumedetail?seekerid=14462636',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'X-Requested-With':'XMLHttpRequest',
            'Proxy-Authorization': auth_s,
        }
        get_coin_response = requests.get(get_coin_url, headers=get_coin_header, allow_redirects=False, proxies=proxy, timeout=20)
        if get_coin_response.status_code not in [200, '200']:
            logger.info('not get 200 when get coin.')
            result['code'] = 2
            return result
        get_coin_json = get_coin_response.json()
        
        result['code'] = 0
        result['coin'] = int(get_coin_response.text)
        return result
    except Exception, e:
        result['code'] = 1
        logger.info(str(traceback.format_exc()))

    return result

# 购买简历入口
def download_thread():
    logger = utils.get_logger()
    logger.info('='*50+'\nstart main!!!')
    global numbers_left
    global sleep_tag
    global get_task_queue

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
    # proxy = {'http': 'http://HD1W5PS9852Y078D:88659F653E98575E@proxy.abuyun.com:9020', 'https': 'http://HD1W5PS9852Y078D:88659F653E98575E@proxy.abuyun.com:9020'}
    proxy = None
    if common_settings.USE_PROXY:
        proxy = settings.get_proxy()
    task_list = []
    mysql_cursor.execute('select count(*) from download_record where updateTime>date(now()) and valid=2 and source=24')
    number_today = mysql_cursor.fetchall()[0][0]
    numbers_left = 0 if numbers_left<number_today else numbers_left - number_today

    # 开始处理任务
    while True:
        task = None
        # 若当前时间不能下载简历，则sleep（此功能目前只在招聘狗上使用，此处暂未使用，sleep_tag会在心跳线程中被更改）
        while not sleep_tag:
            logger.info('not the correct time to buy resume, wait.')
            time.sleep(3600)
        # 若今日简历下载数已达今日上限， 则sleep
        if not numbers_left:
            logger.info('the number of today not left, sleep')
            time.sleep(1800)
            continue
        logger.info('the number left today is:'+str(numbers_left))
        # 从内存队列中获取任务，若没有获取到，sleep一分钟
        try:
            task = get_task_queue.get(timeout=10)
            if not task:
                logger.info('get None task, sleep!')
                time.sleep(600)
                continue
        except Exception, e:
            logger.info('not get task from queue, sleep.')
            time.sleep(60)
            continue

        # 解析任务中的城市、职位信息
        if task[8]:
            try:
                extend_content = json.loads(task[8])
                extend_content['emailJobType'] = '' if 'emailJobType'  not in extend_content else extend_content['emailJobType']
                extend_content['emailCity'] = '' if 'emailCity'  not in extend_content else extend_content['emailCity']
            except Exception, e:
                logger.info('not find extend_content in task:'+str(task))
                extend_content = {"emailJobType":"","emailCity":""}
        else:
            extend_content = {"emailJobType":"","emailCity":""}


        logger.info('start to deal with task:'+task[1])
        # download

        # 购买简历，购买一次失败，认为简历有问题，将valid置为3
        for charge_count in xrange(1):
            if task[6]:
                account, cookie = get_one_account_with_download_by(task[6])
            else:
                account, cookie = get_one_account(download=True)
            charge_result = charge_resume(task[1], cookie, proxy)
            if charge_result['code'] == 1:
                #set_unavaliable_account(account)
                continue
            elif charge_result['code']:
                set_unavaliable_account(account)
                continue
            break
        else:
            logger.info('get error after 1 times try to charge resume')
            try:
                mysql_cursor.execute('update download_record set valid=3 where id=%s' %  str(task[0]))
                mysql_conn.commit()
                logger.info('get 3 null text of resume:'+task[1])
            except Exception, e:
                logger.info(str(traceback.format_exc()))
            continue

        # 保存简历数据
        resume_uuid = uuid.uuid1()
        try:
            content = {'html':charge_result['data']}
            content = json.dumps(content, ensure_ascii=False)
            mysql_cursor.execute(u'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values (%s, %s, "python", %s, now(), %s, %s, %s, %s)' , (common_settings.SOURCE, content, resume_uuid, account['username'], extend_content['emailJobType'], extend_content['emailCity'],  task[1]))
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

        kafka_data = {
            "channelType": "WEB",
            "content": {
                "content": content,
                "id": save_mysql_id,
                "createBy": "python",
                "createTime": int(time.time()*1000),
                "ip": '',
                "resumeSubmitTime": '',
                # "resumeUpdateTime": resume.get('refDate', ''),
                "resumeUpdateTime": '',
                "source": common_settings.SOURCE,
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
            "source": common_settings.SOURCE,
            "trackId": str(resume_uuid),
        }
        logger.info('the raw id is:'+str(kafka_data['content']['id']))
        try:
            buf = StringIO()
            f = gzip.GzipFile(mode='wb', fileobj=buf)
            f.write(json.dumps(kafka_data))
            f.close()
            msg_body = base64.b64encode(buf.getvalue())
            msg = Message(msg_body)
            push_mns_error_tag = False
            for send_message_count in range(common_settings.MNS_SAVE_RETRY_TIME):
                try:
                    mns_client = get_mns_client()
                    mns_client.send_message(msg)
                    break
                except Exception, e:
                   logger.info('error when mns send message, time:'+str(send_message_count)+':'+str(e))
                   if 'The length of message should not be larger than MaximumMessageSize.' == e.message:
                        logger.info('resume too long to push to mns:'+task[1])
                        try:
                            mysql_cursor.execute('update download_record set valid=3, downloadBy="%s" where id=%s' % (str(account['username']), str(task[0])))
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
            logger.info('get error when produce mns, exit!!!'+str(traceback.format_exc()))
            send_dingding_text('youzi resume: download thread return.')
            return 3
        try:
            mysql_cursor.execute('update download_record set valid=2, downloadBy="%s" where id=%s' % (str(account['username']), str(task[0])))
            mysql_conn.commit()
            # del task_list[index]
        except Exception, e:
            logger.info(str(traceback.format_exc()))
            time.sleep(600)
            continue
        #time.sleep(2)

        # 检查剩余可用下载点数，并更新至数据库
        coin_number_result = get_coin_number(cookie, proxy)
        if not coin_number_result['code']:
            update_coin_number_left(account, coin_number_result['coin'])
            if coin_number_result['coin'] < 10:
                logger.info('the coin number of account:'+str(account) + ' is less than 10')
        else:
            logger.info('get unkown error:'+ str(coin_number_result))

    logger.info('quit')
    mysql_cursor.close()
    mysql_conn.close()

def test():
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
    cookie = 'customerUUID=ML%10%12%15G%40LYC%11BCY%40%11A%12Y%16A%16DY%12GAAL%15D%16%15C%10%11; JSESSIONID=257E52796BB0BCF375FFB84CEF30F209; youziRecruiter=B%40AM'
    task = {'jobTitle': u'Java', 'locationid': '594', 'locationname': u'北京'}
    print get_coin_number(cookie, None)
    # a = get_list(cookie, 1, task, None)
    # a=  get_resume('14087715', 'AADC')
    # a = get_resume_has_real_rid('2567308023', '117659691', cookie)
    # a = charge_resume('14087715', cookie)
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

    search_number = common_settings.SEARCH_THREAD_NUMBER

    search_thread_list = []
    # for x in xrange(search_number):
    #    search_thread = threading.Thread(target=awake_thread, name='Thread-'+str(x))
    #    search_thread.start()
    #    search_thread_list.append(search_thread)

    get_download_task_one = threading.Thread(target=get_download_task_thread, name="Get_Download_Task_Thread")
    get_download_task_one.start()

    download_thread_list = []
    for x in xrange(common_settings.DOWNLOAD_THREAD_NUMBER):
        download_thread_one = threading.Thread(target=download_thread, name='Download_Thread-'+str(x))
        download_thread_one.start()
        download_thread_list.append(download_thread_one)

    for i in download_thread_list:
        i.join()
    get_download_task_one.join()

    for i in search_thread_list:
        i.join()
    change_time_thread_one.join()

    logger.info('done.')
