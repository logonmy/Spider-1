#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

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
import os
import requests
import re
import random
import copy

# from ctypes import *
import ctypes

# logger = logging.getLogger()

logger = None
def get_logger():
    global logger
    if not logger:
        logger = logging.getLogger('')
        formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(threadName)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
        stream_handler = logging.StreamHandler()

        rotating_handler = logging.handlers.RotatingFileHandler(
            '%s/%s.log' % ('./logs', 'yifeng_zhilian'), 'a', 50 * 1024 * 1024, 100, None, 0)

        stream_handler.setFormatter(formatter)
        rotating_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(rotating_handler)
        logger.setLevel(logging.INFO)
    return logger

# def get_device():
#     a='1234567890'
#     b=[random.choice(a) for i in xrange(15)]
#     return ''.join(b)

def login(username, passwd, proxy, cookie):
    logger = get_logger()
    return_result = {'login_data': '', 'code': 0}
    logger.info('proxies is' + str(proxy))
    for i in range(3):
        logger.info('start login '+ str(username))
        try:
            get_account_url = 'http://www.yifengjianli.com/company/getAccountInfo'
            get_user_headers = {
                'Accept':'application/json, text/plain, */*',
                'Accept-Encoding':'gzip, deflate',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Host':'www.yifengjianli.com',
                'Origin':'http://www.yifengjianli.com',
                'Referer':'http://www.yifengjianli.com/cv/cvpool',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
                'Cookie': '; '.join([i[0]+'='+i[1] for i in cookie.items()]),
            }
            get_user_response = requests.post(get_account_url, headers=get_user_headers, proxies=proxy, timeout=30, data={})
            logger.info('=======================get_user_response.text:'+get_user_response.text)
            get_user_json = get_user_response.json()

            if get_user_response.status_code not in [200, '200'] or get_user_json['code'] not in [200, '200']:
                login_headers = {
                    'Accept':'application/json, text/plain, */*',
                    'Accept-Encoding':'gzip, deflate',
                    'Accept-Language':'zh-CN,zh;q=0.8',
                    'Content-Type':'application/x-www-form-urlencoded',
                    'Host':'www.yifengjianli.com',
                    'Origin':'http://www.yifengjianli.com',
                    'Referer':'http://www.yifengjianli.com/base/signin',
                    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
                }

                data = {
                    'status': '1',
                    'email': username,
                    'password': passwd,
                    # 'email': 'yangkun@mfwpkj.cn',
                    # 'password': 'Sjyz2015',
                }
                login_url = 'http://www.yifengjianli.com/user/userLogin'
                login_response = requests.post(login_url, data=data, headers=login_headers, proxies=proxy, timeout=30)
                json_data = login_response.json()
                logger.info('return result of login %s' % json_data)
                code = json_data.get('code')
                msg = json_data.get('message')
                data = json_data.get('user', {})
                if code in [200, '200']:
                    # cookie = dict(response.cookies)
                    # login_data = data
                    return_result['code'] = 0
                    # return_result['login_data'] = data
                else:
                    return_result['code'] = 1
                    continue
                cookie.update(dict(login_response.cookies))
                get_user_headers.update({'Cookie': '; '.join([i[0]+'='+i[1] for i in cookie.items()])})
                get_user_response = requests.post(get_account_url, headers=get_user_headers, proxies=proxy, timeout=30, data={})
                logger.info('=======================get_user_response2.text:'+get_user_response.text)
                get_user_json = get_user_response.json()
            if not get_user_json.get('accountMap', {}) or 'isSign' not in get_user_json.get('accountMap', {}):
                login.info('login error, continue')
                return_result['code'] = 3
                continue
            if get_user_json.get('accountMap', {}).get('isSign', 0):
                logger.info('today has obtaincoin')
            else:
                obtaincoin_url = 'http://www.yifengjianli.com/company/signLogs'
                obtaincoin_headers = {
                    'Accept':'application/json, text/plain, */*',
                    'Accept-Encoding':'gzip, deflate',
                    'Accept-Language':'zh-CN,zh;q=0.8',
                    'Host':'www.yifengjianli.com',
                    'Origin':'http://www.yifengjianli.com',
                    'Referer':'http://www.yifengjianli.com/userset/task',
                    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                    'Cookie': '; '.join([i[0]+'='+i[1] for i in cookie.items()]),

                }
                obtaincoin_response = requests.post(obtaincoin_url, headers=obtaincoin_headers, data={}, proxies=proxy, timeout=30)
                logger.info('=======================obtaincoin_response.text:'+obtaincoin_response.text)
                get_user_response = requests.post(get_account_url, headers=get_user_headers, proxies=proxy, timeout=30, data={})
                logger.info('=======================get_user_response3.text:'+get_user_response.text)
            return_result['login_data'] = get_user_response.json()['accountMap']
            return return_result
        except Exception, e:
            logger.info(str(traceback.format_exc()))
        
        logger.info(str(username) + ' login error times ' + str(i))
    return return_result

