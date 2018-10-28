#!coding:utf8

import sys
import os
import urllib

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)

import logging
import traceback
from logging.handlers import RotatingFileHandler
import uuid
import time
import datetime
import json
import requests
import re
import random
import utils
#from selenium import webdriver
import copy

# from ctypes import *
#import ctypes

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

def get_device():
    a='1234567890'
    b=[random.choice(a) for i in xrange(15)]
    return ''.join(b)

def login(username, passwd, proxy, deviceid):
    logger = utils.get_logger()
    return_result = {'login_data': '', 'session': None, 'code': 1}
    for i in range(3):
        logger.info('start login '+ str(username))
        mobile = username
        password = passwd

        headers = {
            'versionCode': 'Android_30',
            'versionName': 'Android_5.9.0',
            'UMengChannel': '2',
            'uid': '',
            'Cookie': 'bps=',
            'appSign': '-1012826753',
            'deviceID': deviceid,
            'deviceName': 'MI5S',
            'role': 'boss',
            'deviceModel': 'MI5S',
            'deviceVersion': '6.0',
            'pushVersion': '52',
            'platform': 'Android-23',
            'User-Agent': 'ChinaHrAndroid5.9.0',
            'extion': '',
            'pbi': '{"itemIndex":0,"action":"click","block":"03","time":%s,"targetPage":"b.LoginActivity\/","page":"2302","sourcePage":""}' % str(int(time.time()*1000)),
            'Brand': 'Xiaomi',
            'device_id': deviceid,
            'device_name': 'MI5S',
            'device_os': 'Android',
            'device_os_version': '6.0',
            'app_version': '5.9.0',
            'uidrole': 'boss',
            'utm_source': '2',
            'tinkerLoadedSuccess': 'false',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'passport.chinahr.com',
            'Accept-Encoding': 'gzip',
        }

        # login
        # print 'proxies is', proxy 
        logger.info('proxies is' + str(proxy))
        try:
            session = requests.session()
            response = session.post('https://passport.chinahr.com/app/login', data={
                'input': mobile,
                'pwd': password,
                'source': '0',
                'msgCode': '',
            }, headers=headers, proxies=proxy, timeout=30)
            json_data = response.json()
            logger.info('return result of login %s' % json_data)
            code = json_data.get('code')
            msg = json_data.get('msg')
            data = json_data.get('data', {})
            if code in [0, '0']:
                # cookie = dict(response.cookies)
                # login_data = data
                return_result['session'] = session
                return_result['code'] = 0
                return_result['login_data'] = data
            else:
                continue
            return return_result
        except Exception, e:
            logger.info(str(traceback.format_exc()))
            return_result = {'login_data': '', 'session': None, 'code': 2}

        logger.info(str(username) + ' login error times ' + str(i))
    return return_result

