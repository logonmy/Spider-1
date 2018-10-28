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
import HTMLParser
import re

stop_tag = False
sleep_tag = True
get_task_queue = None
push_task_time = None
push_task_keyword_tag = '0'
deal_task_lock = threading.Lock()
htmlparser = HTMLParser.HTMLParser()
job_now_re = re.compile(u'当前工作：(.*?)</div>')

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
    if not push_task_time or (datetime.datetime.now()-push_task_time).seconds>14400:
        send_dingding_text(u'开始推送人才啊简历任务.')
        create_task.create_task_from_mysql(push_task_keyword_tag)
        push_task_keyword_tag = '0' if push_task_keyword_tag == '1' else '1'
        push_task_time = datetime.datetime.now()
    push_task_lock.release()

def get_one_account(download=False):
    # return {'username': 'test130279237', 'passwd': 'jinqian4611', 'id': 805}, 'JSESSIONID=C418E9DA2B9FB1051BEE86F19076CE4D'
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
        time.sleep(60)

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
        send_dingding_text(u'人才啊账号需要认证:%s' % account['username'])
        logger.info('set forbidden account response:'+ response.text)
    except Exception, e:
        logger.info(str(traceback.format_exc()))

mysql_pool = None
def get_mysql_client():
    logger = utils.get_logger()
    logger.info('get a mysql connect')
    global mysql_pool
    if not mysql_pool:
        mysql_pool = PersistentDB(
            MySQLdb, 
            host=common_settings.MYSQL_HOST, 
            user=common_settings.MYSQL_USER,
            passwd=common_settings.MYSQL_PASSWD, 
            db=common_settings.MYSQL_DOWNLOAD_DB,
            port=common_settings.MYSQL_PORT, 
            charset='utf8'
        )
    conn = mysql_pool.connection()
    cur = conn.cursor()
    return conn, cur

def update_refresh_score(account):
    logger = utils.get_logger()
    logger.info('update coin number:'+str(account))
    url = common_settings.UPDATE_DOWNLOAD_SCORE
    data = {
        # 'id': account['id'],
        'freshScore': account['freshScore']-1,
        'userName': account['username'],
        'password': account['passwd'],
        'source': common_settings.SOURCE,
    }
    try:
        response = requests.post(url, data=data)
    except Exception, e:
        logger.info(str(traceback.format_exc()))

def get_mns_client():
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY, common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client

