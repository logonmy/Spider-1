#!coding:utf8
# 本程序共一种线程，入口如下，其他方法均被此方法调用
#
# awake_thread（若干）：简历搜索唤醒线程。主要流程：从调度拿取任务，搜索列表页，去重后拿取详情页，并推送mysql和mns进行唤醒
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
from lxml import etree
import create_task
import HTMLParser
import re

stop_tag = False
sleep_tag = True
push_task_time = None
push_task_keyword_tag = '0'
push_task_lock = threading.Lock()
htmlparser = HTMLParser.HTMLParser()
job_now_re = re.compile(u'当前工作：(.*?)</div>')

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

# 调用此方法向钉钉发送消息
dingding_robot = None
def send_dingding_text(text):
    global dingding_robot
    if not dingding_robot:
        dingding_robot = DingDingRobot('eb749abfe9080a69da6524b77f589b8f6ddbcc182c7a41bf095b095336edb0a1')
    dingding_robot.send_text(text)

# 从调度中获取不到任务之后，会调用此方法推送新一轮任务，14400秒内只会推送一轮任务
def push_task():
    logger = utils.get_logger()
    global push_task_time
    global push_task_lock
    global push_task_keyword_tag
    if push_task_lock.locked():
        return
    # 推送任务时加锁，确保每次只有一个线程在推送任务
    push_task_lock.acquire()
    if not push_task_time or (datetime.datetime.now()-push_task_time).seconds>14400:
        send_dingding_text(u'开始推送人才啊简历任务.')
        create_task.create_task_from_mysql(push_task_keyword_tag)
        push_task_keyword_tag = '0' if push_task_keyword_tag == '1' else '1'
        push_task_time = datetime.datetime.now()
    push_task_lock.release()

# 从account模块随机获取一个账号，若获取不到账号则sleep，直到获取到账号为止
def get_one_account(download=False):
    # return {'username': 'test130279237', 'passwd': 'jinqian4611', 'id': 805}, 'JSESSIONID=B414F2E2E1B49632923D86C1B18DFDD5'
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

# 设置账号cookie失效，并重新登录
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
        send_dingding_text(u'人才啊账号需要认证:%s' % account['username'])
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

# 更新账号今天搜索可用次数
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

# 获取mns客户端
def get_mns_client():
    mns_account = Account(common_settings.ENDPOINT, common_settings.ACCID, common_settings.ACCKEY, common_settings.TOKEN)
    mns_client = mns_account.get_queue(common_settings.MNS_QUEUE)
    return mns_client

