#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25
import hashlib
import re
import sys
import redis

reload(sys)
sys.setdefaultencoding('utf8')

import pykafka
from pykafka import KafkaClient
import logging
import requests
import common_settings
from logging.handlers import RotatingFileHandler
import traceback
import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import json
import time
import ConfigParser
from mns.account import Account
from mns.queue import Message
import gzip
from cStringIO import StringIO
import base64
import uuid

# 日志文件默认名称为std.log，如果渠道设置了project_name变量，会使用相应的值作为日志文件名
project_name = 'std'

redis_pool = None
emoji_pattern = re.compile(
    u"(\ud83d[\ude00-\ude4f])|(\ud83c[\udf00-\uffff])|(\ud83d[\u0000-\uddff])|(\ud83d[\ude80-\udeff])|(\ud83c[\udde0-\uddff])+",
    flags=re.UNICODE)


# 初始化函数
def set_setting(params):
    '''
    初始化全局变量，默认使用/data/config/morgan/morgan_spider_common_settings.cfg文件中的参数，优先使用params中传入的参数，设置之后，其他模块秩序导入common_settings模块即可使用其中的参数
    '''
    global project_name
    global redis_pool
    # 设置默认参数
    cfg = ConfigParser.ConfigParser()
    cfg.read('/data/config/morgan/morgan_spider_common_settings.cfg')
    common_settings.__setattr__('MYSQL_HOST', cfg.get('db', 'MYSQL_HOST'))
    common_settings.__setattr__('MYSQL_PORT', cfg.getint('db', 'MYSQL_PORT'))
    common_settings.__setattr__('MYSQL_USER', cfg.get('db', 'MYSQL_USER'))
    common_settings.__setattr__('MYSQL_PASSWD', cfg.get('db', 'MYSQL_PASSWD'))
    common_settings.__setattr__('MYSQL_DB', cfg.get('db', 'MYSQL_DB'))
    common_settings.__setattr__('KAFKA_HOSTS', cfg.get('kafka', 'KAFKA_HOSTS'))
    common_settings.__setattr__('KAFKA_TOPIC', cfg.get('kafka', 'KAFKA_TOPIC'))
    common_settings.__setattr__('TASK_URL', cfg.get('task', 'TASK_URL'))
    common_settings.__setattr__('GET_TASK_PATH', cfg.get('task', 'GET_TASK_PATH'))
    common_settings.__setattr__('CREATE_TASK_PATH', cfg.get('task', 'CREATE_TASK_PATH'))
    common_settings.__setattr__('RETURN_TASK_PATH', cfg.get('task', 'RETURN_TASK_PATH'))
    common_settings.__setattr__('PROXY_URL', cfg.get('other', 'PROXY_URL'))
    common_settings.__setattr__('ACCOUNT_URL', cfg.get('other', 'ACCOUNT_URL'))
    common_settings.__setattr__('SERVER_SLEEP_TIME', cfg.getint('other', 'SERVER_SLEEP_TIME'))
    common_settings.__setattr__('REDIS_IP', cfg.get('other', 'REDIS_IP'))
    common_settings.__setattr__('REDIS_PORT', cfg.getint('other', 'REDIS_PORT'))
    common_settings.__setattr__('SAVE_TYPE', cfg.get('other', 'SAVE_TYPE'))
    common_settings.__setattr__('ACCID', cfg.get('mns', 'ACCID'))
    common_settings.__setattr__('ACCKEY', cfg.get('mns', 'ACCKEY'))
    common_settings.__setattr__('ENDPOINT', cfg.get('mns', 'ENDPOINT'))
    common_settings.__setattr__('TOKEN', cfg.get('mns', 'TOKEN'))
    common_settings.__setattr__('MNS_QUEUE', cfg.get('mns', 'MNS_QUEUE'))
    common_settings.__setattr__('SET_INVALID_URL', cfg.get('other', 'SET_INVALID_URL'))
    common_settings.__setattr__('AWAKE_URL', cfg.get('other', 'AWAKE_URL'))
    common_settings.__setattr__('PROJECT_NAME', project_name)

    # 设置params中的优先参数
    for i in params:
        common_settings.__setattr__(i, params[i])
    project_name = common_settings.PROJECT_NAME
    redis_pool = redis.ConnectionPool(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT)