def get_resume(rid, thirdid, srcid, cookie, proxy=None):
    # time.sleep(1)
    logger = utils.get_logger()
    logger.info('use proxy '+str(proxy)+'to download resume')
    result = {'code': 0}
    global htmlparser

    try:
        # add resume into unhandle
        add_url = 'http://www.rencaiaaa.com/resume/addCandidate.do'
        add_header = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie':cookie,
            'Host':'www.rencaiaaa.com',
            'Origin':'http://www.rencaiaaa.com',
            'Referer':'http://www.rencaiaaa.com/main.do',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'X-Requested-With':'XMLHttpRequest',
        }
        add_data = {
            'rid': rid,
            'srcid': srcid,
            'thirdId': thirdid,
            'resumeType':'1',
            'canContact':'0',
            'rpid':'0',
            'rStage':'1',
            'recommandType':'3',
            'ifMoveRecommendCv':'0',
        }
        logger.info('start to add response')
        add_response = requests.post(add_url, headers=add_header, data=add_data, proxies=proxy, allow_redirects=False, timeout=30)
        if add_response.status_code in [302, '302'] and add_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
            logger.info('add response status headers:'+str(add_response.headers))
            result['code'] = 7
            return result
        elif add_response.status_code in [302, '302'] and add_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/login.jsp?errMsg=':
            logger.info('need relogin')
            result['code'] = 1
            return result
        elif add_response.status_code not in [200, '200']:
            logger.info('not get 200 when add url:'+str(add_response.status_code))
            result['code'] = 2
            return result
        add_json = add_response.json()
        logger.info('o rid:'+rid)
        logger.info('thirdid:'+thirdid)
        logger.info('add response:'+add_response.text)
        tmp_rid = add_json.get('result', {}).get('rid', '')
        if add_json.get('errCode', 0) not in [100, '100'] or add_json.get('ok', 0) not in [True, 'true'] or not tmp_rid:
            logger.info('add resume to Candidate failed:'+add_response.text)
            result['code'] = 3
            return result

        # get resume info
        # time.sleep(random.choice([2, 3, 4]))
        get_resume_url = 'http://www.rencaiaaa.com/rdetail/recommendDetail.do?resumeType=1&rid=%s&pid=0&srcid=%s&thirdId=%s&type=3' % (tmp_rid, srcid, thirdid)
        get_resume_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie':cookie,
            'Host':'www.rencaiaaa.com',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        logger.info('start to get resume')
        get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30, proxies=proxy)
        if get_resume_response.status_code in [302, '302'] and get_resume_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
            logger.info('get resume response status headers:'+str(get_resume_response.headers))
            result['code'] = 7
            return result
        elif get_resume_response.status_code in [302, '302'] and get_resume_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/login.jsp?errMsg=':
            logger.info('need relogin')
            result['code'] = 1
            return result
        elif get_resume_response.status_code not in [200, '200']:
            logger.info('not get 200 when get resume response:'+str(get_resume_response.status_code))
            result['code'] = 4
            return result
        resume_root = etree.HTML(get_resume_response.text)
        resume_info_list = resume_root.xpath('//div[@class="rd-head-info"]')
        contact_list = resume_root.xpath('//div[@class="rd-contact-flag"]')
        job_now_list = job_now_re.findall(get_resume_response.text)
        if resume_info_list:
            result['data'] = htmlparser.unescape(etree.tostring(resume_info_list[0], pretty_print=False))
            result['phone'] = ''
            result['email'] = ''
            result['job_now'] = ''
        if job_now_list:
            result['job_now'] = htmlparser.unescape(job_now_list[0])
        if len(contact_list)<3 and len(contact_list)>=1:
            contact_str_list = []
            for i in contact_list:
                if i.text:
                    contact_str_list.append(i.text)
            if not contact_str_list:
                pass
            elif '@' in contact_str_list[0]:
                result['email'] = contact_str_list[0]
                if len(contact_str_list) ==2:
                    result['phone'] = contact_str_list[1]
            else:
                result['phone'] = contact_str_list[0]
                if len(contact_str_list) ==2:
                    result['email'] = contact_str_list[1]

        try:
            # set resume unavaliable
            # time.sleep(random.choice([2, 3, 4]))
            set_resume_unavaliable_url = 'http://www.rencaiaaa.com/resume/changeStage.do'
            set_resume_unavaliable_header = {
                'Accept':'*/*',
                'Accept-Encoding':'gzip, deflate',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie':cookie,
                'Host':'www.rencaiaaa.com',
                'Origin':'http://www.rencaiaaa.com',
                'Referer':'http://www.rencaiaaa.com/main.do',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'X-Requested-With':'XMLHttpRequest',
            }
            set_resume_unavaliable_data = {
                'rid': tmp_rid,
                'pid':'0',
                'stage':'6',
                'status':'2',
            }
            logger.info('start to set resume unavaliable')
            set_resume_unavaliable_response = requests.post(set_resume_unavaliable_url, headers=set_resume_unavaliable_header, data=set_resume_unavaliable_data, proxies=proxy, allow_redirects=False, timeout=30)
            if set_resume_unavaliable_response.status_code not in [200, '200']:
                logger.info('not get 200 when set resume unavaliable:'+str(set_resume_unavaliable_response.status_code))
                # result['code'] = 5
                # return result
            set_json= set_resume_unavaliable_response.json()
            if set_json.get('errCode', '') not in [100, '100'] or set_json.get('msg', 'error') or set_json.get('ok', '') not in [True, 'true']:
                logger.info('set resume unavaliable failed:'+set_resume_unavaliable_response.text)
                # result['code'] = 6
                # return result
        except Exception, e:
            logger.info('get error when set resume in avaliable:'+str(traceback.format_exc()))
            result['code'] = 8
            return result
        
        result['info_url'] = get_resume_url
        # result['data'] = get_resume_response.text
        result['real_rid'] = tmp_rid
        return result

    except Exception, e:
        logger.info('get error when download resume:'+str(traceback.format_exc()))
        result['code'] = 1
        return result

task_list = []
def get_task():
    logger = utils.get_logger()
    logger.info('='*50 + '\nstart deal thread')
    conn, cur = get_mysql_client()
    global task_list
    deal_task_lock.acquire()
    while not task_list:
        task_number = cur.execute('select * from rencaia_all_resume where status=0 limit 30')
        if not task_number:
            logger.info('not get task in mysql, sleep 300')
            time.sleep(300)
            continue
        task_list = list(cur.fetchall())
    task = task_list.pop()
    cur.execute('update rencaia_all_resume set status=1 where id='+str(task[0]))
    conn.commit()
    deal_task_lock.release()
    return task