# 获取列表页
def get_list(cookie, page_numner, params, proxy=None):
    '''
    args:
        cookie: 账号cookie
        page_numner: 页码
        params: 列表页参数，职能、城市，从任务中获取
        proxy: 代理
    return:
        {'code':0, 'data': [], 'has_next_page': False}
        code: 0,成功; 非0, 失败
        data: 简历数据（加入待处理前的id, third_id, srcid, list页面中获取到的info）
        has_next_page: 是否有下一页
    '''
    logger = utils.get_logger()
    result = {'code': 0, 'data': [], 'has_next_page': False}
    logger.info('use proxy '+str(proxy) + ' to download list')

    try:
        list_url = 'http://www.rencaiaaa.com/resumeSearch/list.do?pager.offset=%s&pager.pageSize=20' % ((page_numner-1)*20,)
        list_header = {
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
        list_data = {
            'keyword': '', 
            'searchCollection': '2', 
            'searchCollectionName': u'免费简历', 
            'spreadSearchCondition': '1', 
            'residenceProvinceId': '1', 
            'residenceIds': params['residence_ids'], 
            'residenceName': params['residence_name'], 
            'includeExpectPlace': '0', 
            'diplomaIdMin': '1', 
            'diplomaNameMin': u'不限', 
            'diplomaIdMax': '1', 
            'diplomaNameMax': u'不限', 
            'workYearsMin': '0', 
            'workYearsNameMin': u'不限', 
            'workYearsMax': '0', 
            'workYearsNameMax': u'不限', 
            'expectSalaryMin': '0', 
            'expectSalaryNameMin': u'不限', 
            'expectSalaryMax': '0', 
            'expectSalaryNameMax': u'不限', 
            'industryIds': '', 
            'industryIdName': u'行业', 
            'industryStrs': '', 
            'functionIds2': '', 
            'function2Strs': '', 
            'functionIds3': params['function_ids3'], 
            'function3Strs': params['function_id_name'], 
            # 'function3Strs': params['function3_strs'], 
            'functionIdName': params['function_id_name'], 
            'sexId': '2', 
            'sexName': u'性别', 
            'ageMinInput': '', 
            'ageMaxInput': '', 
            'ageMin': '', 
            'ageMax': '', 
            'ageName': u'年龄', 
            'jobStatus': '', 
            'jobStatusName': u'求职状态', 
            'updateTimeType': '1', 
            'updateTimeTypeName': u'1周内', 
            'excludeViewedInDays': '0', 
            'marriage0': '', 
            'marriage1': '', 
            'schLevel2': '', 
            'schLevel3': '', 
            'toPage': '', 
            'sortFlag': '1', 
            'sourceId': '-1', 
            'name': '', 
            'groupId': '0', 
            'emailContent': u'您好，该简历我已查阅，请您评估一下。若觉得合适，我们将安排面试，谢谢！', 
            'reviewName': '', 
            'reviewEmail': '', 
            'positionName': '', 
            'candidateEmail': '', 
            'interviewStr': '', 
            'resume_pname': '', 
            'linkedPerson': '', 
            'contactNo': '', 
            'contactEmail': '', 
            'interviewAddress': '', 
            'companyName': '', 
            'interviewerMail': '', 
            'smssent': '', 
            'emailContent': '', 
            'positionName': '', 
            'ageFlag': '1', 
            'schoolNameFlag': '1', 
            'diplomaFlag': '1', 
            'workYearFlag': '1', 
            'recentCompanyFlag': '1', 
            'recentPositionFlag': '1', 
            'wantMonthSalaryFlag': '1', 
            'updateTimeFlag': '1', 
            'bindEmail_ssl': 'false', 
            'talentInviteMailTitle': '', 
            'talentInviteMailTxt': '', 
            'salaryMinInvite': '', 
            'salaryMaxInvite': '', 
            'workPlace': '', 
            'candidateName': '', 
            'talentInvitePid': '', 
            'talentInviteTemplateId': '', 
        }

        list_response = requests.post(list_url, headers=list_header, data=list_data, proxies=proxy, allow_redirects=False, timeout=30)
        # print cookie
        if list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/login.jsp?errMsg=':
                logger.info('invalid cookie, need login.')
                result['code'] = 5
                return result
        elif list_response.status_code in [302, '302'] and list_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
            logger.info('list response status headers:'+str(list_response.headers))
            result['code'] = 6
            return result
        elif list_response.status_code not in [200, '200']:
            logger.info('list response status code:'+str(list_response.status_code))
            result['code'] = 1
            return result
        list_root = etree.HTML(list_response.text)
        div_list = list_root.xpath('//div/div[@class="listShow"]/div[@class="resumediv p_r r_bd4_b"]')
        ids = []
        for div in div_list:
            re_ids = div.xpath('.//input[@class="re_rid"]')
            re_extrids = div.xpath('.//input[@class="re_extrid"]')
            re_srcs = div.xpath('.//input[@class="re_src"]')
            if not re_ids or not re_extrids or not re_srcs:
                continue
            re_id = re_ids[0].attrib.get('value', '')
            re_extrid = re_extrids[0].attrib.get('value', '')
            re_src =re_srcs[0].attrib.get('value', '')

            ids.append([str(re_id), str(re_extrid), str(re_src), htmlparser.unescape(etree.tostring(div, pretty_print=False))])

        #     ids.remove('')
        result['data'] = ids
        if u'下一页</a>' in list_response.text:
            result['has_next_page'] = True
        else:
            result['has_next_page'] = False
        return result
    except Exception, e:
        logger.info(str(traceback.format_exc()))
    result['code'] = 3
    return result

# 获取详情页
def get_resume(rid, thirdid, srcid, cookie, proxy=None):
    '''
    获取简历的用户姓名、联系方式、最近工作职位（无工作经历等任何其他信息）
    args:
        rid: 列表页中的简历id
        thirdid: 列表页中获取到的third id
        srcid: 列表页中获取到的srcid
        cookie: 账号cookie
        proxy: 代理
    return:
        {'code': 0, 'charge_json': {'mail': '', 'phone': '', 'job_now'}, 'real_rid': '', 'name': ''}
        code: 0,成功;非0, 失败
        charge_json: 从购买页面解析出来的手机号、邮箱、最近工作
        name: 待处理列表页获取到的姓名
        real_rid: 加入代理之后的rid
    '''
    # time.sleep(1)
    logger = utils.get_logger()
    logger.info('use proxy '+str(proxy)+'to download resume')
    result = {'code': 0}

    try:
        # 将简历加入到待处理
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

        # # 获取简历详情页，之前版本需要，现在已经弃用
        # time.sleep(random.choice([2, 3, 4]))
        # get_resume_url = 'http://www.rencaiaaa.com/rdetail/recommendDetail.do?ext=1&resumeType=0&rid=%s&pid=0&srcid=%s&thirdId=%s&type=3' % (tmp_rid, srcid, thirdid)
        # get_resume_header = {
        #     'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        #     'Accept-Encoding':'gzip, deflate',
        #     'Accept-Language':'zh-CN,zh;q=0.8',
        #     'Cookie':cookie,
        #     'Host':'www.rencaiaaa.com',
        #     'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        # }
        # logger.info('start to get resume'+get_resume_url)
        # get_resume_response = requests.get(get_resume_url, headers=get_resume_header, allow_redirects=False, timeout=30, proxies=proxy)
        # if get_resume_response.status_code not in [200, '200']:
        #     logger.info('not get 200 when get resume response:'+str(get_resume_response.status_code))
        #     result['code'] = 4
        #     return result


        # 获取待处理列表页，并解析姓名
        get_name_url ='http://www.rencaiaaa.com/resume/manage.do'
        get_name_header = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': cookie,
            'Host':'www.rencaiaaa.com',
            'Origin':'http://www.rencaiaaa.com',
            'Referer':'http://www.rencaiaaa.com/main.do',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            'X-Requested-With':'XMLHttpRequest',
        }
        get_name_data = {
            'applyStage':'',
            'applyStatus':'',
            'candidateStr':'',
            'msgnum':'',
            'style':'',
            'bindEmail_ssl':'false',
            'talentInviteMailTitle':'',
            'talentInviteMailTxt':'',
            'salaryMinInvite':'',
            'salaryMaxInvite':'',
            'workPlace':'',
            'candidateName':'',
            'talentInvitePid':'',
            'talentInviteTemplateId':'',
        }
        get_name_response = requests.post(get_name_url, headers=get_name_header, data=get_name_data, allow_redirects=False, timeout=30, proxies=proxy)
        if get_name_response.status_code in [302, '302'] and get_name_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
            logger.info('get name response status headers:'+str(get_name_response.headers))
            result['code'] = 7
            return result
        elif get_name_response.status_code not in [200, '200']:
            logger.info('not get 200 when add url:'+str(get_name_response.status_code))
            result['code'] = 2
            return result
        get_name_root = etree.HTML(get_name_response.text)
        name_span_list = get_name_root.xpath('//span[@class="resumedivname r_tc4 f_s16"]')
        name = ''
        for name_span in name_span_list:
            id_list = name_span.xpath('.//input[@class="re_rid"]')
            if not id_list:
                continue
            if str(id_list[0].attrib.get('value')) == str(tmp_rid):
                name=name_span.text.strip()
                break
        if not name:
            logger.info('not get name in get_name_list')
            result['code'] = 10
            return result
        result['name'] = name
        try:
            # 将简历置为不合适
            time.sleep(random.choice([2, 3, 4]))
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



        # 购买简历（直接获取页面，无需下载点），并解析出手机号、邮箱、最近工作，某些字段可能没有
        charge_json = {'phone': '', 'mail': '', 'job_now': ''}
        charge_url = 'http://www.rencaiaaa.com/rdetail/recommendDetail.do?resumeType=1&rid=%s&pid=0&srcid=%s&thirdId=%s&type=3' % (tmp_rid, srcid, thirdid)
        charge_header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Cookie':cookie,
            'Host':'www.rencaiaaa.com',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        charge_response = requests.get(charge_url, headers=charge_header, allow_redirects=False, timeout=30, proxies=proxy)
        if charge_response.status_code in [302, '302'] and charge_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/authexpire.do':
            logger.info('get resume response status headers:'+str(charge_response.headers))
            result['code'] = 9
            return result
        elif charge_response.status_code in [302, '302'] and charge_response.headers.get('Location', '') == 'http://www.rencaiaaa.com/login.jsp?errMsg=':
            logger.info('need relogin')
            result['code'] = 1
            return result
        elif charge_response.status_code not in [200, '200']:
            logger.info('not get 200 when get resume response:'+str(charge_response.status_code))
            result['code'] = 4
            return result
        if u'该用户暂无求职意向，已在外网设置简历不公开' in charge_response.text:
            result['code'] = 7
            return result
        resume_root = etree.HTML(charge_response.text)
        contact_list = resume_root.xpath('//div[@class="rd-contact-flag"]')
        job_now_list = job_now_re.findall(charge_response.text)
        if job_now_list:
            charge_json['job_now'] = htmlparser.unescape(job_now_list[0])
        if len(contact_list)<3 and len(contact_list)>=1:
            contact_str_list = []
            for i in contact_list:
                if i.text:
                    contact_str_list.append(i.text)
            if not contact_str_list:
                pass
            elif '@' in contact_str_list[0]:
                charge_json['mail'] = contact_str_list[0]
                if len(contact_str_list) ==2:
                    charge_json['phone'] = contact_str_list[1]
            else:
                charge_json['phone'] = contact_str_list[0]
                if len(contact_str_list) ==2:
                    charge_json['mail'] = contact_str_list[1]
        

        # result['data'] = get_resume_response.text
        result['real_rid'] = tmp_rid
        result['charge_json'] = charge_json
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

    logger.info('deal with:'+str(task))

    page_now = 1
    download_day = str(time.localtime().tm_mon)+'-'+str(time.localtime().tm_mday)
    while page_now != -1:
        logger.info('start download page:'+str(page_now))
        # 每个列表页更换一次账号
        account, cookie = get_one_account()
        # 获取列表页
        list_result = get_list(cookie, page_now, task, proxy)
        #time.sleep(2)
        if list_result['code'] == 5:
            set_unavaliable_account(account)
            continue
        elif list_result['code'] == 6:
            set_forbidden_account(account)
            continue
        elif list_result['code']:
            logger.info('get error list result:'+str(list_result))
            page_now = -1
            continue
        logger.info('page number of now is '+str(page_now))

        # 逐个处理简历
        for resume_one in list_result['data']:
            resume, thirdid, srcid, list_content = resume_one
            has_find_in_redis = False
            resume_key = 'rencaia_resume_'+str(resume)
            real_rid = ''
            real_thirdid = ''
            # 在redis中查看今天是否已经下过，若今天已经下过，则跳过
            try:
                resume_redis_value=redis_client.get(resume_key)
                if resume_redis_value:
                    resume_redis_value_list = resume_redis_value.split('_')
                    if resume_redis_value_list[0] == download_day:
                        has_find_in_redis = True
                    real_rid = resume_redis_value_list[1]
                    real_thirdid = resume_redis_value_list[2]
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
                logger.info('has find %s in redis' % resume_key)
                continue
            else:
                logger.info('not find %s in redis' % resume_key)

            # 获取简历信息，尝试三次，三次失败则跳过
            for x in xrange(3):
                account, cookie = get_one_account()
                resume_result = get_resume(resume, thirdid, srcid, cookie, proxy=proxy)
                update_refresh_score(account)
                if resume_result['code'] == 1:
                    set_unavaliable_account(account)
                    account = None
                    continue
                if resume_result['code'] == 7:
                    set_forbidden_account(account)
                    account = None
                    continue
                if resume_result['code']:
                    logger.info('get error resume:'+str(resume_result))
                    continue
                
                # if u'存在被盗用的风险' in resume_result['data']:
                #     logger.info(u'find 存在被盗用的风险 in page:'+str(account))
                #     set_forbidden_account(account)
                #     account = None
                #     redis_client.delete(resume_key)
                #     continue
                # if u'该用户暂无求职意向，已在外网设置简历不公开' in resume_result['data']:
                #     # logger.info('un publish resume:'+str(resume)+ 'account:'+account['username'])
                #     # redis_client.delete(resume_key)
                #     logger.info('get not open resumed:'+str(account))
                #     # set_forbidden_account(account)
                #     continue
                redis_client.set(resume_key, '_'.join([download_day, str(resume_result['real_rid'] or real_rid), thirdid, srcid]))
                break
            else:
                continue


            # 保存数据至mysql和mns
            resume_uuid = uuid.uuid1()
            try:
                content = {'html':list_content}
                content['email'] = resume_result['charge_json'].get('mail')
                content['phone'] = resume_result['charge_json'].get('phone')
                content['name'] = resume_result.get('name')
                content = json.dumps(content, ensure_ascii=False)
                sql = 'insert into resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject, reason) values (%s, %s, "python", %s, now(), %s, %s, %s, %s, "list")'
                sql_value = (common_settings.SOURCE, content, resume_uuid, str(account['username']), task['function_id_name'], task['residence_name'], str(resume))

                resume_update_time = ''
                # resume_update_time =  resume_result['json']['updateDate'] 
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
                        'emailJobType': task['function_id_name'],
                        'emailCity': task['residence_name'],
                        'subject': str(resume),
                        'reason': 'list',
                    },
                    "interfaceType": "PARSE",
                    "resourceDataType": "RAW",
                    "resourceType": "RESUME_INBOX",
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

# 唤醒线程入口, 本方法从调度获取任务，基本无需更改，如需更改处理任务流程，请更改awake_one_task方法
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
            # print '---------------the process_result:', process_result
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
    cookie = 'JSESSIONID=2F6583645ACFFF1B20E9E7102BED31BF'
    task = {'residence_ids': '1', 'residence_name': u'北京', 'function_ids3':'293', 'function3_strs': u'IT技术/研发经理/主管', 'function_id_name': u'IT技术/研发经理/主管'}
    # print get_list(cookie, 1, task, None)
    # print get_list_with_keyword(cookie, 1, task, None)
    print  get_resume('36861855', '304990956', '0', cookie)
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

    search_number = common_settings.SEARCH_THREAD_NUMBER

    search_thread_list = []
    for x in xrange(search_number):
        search_thread = threading.Thread(target=awake_thread, name='Thread-'+str(x))
        search_thread.start()
        search_thread_list.append(search_thread)


    for i in search_thread_list:
        i.join()

    logger.info('done.')
