#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
import os
import traceback
import uuid

import oss2
import requests

import settings

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append('../common')
import utils as common_utils

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
"""
@version: python2.7
@author: 王增帅
@contact: 549409587@qq.com
@software: PyCharm
@file: inbox_utils.py
@time: 2017/5/10 17:26
"""


class ResumeRaw:
    """
    简历原文对象
    """
    def __init__(self):
        self.source = None
        self.id = None
        self.email = None
        self.subject = None
        self.content = None
        self.processStatus = None
        self.parsedTime = None
        self.reason = None
        self.resumeUpdateTime = None
        self.resumeSubmitTime = None
        self.emailJobType = None
        self.emailCity = None
        self.avatarUrl = None
        self.ip = None
        self.createTime = None
        self.createBy = None
        self.trackId = None

    def to_dict(self):
        dict = {}
        if self.id:
            dict['id'] = self.id
        if self.source:
            dict['source'] = self.source
        if self.email:
            dict['email'] = self.email
        if self.subject:
            dict['subject'] = self.subject
        if self.content:
            dict['content'] = self.content
        if self.processStatus:
            dict['processStatus'] = self.processStatus
        if self.parsedTime:
            dict['parsedTime'] = self.parsedTime
        if self.reason:
            dict['reason'] = self.reason
        if self.resumeUpdateTime:
            dict['resumeUpdateTime'] = self.resumeUpdateTime
        if self.resumeSubmitTime:
            dict['resumeSubmitTime'] = self.resumeSubmitTime
        if self.emailJobType:
            dict['emailJobType'] = self.emailJobType
        if self.emailCity:
            dict['emailCity'] = self.emailCity
        if self.avatarUrl:
            dict['avatarUrl'] = self.avatarUrl
        if self.ip:
            dict['ip'] = self.ip
        if self.createTime:
            dict['createTime'] = self.createTime
        if self.createBy:
            dict['createBy'] = self.createBy
        if self.trackId:
            dict['trackId'] = self.trackId

        return dict


def get_account(username):
    """
    获取含有cookie的帐号
    :param username:
    :return: dict{}
    """
    if not username:
        return None
    account_dict = common_utils.get_account(username)
    dict_get = account_dict.get('cookie', '')
    if not dict_get:
        return None
    cookie_list = json.loads(dict_get)
    cookie_str = ''
    for cookie in cookie_list:
        mid = cookie.get('name') + '=' + cookie.get('value') + '; '
        cookie_str += mid
        cookie_str += '51job=cenglish%3D0; '
    cookie_str += 'adv=adsnew%3D0%26%7C%26adsresume%3D1%26%7C%26adsfrom%3Dhttp%253A%252F%252Fbzclk.baidu.com%252Fadrc.php%253Ft%253D06KL00c00fAjOKR07edR00uiAs0IoyPm00000rRPIH300000I1hgBF.THLZ_Q5n1VeHksK85yF9pywdpAqVuNqsusK15Hbzmhm1P1mknj0snjF-mH00IHY3nRDvfWnLPjnYn1fvnY7Dnjb1wj7anYR3wjIKnH64n0K95gTqFhdWpyfqnW6YnjnvPjbvriusThqbpyfqnHm0uHdCIZwsrBtEIZF9mvR8PH7JUvc8mvqVQLwzmyP-QMKCTjq9uZP8IyYqP164nWn1Fh7JTjd9i7csmYwEIbs1ujPbXHfkHNIsI--GPyGBnWKvRjFpXycznj-uURusyb9yIvNM5HYhp1YsuHDdnWfYnhf3mhn4PHK-PHbvmhnYPWD4mvm4nAuhm6KWThnqn1fsPWc%2526tpl%253Dtpl_10085_14394_1%2526l%253D1047858661%2526wd%253D%2525E5%252589%25258D%2525E7%2525A8%25258B%2525E6%252597%2525A0%2525E5%2525BF%2525A7%2526issp%253D1%2526f%253D8%2526ie%253Dutf-8%2526rqlang%253Dcn%2526tn%253Dbaiduhome_pg%2526inputT%253D2097%26%7C%26adsnum%3D789233; adv=adsnew%3D0%26%7C%26adsresume%3D1%26%7C%26adsfrom%3Dhttp%253A%252F%252Fbzclk.baidu.com%252Fadrc.php%253Ft%253D06KL00c00fAjOKR07edR00uiAs0mNG-m00000rRPIH300000I1hgBc.THYdnyGEm6K85yF9pywd0Znquj9BmyNBPHmsnj01PhcYnfKd5H6kfHuan1TYn1f1Pjm1fRfsrHPDnRc1wH9DPYDkrjbs0ADqI1YhUyPGujYzrjfsn1mYrHm4FMKzUvwGujYkP6K-5y9YIZ0lQzqYTh7Wui3dnyGEmB4WUvYEIZF9mvR8TA9s5v7bTv4dUHYLrjbzn1nhmyGs5y7cRWKWwAqvHjPbnvw4Pj7PNLKvyybdphcznZufn-G4mWcsrN-VwMKpi7uLuyTq5iuo5HK-nHRzPjfzuj9Bm1bdnARdrHuBm1fvnH-WuWbsuhuB0APzm1Ydrjc4n0%2526tpl%253Dtpl_10085_14394_1%2526l%253D1047858661%2526ie%253Dutf-8%2526f%253D3%2526tn%253Dbaidu%2526wd%253D51job%2526rqlang%253Dcn%2526prefixsug%253D51%2526rsp%253D3%2526inputT%253D3067%26%7C%26adsnum%3D789233;'
    account_dict['cookie'] = cookie_str.encode()

    return account_dict


def get_headers(refer_url=None):
    if refer_url:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Referer": refer_url
        }
    else:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8"
        }

    return headers


def save_mobile_imgs_to_oss(img_url, retry, trackId, headers=None):
    """
    连接获取电话图片保存oss
    :return:
    """
    logger = common_utils.get_logger()
    logger.error("准备连接电话图片: %s" % trackId)
    if retry <= 0:
        return None
    try:
        r = requests.get(img_url, proxies=common_utils.get_proxy(), timeout=8)
    except Exception as e:
        logger.error(e)
        logger.error("连接电话图片异常: %s 重试" % trackId)
        return save_mobile_imgs_to_oss(img_url, retry - 1, trackId)

    # 存储oss
    logger.error("准备存储oss: %s " % trackId)
    auth = oss2.Auth('LTAIa3y58SBV0Kyn', 'yBZcBKhQTgtf4cV55ljpnNCSk1XWaI')
    bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'ocr-img')
    # oss_api = OssAPI('http://oss-cn-beijing.aliyuncs.com', 'LTAIa3y58SBV0Kyn', 'yBZcBKhQTgtf4cV55ljpnNCSk1XWaI')
    oss_addr = 'spider/FIVE_ONE/RESUME_INBOX/' + str(uuid.uuid1()) + '.jpg'
    try:
        # oss_api.put_object('ocr-img', r, oss_addr)
        bucket.put_object(oss_addr, r)
    except Exception as e:
        logger.error(traceback.format_exc())
        return save_mobile_imgs_to_oss(img_url, retry - 1, trackId)

    return oss_addr


def invalid_account(account):
    logger = common_utils.get_logger()
    account_url = settings.INVALID_ACCOUNT_URL + 'userName=%s&password=%s' % (
        account.get('userName'), account.get('password'))
    account_result = common_utils.download(url=account_url, is_json=True)
    logger.info('cookies失效,帐号重新登录请求发送成功 %s', account_result.get('data', ''))
