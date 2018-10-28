#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 0003 15:41
# @Author  : huangyee
# @Email   : 1173842904@qq.com
# @File    : login_test.py
# @Software: PyCharm
import sys
import os
import logging
import json
import requests
import settings
import logging.handlers

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
current_file_name = os.path.basename(__file__)
logger = logging.getLogger()


def login(username, password):
    # 3
    login_url = 'http://www.jianlika.com/Index/login.html'
    post_data = {
        'username': username,
        'password': password,
        'remember': 'no'
    }
    login_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'think_language=zh-CN; user_auth_sign=8rc593c82ogfc55938595vsc14; rememberUsername=18629947965; gift_hide_timeout=1',
        'Host': 'www.jianlika.com',
        'Origin': 'http://www.jianlika.com',
        'Referer': 'http://www.jianlika.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    response = requests.post(url=login_url, data=post_data, headers=login_header, proxies=settings.get_proxy())
    # 登录完成之后，返回的内容为：'{"info":"","status":1,"url":"\\/Search"}'
    # print response.proxies
    print response.content
    print 'cookie：===》》》 %s ' % response.headers.get('Set-Cookie')
    pass


def process():
    login('18629947965', 'l56441193')
    pass


if __name__ == '__main__':
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('/data/logs', 'login_test'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)
    process()
    pass