# get logger
logger = None


def get_logger():
    global logger
    global project_name
    if not logger:
        logger = logging.getLogger('')
        formatter = logging.Formatter(
            fmt="%(asctime)s %(filename)s %(threadName)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        stream_handler = logging.StreamHandler()

        rotating_handler = logging.handlers.TimedRotatingFileHandler(
            '/data/logs/morgan-spider/' + project_name + '.log', 'midnight', 1)

        stream_handler.setFormatter(formatter)
        rotating_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(rotating_handler)
        logger.setLevel(logging.INFO)
    return logger


def redis_get(key):
    global redis_pool
    m = hashlib.md5()
    m.update(key)
    key_md5 = m.hexdigest()
    redis_ = redis.Redis(connection_pool=redis_pool)
    return redis_.get(key_md5)


def redis_delete(key):
    """
    :param key:
    :return: 1: 删除成功 , 0: key不存在 or删除失败
    """
    global redis_pool
    m = hashlib.md5()
    m.update(key)
    key_md5 = m.hexdigest()
    redis_ = redis.Redis(connection_pool=redis_pool)
    return redis_.delete(key_md5)


def redis_set(key, value):
    global redis_pool
    m = hashlib.md5()
    m.update(key)
    key_md5 = m.hexdigest()
    redis_ = redis.Redis(connection_pool=redis_pool)
    return redis_.set(key_md5, value, 3600 * 24)


def redis_incr(key, value=1):
    global redis_pool
    m = hashlib.md5()
    m.update(key)
    key_md5 = m.hexdigest()
    redis_ = redis.Redis(connection_pool=redis_pool)
    return redis_.incr(key_md5, value)


# 获取kafka客户端（现已改用mns，所以此方法已经不会用到）
kafka_client = None
kafka_producer = None


def get_kafka_client():
    global kafka_client, kafka_producer
    if not kafka_client or not kafka_producer:
        kafka_client = KafkaClient(common_settings.KAFKA_HOSTS)
        kafka_producer = kafka_client.topics[common_settings.KAFKA_TOPIC].get_sync_producer()
    return kafka_producer


def reset_kafka():
    global kafka_client, kafka_producer
    kafka_client = None
    kafka_producer = None


# 获取mns客户端
mns_client = None


def get_mns_client():
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY,
                          common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client


# 获取mysql客户端
mysql_pool = None


def get_mysql_client():
    global mysql_pool
    if not mysql_pool:
        mysql_pool = PersistentDB(MySQLdb, host=common_settings.MYSQL_HOST, user=common_settings.MYSQL_USER,
                                  passwd=common_settings.MYSQL_PASSWD, db=common_settings.MYSQL_DB,
                                  port=common_settings.MYSQL_PORT, charset='utf8')
    conn = mysql_pool.connection()
    cur = conn.cursor()
    return conn, cur


def query_by_sql(sql):
    conn, cur = get_mysql_client()
    try:
        results = cur.execute(sql)
        if results:
            result = cur.fetchall()
            get_logger().info('query success %s' % sql)
            return result
    except Exception as e:
        get_logger().error('query database error %s', sql)
        return None


def update_by_sql(sql):
    conn, cur = get_mysql_client()
    try:
        cur.execute(sql)
        conn.commit()
        get_logger().info('update_ success %s' % sql)
    except Exception as e:
        get_logger().error('update_ database error %s:%s', sql, e.message)
        return None


# 下载一个url，公共方法，可被任意模块调用
def download(session=None, url=None, headers=None, data='', method='get', cookie=None, proxy=None, is_json=False,
             encoding=None, retry_time=1, need_session=False, allow_redirects=False, verify=True, timeout=10):
    '''
    args:
        session: 下载使用的session，如果没有传，默认使用requests
        url: 下载的url
        headers: 下载使用的headers，可以不传入，有默认headers
        data: 下载为post时，post的data数据，字符串类型或dict类型
        method: 下载方法，目前只支持get、post，字符串类型
        cookie: 下载使用的cookie，和headers中的相比，优先使用这里的cookie
        proxy: 下载使用的代理
        is_json: 若返回结果是json格式，是否需要返回json.loads的结果
        encoding: 返回结果的编码方式
        retry_time: 下载重试次数
        need_session: 是否要返回下载的session，默认不需要
        allow_redirects: 是否允许重定向，默认不允许
        verify: 是否需要验证，用于代理，默认设置成True，如果使用讯代理或其他不需要验证的代理，需要传入False
        timeout: 下载超时时间，默认10秒钟
    return:
        {'code': 0, 'data': '', 'json': {}, 'headers': {}, 'session': session}
        code: 0，成功；非0，失败
        data: 下载的源码数据
        json: 如果设置is_json为True，此处返回json.loads之后的结果
        headers: response的headers信息
        session: 如果设置need_session为True，此处返回下载使用的session
    '''
    logger = get_logger()
    for x in xrange(retry_time):
        return_result = {'code': 0, 'json': {}}
        if not url or len(url.split('/')) < 3:
            return_result['code'] = 1
            logger.info('download error, not get url!!!')
            return return_result
        session_download = session or requests
        logger.info('use proxy:' + str(proxy) + ' to download:' + url)
        # 若headers为None，使用默认headers
        if type(headers) != type({}):
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Host': url.split('/')[2],
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            }

        # 优先使用参数中传入的cookie
        if cookie:
            headers['Cookie'] = cookie

        try:
            # 开始下载
            response = {}
            if method.lower() == 'post':
                response = session_download.post(url, headers=headers, data=data, allow_redirects=allow_redirects,
                                                 proxies=proxy,
                                                 timeout=timeout, verify=verify)
            else:
                response = session_download.get(url, headers=headers, allow_redirects=allow_redirects, proxies=proxy,
                                                timeout=timeout, verify=verify)

            if response.status_code not in [200, '200']:
                logger.info('download error, not get 200!!! %s' % (response.status_code,))
                return_result['code'] = 2
            if encoding:
                response.encoding = encoding
            return_result['data'] = response.text
            if is_json and not return_result['code']:
                return_result['json'] = response.json()
            return_result['headers'] = response.headers
            if need_session:
                return_result['session'] = session_download
            break
        # 检验超时
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.ProxyError,
                requests.exceptions.SSLError, requests.exceptions.ConnectTimeout,
                requests.exceptions.TooManyRedirects), e:
            logger.error('requests error when download ' + url + ' !!!' + str(traceback.format_exc()))
            return_result['code'] = 4
        except Exception, e:
            logger.info('unkown error when download ' + url + ' !!!' + str(traceback.format_exc()))
            return_result['code'] = 3
    return return_result