def get_list(user_now, params, proxy, list_page):
    logger = utils.get_logger()
    global citys_dict
    for x in xrange(5):
        try:
            #get_number_url = 'https://app.chinahr.com/cvapp/search?keyword=%s&minAge=20&maxAge=30&live=%s&workExp=0&degree=%s&reFreshTime=%s&page=%s&searchType=' % (params['keyword'], params['live'], params['degree'], params['refreshTime'], list_page)
            #zuijingongzuo
            #get_number_url = 'https://app.chinahr.com/cvapp/search?keyword=%s&maxAge=35&live=%s&workExp=0&degree=0&reFreshTime=1&page=%s&searchType=1' % (urllib.quote(params['keyword'].encode('utf8')).upper(), citys_dict[params['zone']], list_page)
            get_number_url = 'https://app.chinahr.com/cvapp/search?keyword=%s&maxAge=35&live=%s&workExp=0&degree=0&reFreshTime=2&page=%s&searchType=' % (urllib.quote(params['keyword'].encode('utf8')).upper(), citys_dict[params['zone']], list_page)
            # get_number_url = 'https://app.chinahr.com/cvapp/search?keyword=%s&live=%s&workExp=0&degree=%s&reFreshTime=%s&page=%s&searchType=' % (params['keyword'], params['live'], params['degree'], params['refreshTime'], list_page)
            get_number_headers = {
                'versionCode': 'Android_30',
                'versionName': 'Android_5.9.0',
                'UMengChannel': '2',
                'uid': str(user_now['uid']),
                'appSign': '-1012826753',
                'deviceID': str(user_now['device_id']),
                'deviceName': 'MI5S',
                'role': 'boss',
                'deviceModel': 'MI5S',
                'deviceVersion': '6.0',
                'pushVersion': '52',
                'platform': 'Android-23',
                'User-Agent': 'ChinaHrAndroid5.9.0',
                'extion': '',
                'pbi': '{"itemIndex":0,"action":"click","block":"02","time":%s,"targetPage":"b.B_ResultListActivity\/","page":"2101","sourcePage":""}' % str(int(time.time()*1000)),
                'Brand': 'Xiaomi',
                'device_id': str(user_now['device_id']),
                'device_name': 'MI5S',
                'device_os': 'Android',
                'device_os_version': '6.0',
                'app_version': '5.9.0',
                'uidrole': 'boss',
                'utm_source': '2',
                'tinkerLoadedSuccess': 'false',
                'Host': 'app.chinahr.com',
                'Accept-Encoding': 'gzip',
                'Cookie': '; '.join([i[0]+'='+i[1] for i in user_now['cookie'].items()]),
            }
            logger.info('start download list:'+get_number_url)
            response = requests.get(get_number_url, headers=get_number_headers, proxies=proxy, timeout=30)
            json_data = response.json()
            if json_data.get('code', -1) in [0, '0']:
                #logger.info(str(json_data))
                return json_data
            elif json_data.get('code', -1) in [800, '800']:
                logger.info(str(json_data))
                return {'code': 1}
            elif json_data.get('code', -1) in [100, '100']:
                logger.info(str(json_data))
                return {'code': 3}
            else:
                logger.info(str(json_data))
                return {'code': 2}
        except Exception, e:
            logger.info('error '+ str(x)+ ' times of download list '+str(params)+' '+ str(list_page)+str(traceback.format_exc()))
            time.sleep(3)
        return {'code': -1}

