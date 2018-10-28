#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 0003 14:54
# @Author  : huangyee
# @Email   : 1173842904@qq.com
# @File    : resume_test.py
# @Software: PyCharm
import sys
import os
import logging
import requests
import uuid
import json
import time
import traceback
import resume_jianlika

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
current_file_name = os.path.basename(__file__)
logger = logging.getLogger()
sys.path.append('../common')
import utils


def process():
    detail_urls = [
        #  '/Resume/view/token/a70c3ac1.html', '/Resume/view/token/e4436f8e.html',
        # '/Resume/view/token/fccffd60.html', '/Resume/view/token/fcde9799.html',
        # '/Resume/view/token/07be20f2.html', '/Resume/view/token/7279dbc7.html',
        # '/Resume/view/token/e3060892.html', '/Resume/view/token/dc6713c1.html',
        # '/Resume/view/token/afc11329.html', '/Resume/view/token/e0f370b5.html',
        # '/Resume/view/token/0b95afc7.html', '/Resume/view/token/ec611af0.html',
        # '/Resume/view/token/decfe7a3.html', '/Resume/view/token/5e79e367.html',
        # '/Resume/view/token/9d332a03.html', '/Resume/view/token/e0bb5f00.html',
        # '/Resume/view/token/db3e486e.html', '/Resume/view/token/38e7634a.html',
        # '/Resume/view/token/eb430f14.html', '/Resume/view/token/4bb74b6a.html',
        # '/Resume/view/token/df99f625.html', '/Resume/view/token/1f4b81ee.html',
        # '/Resume/view/token/2e4f2028.html', '/Resume/view/token/a496a8c9.html',
        # '/Resume/view/token/9582519b.html'
        # '/Resume/view/token/b4e7be8c.html', '/Resume/view/token/efe20ce3.html', '/Resume/view/token/23942f99.html',
        # '/Resume/view/token/7522d069.html', '/Resume/view/token/912cda6d.html', '/Resume/view/token/ece8a16f.html',
        # '/Resume/view/token/8076a17f.html', '/Resume/view/token/920b76ab.html', '/Resume/view/token/885c87ac.html',
        # '/Resume/view/token/c0fadb99.html', '/Resume/view/token/5509f242.html', '/Resume/view/token/79be976c.html',
        # '/Resume/view/token/aa30d655.html', '/Resume/view/token/490f4692.html', '/Resume/view/token/69a7264b.html',
        # '/Resume/view/token/3b644a55.html', '/Resume/view/token/432375dc.html', '/Resume/view/token/95db2f64.html',
        # '/Resume/view/token/56ee81a7.html', '/Resume/view/token/287cf605.html', '/Resume/view/token/827d4fa0.html',
        # '/Resume/view/token/19512257.html', '/Resume/view/token/58489cdf.html', '/Resume/view/token/54797cdb.html',
        # '/Resume/view/token/9327bc89.html'
        '/Resume/view/token/1d358629.html', '/Resume/view/token/663ef7c2.html', '/Resume/view/token/c777ade5.html',
        '/Resume/view/token/38f3081b.html', '/Resume/view/token/51350834.html', '/Resume/view/token/27bbea65.html',
        '/Resume/view/token/0116acdb.html', '/Resume/view/token/b88098f8.html', '/Resume/view/token/f96b3ec5.html',
        '/Resume/view/token/c848b4bc.html', '/Resume/view/token/26312da3.html', '/Resume/view/token/75322dc8.html',
        '/Resume/view/token/0f816ded.html', '/Resume/view/token/7548d41e.html', '/Resume/view/token/b96b3d76.html',
        '/Resume/view/token/75905a26.html', '/Resume/view/token/7834072d.html', '/Resume/view/token/89dc5ad0.html',
        '/Resume/view/token/b3192397.html', '/Resume/view/token/6f142114.html', '/Resume/view/token/4f9bd2bb.html',
        '/Resume/view/token/ad60e505.html', '/Resume/view/token/81a20010.html', '/Resume/view/token/aa3e4b20.html',
        '/Resume/view/token/8922ba07.html'
    ]
    for url in detail_urls:
        time.sleep(3)
        detail_url = 'http://www.jianlika.com' + url
        detail_header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip:deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
            'Cache-Control': 'max-age=0',
            'Cookie': 'rememberUsername=18629947965; gift_hide_timeout=1; think_language=zh-CN; user_auth_sign=bu92err0om7cjmmv44sv9mo9h5; search_list_mode=full',
            'Host': 'www.jianlika.com',
            'Proxy-Connection': 'keep-alive',
            'Referer': 'http://www.jianlika.com/Search/result/token/7d9903888fe00e1acc6f2d67856a3a62.html',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML:like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        }
        detail_content = requests.get(url=detail_url, headers=detail_header).content
        resume_uuid = uuid.uuid1()
        try:
            content = json.dumps({'name': '', 'email': '', 'phone': '', 'html': detail_content},
                                 ensure_ascii=False)
            sql = 'insert into spider_search.resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values (%s, %s, "python", %s, now(), %s, %s, %s, %s)'
            sql_value = ('RESUME_KA', content, resume_uuid, '18629947965', '销售',
                         '北京', '')

            resume_update_time = ''
            # resume_update_time =  resume_result['json']['updateDate']
            kafka_data = {
                "channelType": "WEB",
                "content": {
                    "content": content,
                    "id": '',
                    "createBy": "python",
                    "createTime": int(time.time() * 1000),
                    "ip": '',
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": resume_update_time,
                    "source": 'RESUME_KA',
                    "trackId": str(resume_uuid),
                    "avatarUrl": '',
                    "email": '18629947965',
                    'emailJobType': '客服',
                    'emailCity': '北京',
                    'subject': ''
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_SEARCH",
                "source": 'RESUME_KA',
                "trackId": str(resume_uuid),
                'traceID': str(resume_uuid),
                'callSystemID': 'python',
            }
            utils.save_data(sql, sql_value, kafka_data)
        except Exception, e:
            logger.info('get error when write mns, exit!!!' + str(traceback.format_exc()))
            # return
    pass


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
    cookie = 'gift_hide_timeout=1; AWSELB=4B9B4BE516A95C5CEC852C0DFA15D4E95B0DF84E43ABD0E3E867DF4A41D7C97A3E4321B6AD083CC33CEF2345183B0208E7613A0665994376C81E292BDA81FBD4A05045A034; think_language=zh-CN; PHPSESSID=3mt68rpaf839o7j9hs7oo30o14'
    task = {'areas': '110000', 'hJobs': '56', 'keywords': u'销售', 'areas_name': u'北京'}
    token = '5e96775c55f137f76e3d14f1e6d1189f'
    print get_coin_number(cookie, None)
    # print awake_one_task(task)
    # print get_list(cookie, 2, token, task, None)
    # print get_list(cookie, 1, token, task, None)
    # print get_list_with_keyword(cookie, 1, token, task, None)
    # a=  get_resume('http://www.jianlika.com/Resume/view/token/1ff18ddd.html', cookie)
    # a = get_resume_has_real_rid('2567308023', '117659691', cookie)
    # a = charge_resume('a0ee5mmk0e', cookie)
    # f=open('123', 'w')
    # f.write(json.dumps(a, ensure_ascii=False))
    # f.close()

if __name__ == '__main__':
    utils.set_setting([])
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('/data/logs', 'resume_test'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)

    # cookie
    cookie = 'think_language=zh-CN; user_auth_sign=8rc593c82ogfc55938595vsc14; rememberUsername=18629947965'
    # 详情页面url
    get_resume_url3 = 'http://www.jianlika.com' + '/Resume/view/token/57f038fc.html'
    data = resume_jianlika.get_resume(get_resume_url=get_resume_url3, cookie=cookie)
    logger.info('%s' % str(data.get('data')).encode('utf-8'))
    process()
    pass