def get_account(username=None):
    logger = get_logger()
    logger.info('get_account start!!!')
    account_url = common_settings.ACCOUNT_URL % (common_settings.SOURCE, 'LOGIN')
    if username:
        account_url = account_url + '&userName=' + str(username)
    account_result = download(url=account_url, is_json=True)
    while account_result['code'] or account_result['json'].get('code', '') not in [200, '200']:
        logger.info('get error when get_account!!!' + str(account_result))
        time.sleep(10)

    return account_result['json']['data']


def login():
    pass


def get_proxy(get_proxy_url=None):
    '''
    从代理模块随机获取一个代理
    '''
    session = requests.session()
    for x in xrange(3):
        get_proxy_url = get_proxy_url or common_settings.PROXY_URL
        content = session.get(get_proxy_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
        }, proxies=None, timeout=10).content
        if content:
            # print content
            data = json.loads(content)
            ip = data['data']['ip']
            port = data['data']['port']
            return {'http': 'http://%s:%s' % (ip, port), 'https': 'http://%s:%s' % (ip, port)}
        else:
            get_logger().info('proxy request return null')
    return None


# 保存数据
def save_data(sql, sql_value, kafka_data):
    '''
    将下载到的数据保存到mysql、kafka、mns，现在只支持mns和mysql
    args:
        sql: 需要保存到mysql中的数据的sql语句
        sql_value: 需要保存到mysql中数据的value，与sql做对应
        kafka_data: 需要保存到mns中的json数据
    return:
        False: 保存失败
        True: 保存成功
    '''
    logger = get_logger()
    traceID = uuid.uuid4()
    kafka_data['traceID'] = str(traceID)
    logger.info(" %s traceID [%s] 准备推送消息队列 " % (common_settings.PROJECT_NAME, str(traceID)))
    kafka_data['callSystemID'] = common_settings.PROJECT_NAME
    logger.info('saving data...')
    global emoji_pattern
    conn, cur = get_mysql_client()
    msg_queue_client = None
    if common_settings.SAVE_TYPE == 'kafka':
        msg_queue_client = get_kafka_client()
    elif common_settings.SAVE_TYPE == 'mns':
        msg_queue_client = get_mns_client()
    else:
        pass

    try:
        # 去除emoji表情字符
        sql = emoji_pattern.sub(r'', sql)
        sql_value = tuple(
            [emoji_pattern.sub(r'', i) if type(i) in (type(str), type(unicode)) else i for i in sql_value])
        cur.execute(sql, sql_value)
        # save_mysql_id = int(conn.insert_id())
        conn.commit()
        cur.execute('select last_insert_id()')
        save_mysql_ids = cur.fetchall()
        if not save_mysql_ids or not save_mysql_ids[0]:
            logger.info('INSERT INTO mysql ERROR!!!:' + sql + '    ' + str(sql_value))
            return False
        save_mysql_id = save_mysql_ids[0][0]
        logger.info('入库成功 %s' % save_mysql_id)
        # 将保存到mysql中的数据id写入kafka——data
        kafka_data['content']['id'] = save_mysql_id
        dumps = json.dumps(kafka_data, ensure_ascii=False).encode('utf8')
        # 将保存到mns中的数据去除emoji表情
        dumps = emoji_pattern.sub(r'', dumps)
        try:
            if common_settings.SAVE_TYPE == 'kafka':
                msg_queue_client.produce(dumps)
            elif common_settings.SAVE_TYPE == 'mns':
                buf = StringIO()
                f = gzip.GzipFile(mode='wb', fileobj=buf)
                f.write(dumps)
                f.close()
                msg_body = base64.b64encode(buf.getvalue())
                msg = Message(msg_body)
                msg_queue_client.send_message(msg)
            else:
                logger.info('did not support save type:' + common_settings.SAVE_TYPE)
            logger.info('推送' + common_settings.SAVE_TYPE + '完毕  ' + str(kafka_data['content']['id']))
        except pykafka.exceptions.LeaderNotAvailable, e:
            reset_kafka()
            logger.info('推送' + common_settings.SAVE_TYPE + '出错：' + str(traceback.format_exc()))
            # kafka_producer.produce(dumps.encode('utf8'))

    except Exception, e:
        logger.info('数据保存失败' + str(traceback.format_exc()))
        return False
    return True


def add_task(data):
    try:
        url = common_settings.TASK_URL + common_settings.CREATE_TASK_PATH
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }
        r = download(url=url, data=data, headers=headers, method='post')
        logger.info('任务添加完毕 %s' % r['code'])
    except Exception, e:
        logger.error(traceback.format_exc())


def find(pattern, context):
    if not context:
        return None

    findall = re.findall(pattern=pattern, string=context)

    if findall:
        return findall[0]
    else:
        return None


'''
去掉emoji表情
'''


def remove_emoji(content):
    emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
        "+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', content)


def test():
    pass


if __name__ == '__main__':
    test()