def get_resume(user_now, cvid, proxy):
    logger = utils.get_logger()
    result = {'code': 0}
    if not user_now:
        logger.info('there has no user_now in resume, return!!!')
        result['code'] = 1
        return result
    if not proxy:
        logger.info('there has no proxy in resume, return!!!')
        result['code'] = 5
        return result
    if not cvid:
        logger.info('there has no cvid in resume, return!!!')
        result['code'] = 2
        return result

    try:
        # download the info page
        resume_url = 'https://app.chinahr.com/cvapp/cvdetails?cvid=%s&source=2&sourceType=&unid=' % cvid
        resume_header = {
            'versionCode': 'Android_30',
            'versionName': 'Android_5.9.0',
            'UMengChannel': '2',
            'uid': str(user_now['uid']),
            'appSign': '-1012826753',
            'deviceID': str(user_now['device_id']),
            'deviceName': 'MI5S',
            'role': 'boss',
            'deviceModel': 'MI5S',
            'deviceVersion': '6.0',
            'pushVersion': '52',
            'platform': 'Android-23',
            'User-Agent': 'ChinaHrAndroid5.9.0',
            'extion': '',
            'pbi': '{"itemIndex":0,"time":%s,"targetPage":"b.ResumeDetailActivity\/","page":"2101","itemType":"CV","action":"click","block":"03","itemId":"%s","sourcePage":""}' % (str(int(time.time()*1000)), cvid),
            'Brand': 'Xiaomi',
            'device_id': str(user_now['device_id']),
            'device_name': 'MI5S',
            'device_os': 'Android',
            'device_os_version': '6.0',
            'app_version': '5.9.0',
            'uidrole': 'boss',
            'utm_source': '2',
            'tinkerLoadedSuccess': 'false',
            'Host': 'app.chinahr.com',
            'Accept-Encoding': 'gzip',
            'Cookie': '; '.join([i[0]+'='+i[1] for i in user_now['cookie'].items()]),
        }
        # response = session.get(resume_url, headers=resume_header, proxies=proxy)
        # json_data = response.json()
        # if json_data.get('code', -1) not in [0, '0']:
        #     logger.info('get error resume of '+ str(cvid)+str(response.text))
        #     result['code'] = 8
        #     return result
        # else:
        #     age_str = json_data.get('data', {}).get('age', '')
        #     age_re = re.compile('(\d+).*')
        #     age_list = age_re.findall(age_str)
        #     if not age_list:
        #         logger.info('did not find the age in data!!!')
        #         result['code'] = 9
        #         return result
        #     elif int(age_list[0])>30 or int(age_list[0])<20:
        #         result['code'] = 10
        #         logger.info('the age is '+ str(age_list[0]))
        #         return result

        # need to renzheng
        # check_download_headers = copy.deepcopy(resume_header)
        # check_download_headers['pbi'] = '{"itemIndex":0,"action":"click","block":"01","time":%s,"targetPage":"b.ResumeDetailActivity\/","page":"2501","sourcePage":""}' % str(int(time.time()*1000))
        # check_download_url = 'https://app.chinahr.com/cvapp/checkDownload?cvid=%s' % cvid
        # response = session.get(check_download_url, headers=check_download_headers, proxies=proxy, timeout=30)
        # json_data = response.json()
        # if json_data.get('code', -1) not in [0, '0'] or not json_data.get('data', {}).get('downloadFlag', False):
        #     logger.info('get error result of check_download_url!!!'+str(response.text))
        #     result['code'] = 6
        #     return result
        # # print response.text
        # logger.info(response.text)

        # time.sleep(5)
        # do_download_url = 'https://app.chinahr.com/cvapp/doDownload?cvid=%s' % cvid
        # do_download_headers = copy.deepcopy(resume_header)
        # do_download_headers['pbi'] = '{"itemIndex":0,"action":"click","block":"01","time":%s,"targetPage":"b.ResumeDetailActivity\/","page":"2501","sourcePage":""}' % str(int(time.time()*1000))
        # response = requests.get(do_download_url, headers=do_download_headers, proxies=proxy, timeout=30)
        # json_data = response.json()
        # if json_data.get('code', -1) in [800, '800']:
        #     logger.info('get error result of do_download_url!!!'+str(response.text))
        #     result['code'] = 8
        #     return result
        # if json_data.get('code', -1) in [-1, '-1']:
        #     logger.info('get error result of do_download_url!!!'+str(response.text))
        #     result['code'] = 9
        #     return result
        # if json_data.get('code', -1) in [405, '405']:
        #     logger.info('need to auth the account, deviceid: '+str(str(user_now['device_id'])))
        #     result['code'] = 10
        #     return result
        # if json_data.get('code', -1) not in [0, '0'] :
        #     logger.info('get error result of do_download_url!!!'+str(response.text))
        #     result['code'] = 7
        #     return result

        response = requests.get(resume_url, headers=resume_header, proxies=proxy, timeout=30)
        json_data = json.loads(response.text)
        if json_data.get('code', -1) in [0, '0']:
            # print response.text
            return json_data
        else:
            logger.info('get error info resume of '+ str(cvid)+str(response.text))
            result['code'] = 3
    except Exception, e:
        logger.info('unkown error'+str(traceback.format_exc()))
        result['code']=4
    return result