def get_zhilian_list(params, proxy, list_page, cookie):
    logger = get_logger()
    data = {
        'keyWord':'',
        'any':'false',
        'compName':'',
        'near':'false',
        'size':'',
        'jobStatus':'',
        'age':'',
        'hukou':'',
        'hukou_name':';',
        'address':'',
        'address_name':';',
        'schoolName':'',
        'majorName':'',
        'language':'',
        'language_name':';',
        'salary':'',
        'expSalary':'',
        'expIndustry':'',
        'expIndustry_name':';',
        'expJob':'2070000',
        'expJob_name':'',
        'expcity':'',
        'expcity_name':'',
        'expWorkPro':'',
        'skill':'',
        'skill_name':';',
        'overseas':'',
        'management':'',
        'nature':'',
        'jobName':'',
        'jobName_name':';',
        'industry':'',
        'industry_name':';',
        'jobYear':'',
        'education':'5,7',
        'sex':'',
        'updateTime':'1,9',
        'havePhoto':'',
        'showLanguage':'',
        'orderBy':'',
        'pageIndex':'1',
        'pageSize':'',
        'exclude':'',
        'selectShowConditon':'currentIndustry,updateTime,workExperience,education,currentCity,age,sex,expectJob,expectCity',
        'selectShowConditonId':'3;7;4;5;6;8;9;17;18',
        'zl_userId':'',
        'currentSource':'0',
    }
    params_copy = copy.copy(params)
    params_copy.pop('page_now')
    data.update(params_copy)
    data['pageIndex'] = list_page
    for x in xrange(5):
        try:
            get_number_url = 'http://www.yifengjianli.com/zlresume/zlResuSearch'
            # get_number_url = 'https://app.chinahr.com/cvapp/search?keyword=%s&live=%s&workExp=0&degree=%s&reFreshTime=%s&page=%s&searchType=' % (params['keyword'], params['live'], params['degree'], params['refreshTime'], list_page)
            get_number_headers = {
                'Accept':'application/json, text/plain, */*',
                'Accept-Encoding':'gzip, deflate',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Content-Type':'application/x-www-form-urlencoded',
                'Host':'www.yifengjianli.com',
                'Origin':'http://www.yifengjianli.com',
                'Referer':'http://www.yifengjianli.com/userset/superPoolZL?form=checkSession&cid='+str(int(time.time())*1000)+'&ipCheck=1&resumeCode=&cu=userId&bv=Mozilla/5.0%20(Windows%20NT%206.1;%20WOW64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/57.0.2987.133%20Safari/537.36',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
                'Cookie': '; '.join([i[0]+'='+i[1] for i in cookie.items()]),
            }
            response = requests.post(get_number_url, headers=get_number_headers, proxies=proxy, timeout=30, data=data)
            cookie.update(dict(response.cookies))
            json_data = response.json()
            if json_data.get('code', -1) in [200, '200']:
                return json_data
            else:
                pass
        except Exception, e:
            logger.info('error '+ str(x)+ ' times of download list '+str(params)+' '+ str(list_page))
        return {'code': -1}

def get_yifeng_list(params, proxy, list_page, cookie):
    logger = get_logger()
    data = {
        'page':'1',
        'pageSize':'20',
        'searches':'',
        'sex':'',
        'education':'',
        'startYear':'0',
        'endYear':'30',
        'salary':'',
        'updateTime':'1',
        'jobState':'',
        'city':'530',
        'job':'4010200',
        'startAge':'',
        'endAge':'30',
        'companyName':'',
        'latelyCompName':'',
        'endEducation':'',
        'jobType':'1',
    }
    params_copy = copy.copy(params)
    params_copy.pop('page_now')
    data.update(params_copy)
    data['page'] = list_page
    for x in xrange(5):
        try:
            get_number_url = 'http://www.yifengjianli.com/cv/getResumePoolList'
            # get_number_url = 'https://app.chinahr.com/cvapp/search?keyword=%s&live=%s&workExp=0&degree=%s&reFreshTime=%s&page=%s&searchType=' % (params['keyword'], params['live'], params['degree'], params['refreshTime'], list_page)
            get_number_headers = {
                'Accept':'application/json, text/plain, */*',
                'Accept-Encoding':'gzip, deflate',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Content-Type':'application/x-www-form-urlencoded',
                'Host':'www.yifengjianli.com',
                'Origin':'http://www.yifengjianli.com',
                'Referer':'http://www.yifengjianli.com/cv/cvpool',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
                'Cookie': '; '.join([i[0]+'='+i[1] for i in cookie.items()]),
            }
            response = requests.post(get_number_url, headers=get_number_headers, proxies=proxy, timeout=30, data=data)
            cookie.update(dict(response.cookies))
            json_data = response.json()
            if json_data.get('code', -1) in [200, '200']:
                return json_data
            # else:
            #     pass
        except Exception, e:
            logger.info('error '+ str(x)+ ' times of download list '+str(params)+' '+ str(list_page))
        return {'code': -1}