def deal_task():
    logger = utils.get_logger()
    logger.info('='*50 + '\nstart deal thread')
    task_list = []
    conn, cur = get_mysql_client()
    change_account_number = 10
    account = {}

    while True:
        task = get_task()
        proxy = settings.get_proxy()
        
        # task = redis_client.get(task_list.pop())
        task_split = task[12].split('_')

        for x in xrange(5):
            if not change_account_number or not account:
                account, cookie = get_one_account()
            start_time = time.time()
            resume_result = get_resume(task_split[0], task_split[1], task_split[2], cookie, proxy=proxy)
            end_time = time.time()
            logger.info('once time cost:'+ str(int(end_time-start_time)))
            # update_refresh_score(account)
            if resume_result['code'] == 1:
                set_unavaliable_account(account)
                account = None
                # redis_client.delete(resume_key)
                continue
            if resume_result['code'] == 7:
                set_forbidden_account(account)
                account = None
                # redis_client.delete(resume_key)
                continue
            if resume_result['code']:
                logger.info('get error resume:'+str(resume_result))
                # redis_client.delete(resume_key)
                account = None
                continue
            
            # if u'存在被盗用的风险' in resume_result['data']:
            #     logger.info(u'find 存在被盗用的风险 in page:'+str(account))
            #     set_forbidden_account(account)
            #     account = None
            #     redis_client.delete(resume_key)
            #     continue
            if 'data' not in resume_result:
                logger.info('not get data in resume result.')
                continue
            if u'该用户暂无求职意向，已在外网设置简历不公开' in resume_result['data']:
                # logger.info('un publish resume:'+str(resume)+ 'account:'+account['username'])
                # redis_client.delete(resume_key)
                logger.info('get not open resumed:'+str(account))
                # set_forbidden_account(account)
                continue
            

            resume_uuid = uuid.uuid1()
            try:
                sql = 'update rencaia_all_resume set status=2, info_content=%s, resumeid=%s, url=%s,  phone=%s, email=%s, job_now=%s, ip=%s, account=%s where id=%s'
                sql_value = (resume_result['data'], resume_result['real_rid'], resume_result.get('info_url'), resume_result.get('phone'), resume_result.get('email'),resume_result.get('job_now'), proxy['http'], account['username'], task[0])

                cur.execute(sql, sql_value)
                conn.commit()

                logger.info('save resume success: %s' % task[0])
                break

            except Exception, e:
                logger.info('get error when write mysql, exit!!!'+str(traceback.format_exc()))
                # return
            # time.sleep(1)
            #return
        else:
            logger.info('did not success after 5 times get resume of '+str(task[0]))
            sql = 'update rencaia_all_resume set status=3 where id=%s'
            sql_value = (task[0], )
            cur.execute(sql, sql_value)
            conn.commit()

def test():
    cookie = 'JSESSIONID=73787069B3F9403FAB98EC91F4FFF3D1'
    task = {'residence_ids': '1', 'residence_name': u'北京', 'function_ids3':'293', 'function3_strs': u'IT技术/研发经理/主管', 'function_id_name': u'IT技术/研发经理/主管'}
    a = awake_one_task(task)
    # a = get_list(cookie, 1, task, None)
    # a= get_list_with_keyword(cookie, 1, task, None)
    # a = get_resume('80887364', '609625363', '1', cookie)
    f=open('123', 'w')
    f.write(json.dumps(a, ensure_ascii=False))
    f.close()

if __name__ == '__main__':
    settings.project_settings['PROJECT_NAME'] = 'resume_rencaia_all_download'
    utils.set_setting(settings.project_settings)
    logger = utils.get_logger()
    logger.info('='*50 + 'start main')
    # test()

    # global numbers_left, get_task_queue
    # numbers_left= common_settings.NUMBERS_ERVERYDAY
    # get_task_queue = Queue.Queue(maxsize=common_settings.QUEUE_MAX_SIZE)


    dowload_number = common_settings.DOWNLOAD_THREAD_NUMBER

    conn, cur = get_mysql_client()
    cur.execute('update rencaia_all_resume set status=0 where status=1')
    conn.commit()
    deal_thread_list = []
    for x in xrange(dowload_number):
        deal_thread = threading.Thread(target=deal_task, name='Thread-'+str(x))
        deal_thread.start()
        deal_thread_list.append(deal_thread)

    for i in deal_thread_list:
        i.join()

    # logger.info('done.')