def buy_resume(cookie, uid, cvid, proxy, deviceid):
    logger = utils.get_logger()
    result = {'code': 0}
    if not cookie:
        logger.info('there has no login_result in resume, return!!!')
        result['code'] = 1
        return result
    if not proxy:
        logger.info('there has no proxy in resume, return!!!')
        result['code'] = 5
        return result
    if not cvid:
        logger.info('there has no cvid in resume, return!!!')
        result['code'] = 2
        return result
    # session = login_result['session']

    try:
        # download the info page
        resume_url = 'https://app.chinahr.com/cvapp/cvdetails?cvid=%s&source=2&sourceType=&unid=' % cvid
        resume_header = {
            'versionCode': 'Android_30',
            'versionName': 'Android_5.9.0',
            'UMengChannel': '2',
            'uid': uid,
            'appSign': '-1012826753',
            'deviceID': deviceid,
            'deviceName': 'MI5S',
            'role': 'boss',
            'deviceModel': 'MI5S',
            'deviceVersion': '6.0',
            'pushVersion': '52',
            'platform': 'Android-23',
            'User-Agent': 'ChinaHrAndroid5.9.0',
            'extion': '',
            'pbi': '{"itemIndex":0,"time":%s,"targetPage":"b.ResumeDetailActivity\/","page":"2101","itemType":"CV","action":"click","block":"03","itemId":"%s","sourcePage":""}' % (str(int(time.time()*1000)), cvid),
            'Brand': 'Xiaomi',
            'device_id': deviceid,
            'device_name': 'MI5S',
            'device_os': 'Android',
            'device_os_version': '6.0',
            'app_version': '5.9.0',
            'uidrole': 'boss',
            'utm_source': '2',
            'tinkerLoadedSuccess': 'false',
            'Host': 'app.chinahr.com',
            'Accept-Encoding': 'gzip',
            'Cookie': '; '.join([i[0]+'='+i[1] for i in cookie.items()]),
        }
        # response = session.get(resume_url, headers=resume_header, proxies=proxy)
        # json_data = response.json()
        # if json_data.get('code', -1) not in [0, '0']:
        #     logger.info('get error resume of '+ str(cvid)+str(response.text))
        #     result['code'] = 8
        #     return result
        # else:
        #     age_str = json_data.get('data', {}).get('age', '')
        #     age_re = re.compile('(\d+).*')
        #     age_list = age_re.findall(age_str)
        #     if not age_list:
        #         logger.info('did not find the age in data!!!')
        #         result['code'] = 9
        #         return result
        #     elif int(age_list[0])>30 or int(age_list[0])<20:
        #         result['code'] = 10
        #         logger.info('the age is '+ str(age_list[0]))
        #         return result

        # need to renzheng
        check_download_headers = copy.deepcopy(resume_header)
        check_download_headers['pbi'] = '{"itemIndex":0,"action":"click","block":"01","time":%s,"targetPage":"b.ResumeDetailActivity\/","page":"2501","sourcePage":""}' % str(int(time.time()*1000))
        check_download_url = 'https://app.chinahr.com/cvapp/checkDownload?cvid=%s' % cvid
        response = requests.get(check_download_url, headers=check_download_headers, proxies=proxy, timeout=30)
        json_data = response.json()
        # if json_data.get('code', -1) not in [0, '0'] or not json_data.get('data', {}).get('downloadFlag', False):
        if json_data.get('code', -1) in [100, '100']:
            logger.info('get 100, need relogin')
            result['code'] = 11
            return result
        elif json_data.get('code', -1) not in [0, '0']:
            logger.info('get error result of check_download_url!!!'+str(response.text))
            result['code'] = 6
            return result
        # print response.text
        logger.info(response.text)

        # time.sleep(5)
        do_download_url = 'https://app.chinahr.com/cvapp/doDownload?cvid=%s' % cvid
        do_download_headers = copy.deepcopy(resume_header)
        do_download_headers['pbi'] = '{"itemIndex":0,"action":"click","block":"01","time":%s,"targetPage":"b.ResumeDetailActivity\/","page":"2501","sourcePage":""}' % str(int(time.time()*1000))
        response = requests.get(do_download_url, headers=do_download_headers, proxies=proxy, timeout=30)
        json_data = response.json()
        if json_data.get('code', -1) in [800, '800']:
            logger.info('get error result of do_download_url!!!'+str(response.text))
            result['code'] = 8
            return result
        if json_data.get('code', -1) in [-1, '-1']:
            logger.info('get error result of do_download_url!!!'+str(response.text))
            result['code'] = 9
            return result
        if json_data.get('code', -1) in [405, '405']:
            logger.info('need to auth the account, deviceid: '+str(deviceid))
            result['code'] = 10
            return result
        if json_data.get('code', -1) in [1, '1']:
            logger.info('get error result of do_download_url!!!'+str(response.text))
            result['code'] = 12
            return result
        # 暂时没有可用于下载此城市简历的点数,请选择其它简历下载
        if json_data.get('code', -1) in [2, '2']:
            logger.info('get error result of do_download_url!!!'+str(response.text))
            result['code'] = 13
            return result
        if json_data.get('code', -1) not in [0, '0'] :
            logger.info('get error result of do_download_url!!!'+str(response.text))
            result['code'] = 7
            return result

        response = requests.get(resume_url, headers=resume_header, proxies=proxy, timeout=30)
        json_data = json.loads(response.text)
        if json_data.get('code', -1) in [0, '0']:
            # print response.text
            return json_data
        else:
            logger.info('get error info resume of '+ str(cvid)+str(response.text))
            result['code'] = 3
    except Exception, e:
        logger.info('unkown error'+str(traceback.format_exc()))
        result['code']=4
    return result