def get_yifeng_resume(userid, proxy, cookie):
    logger = get_logger()
    result = {'code': 0}
    # if not proxy:
    #     logger.info('there has no proxy in resume, return!!!')
    #     result['code'] = 5
    #     return result
    if not userid:
        logger.info('there has no userid in resume, return!!!')
        result['code'] = 2
        return result

    try:
        # gain_url = 'http://www.yifengjianli.com/company/gainResume'
        # gain_header = {
        #     'Accept':'application/json, text/plain, */*',
        #     'Accept-Encoding':'gzip, deflate',
        #     'Accept-Language':'zh-CN,zh;q=0.8',
        #     'Content-Type':'application/x-www-form-urlencoded',
        #     'Cookie':'; '.join([i[0]+'='+i[1] for i in cookie.items()]),
        #     'Host':'www.yifengjianli.com',
        #     'Origin':'http://www.yifengjianli.com',
        #     'Referer':'http://www.yifengjianli.com/cv/cvbid?userId=%s' % userid,
        #     'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        # }
        # gain_data = {
        #     'userId': userid,
        # }
        # gain_response = requests.post(gain_url, data=gain_data, headers=gain_header, allow_redirects=False, proxies=proxy, timeout=30)
        # gain_json = gain_response.json()
        # result.update(gain_json)
        # # if gain_json.get('code', '') not in [200, '200']:
        # #     logger.info('did not get 200 when gain resume!!!')
        # #     result.update(gain_json)
        # #     return result
        # # download the info page



        get_resume_url = 'http://www.yifengjianli.com/bidme/getUserResume'
        get_resume_header = {
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/x-www-form-urlencoded',
            'Host':'www.yifengjianli.com',
            'Origin':'http://www.yifengjianli.com',
            'Referer':'http://www.yifengjianli.com/cv/cvbid?userId=%s&keyword=' % userid,
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Cookie':'; '.join([i[0]+'='+i[1] for i in cookie.items()]),
        }
        get_resume_data = {
            'userId': userid,
        }
        get_resume_response = requests.post(get_resume_url, data=get_resume_data, headers=get_resume_header, allow_redirects=False, proxies=proxy, timeout=30)
        get_resume_json = get_resume_response.json()
        result.update(get_resume_json)
        # if gain_json.get('code', '') not in [200, '200']:
        #     logger.info('did not get 200 when gain resume!!!')
        #     result.update(gain_json)
        #     return result
        # download the info page
        
    except Exception, e:
        logger.info('unkown error'+str(traceback.format_exc()))
        result['code']=4
    return result

def get_zhilian_resume(params_str, proxy, cookie):
    logger = get_logger()
    result = {'code': 0}
    # if not proxy:
    #     logger.info('there has no proxy in resume, return!!!')
    #     result['code'] = 5
    #     return result
    if not params_str:
        logger.info('there has no params_str in resume, return!!!')
        result['code'] = 2
        return result
    params_list = params_str.split('&')
    params_dict = {}
    for i in params_list[1:]:
        i_list = i.split('=')
        params_dict[i_list[0]] = '='.join(i_list[1:])

    try:
        getresu_url = 'http://www.yifengjianli.com/zlresume/zlResuDetail'
        getresu_header = {
            'Accept':'application/json, text/plain, */*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/x-www-form-urlencoded',
            'Host':'www.yifengjianli.com',
            'Origin':'http://www.yifengjianli.com',
            # 'Referer':'http://www.yifengjianli.com/zlresume/resumedetail?url=%s&city=%s&searchId=%s&keyword=&ipCheck=1&resumeCode=&activePage=zl&replacePage=zl' % (params_str, city, resume.get('searchId', '')),
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Cookie':'; '.join([i[0]+'='+i[1] for i in cookie.items()]),
        }
        getresu_data = {
            'key': params_list[0].split('?')[0],
            'time':params_dict.get('t', ''),
            'r':params_dict.get('k', ''),
            'ipCheck':'1',
            'resumeCode':'',
        }
        logger.info('getresu_data:'+str(getresu_data))
        getresu_response = requests.post(getresu_url, data=getresu_data, headers=getresu_header, allow_redirects=False, proxies=proxy, timeout=30)
        cookie.update(dict(getresu_response.cookies))
        getresu_json = getresu_response.json()
        result.update(getresu_json)
        # if gain_json.get('code', '') not in [200, '200']:
        #     logger.info('did not get 200 when gain resume!!!')
        #     result.update(gain_json)
        #     return result
        # download the info page
        
    except Exception, e:
        logger.info('unkown error'+str(traceback.format_exc()))
        result['code']=4
    return result

def test():
    get_resume()

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