def get_download_beans(cookie, uid, proxy, deviceid):
    logger = utils.get_logger()
    result = {'code': 0, 'coin_number': 0}
    has_login = False
    get_number_url = 'https://app.chinahr.com/buser/chrCoin/getCoinInfo'
    get_number_headers = {
        'versionCode': 'Android_30',
        'versionName': 'Android_5.9.0',
        'UMengChannel': '2',
        'uid': uid,
        'appSign': '-1012826753',
        'deviceID': deviceid,
        'deviceName': 'MI5S',
        'role': 'boss',
        'deviceModel': 'MI5S',
        'deviceVersion': '6.0',
        'pushVersion': '52',
        'platform': 'Android-23',
        'User-Agent': 'ChinaHrAndroid5.9.0',
        'extion': '',
        'pbi': '{"itemIndex":0,"action":"click","block":"02","time":%s,"targetPage":"class com.chinahr.android.b.resumepoint.ResumePointMainActivity\/","page":"2101","sourcePage":""}' % str(int(time.time()*1000)),
        'Brand': 'Xiaomi',
        'device_id': deviceid,
        'device_name': 'MI5S',
        'device_os': 'Android',
        'device_os_version': '6.0',
        'app_version': '5.9.0',
        'uidrole': 'boss',
        'utm_source': '2',
        'tinkerLoadedSuccess': 'false',
        'Host': 'app.chinahr.com',
        'Accept-Encoding': 'gzip',
        'Cookie': '; '.join([i[0]+'='+i[1] for i in cookie.items()]),
    }

    for x in range(3):
        try:
            response = requests.get(get_number_url, headers=get_number_headers, proxies=proxy, timeout=30)
            json_data = response.json()
            if json_data.get('code') in [0, '0']:
                result['code'] = 0
                result['coin_number'] = json_data.get('data', {}).get('chrCoinCount', 0)
            else:
                logger.info('get error get_download_beans_response '+ str(response.text))
                result['code'] = 1
            break
        except Exception, e:
            logger.info('get error times of get download_bean:'+str(x)+':'+str(e))
            result['code'] = 2
    return result


PHONES = ['15910286297','18310399539']
def send_sms(content):
    for phone in PHONES:
        url = "http://emg.mofanghr.com/inner/sms/send.json?traceID=10001&systemID=10001&params={'content': '%s','mobile': '%s'," \
              "'appKey': 'SMS_MONITOR'}" % (content,phone)
        logger.info('send message url is:'+url)
        res = requests.get(url)
        if res.status_code != 200:
            logger.info('send message failed, content is:%s'% content)

def test():
    login("P4e3wgtN5BXDsG5Wn0dGlQ", "Rmk2aiE9qK4", None, get_device())

if __name__ == '__main__':
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('./logs', 'obtain_point'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)

    # libtest = ctypes.CDLL("libChinahr.so")

    # libtest = cdll.LoadLibrary('libChinahr.so')
    # print libtest.encodeDes('18310399539')

    test()
    # origin_str = u'0123456789abcdefghijklmnopqrstuvwxyz?+ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # print origin_str.index(u'z')
    # print origin_str.index(u'U')
    # print origin_str.index(u'l')
    # print origin_str.index(u'g')

    # tmp_ch = None
    # index = 0
    # for ch in u'sbeg':
    #     index += 1
    #     if index % 2 == 0:
    #         sum = origin_str.index(tmp_ch) + origin_str.index(ch)
    #         print str(sum)[-1:]
    #     else:
    #         tmp_ch = ch



    # print u'abcdefghijklmnopqrstuvwxyz'.upper()
