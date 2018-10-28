#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import sys
import traceback
import urllib
import uuid

import time

import inbox_utils
from inbox_utils import ResumeRaw

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
import utils as common_utils

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
"""
@version: python2.7
@author: 王增帅
@contact: 549409587@qq.com
@software: PyCharm
@file: five_one_inbox_spider.py
@time: 2017/4/24 13:40
"""
import requests
import lxml.html as xmlh

logger = None
proxy = None


def conn_html(account, url, retry, refer_url=None, track_id=None):
    """
    连接搜索列表
    :return:
    """
    global proxy
    logger.info("开始连接 %s , 重试次数 %s" % (url, retry))
    if retry <= 0:
        return None
    headers = inbox_utils.get_headers(refer_url)
    # headers['Cookie'] = account['cookie']
    # r = requests.get(url, headers=headers, timeout=10)
    r = common_utils.download(url=url, headers=headers, cookie=account['cookie'], proxy=proxy)

    if r.get("code") != 0:
        logger.error("列表页面返回不正常 data= %s" % r.get('data'))
        if r.get('data') and '<a href="/MainLogin.aspx?returl=' in r['data']:
            return 'login'
        proxy = common_utils.get_proxy()
        return conn_html(account, url, retry - 1, refer_url, track_id)
    if '<a href="/MainLogin.aspx?returl=' in r['data']:
        return 'login'

    return r.get('data')


def parse_list_html(list_html, removeIds=None, track_id=None):
    """
    解析获取需要下载的简历(去重),
    :return:
    """
    tree = xmlh.document_fromstring(list_html)
    title = tree.xpath('//*[@id="Head1"]/title/text()')
    if title:
        if '人才招聘-前程无忧 | 51job 网才' in title[0]:
            return 'refer-login'

    none_ = tree.xpath('//span[@id="lblNodata"]')
    if not none_:
        return 'none'
    inputs = tree.xpath('//input[@id="chkBox"]')
    if inputs:
        list = []
        for input in inputs:
            list.append(input.attrib['value'])

    return list


def parse_info_html(account, info_html, track_id):
    """
    组织raw对象
    :return:
    """
    raw = ResumeRaw()
    raw.trackId = track_id
    raw.source = 'FIVE_ONE'
    raw.content = info_html
    raw.email = account['userName']

    tree = xmlh.document_fromstring(info_html)
    img_url = common_utils.find('.*?(/Candidate/ReadAttach.aspx\?UserID=\\d+).*?', info_html)

    try:
        submit_times = common_utils.find('投递时间：<span class="blue_txt">(.*?)</span>', info_html)
        if submit_times:
            raw.resumeSubmitTime = submit_times
        update_times = tree.xpath('//*[@id="lblResumeUpdateTime"]/text()')
        if update_times:
            raw.resumeUpdateTime = str(update_times[0])
    except Exception as e:
        logger.error(e.message)

    if img_url:

        url = "http://ehire.51job.com/" + img_url
        oss_addr = inbox_utils.save_mobile_imgs_to_oss(url, 2, track_id)
        if oss_addr:
            raw.avatarUrl = oss_addr
    return raw


# def insert_to_db(raw, track_id):
#     """保存数据库"""
#     logger.info("准备入库: %s" % track_id)
#     mysql = mysql_utils.Mysql()
#     sql = 'INSERT INTO resume_raw (' \
#           'trackId,source,content,createTime,createBy,email,resumeUpdateTime,resumeSubmitTime' \
#           ') values(%s, "FIVE_ONE",%s, now(), "python", %s, %s, %s)'
#     value = (raw.trackId, raw.content, raw.email, raw.resumeUpdateTime, raw.resumeSubmitTime)
#     try:
#         raw_id = mysql.insertOne(sql, value)
#         logger.info('入库成功 rawId= %d' % raw_id)
#         raw.id = raw_id
#     except Exception as e:
#         logger.error("58-raw-入库失败 %s" % track_id)
#         logger.error(e)
#     finally:
#         mysql.end()
#
#
# def send_to_kafka(raw):
#     """
#     发送至kafka
#     :return:
#     """
#     logger.info("准备推送kafka %s" % raw.trackId)
#     raw_data = json.dumps(raw, ensure_ascii=False, default=serialize_instance)
#     data = ResourceData(raw.trackId, raw_data)
#     try:
#         kafka_data = json.dumps(data, ensure_ascii=False, default=serialize_instance)
#         spider_utils.send_kafka(kafka_data)
#         print  kafka_data
#         logger.info("推送kafka %s 完毕" % raw.trackId)
#     except Exception as e:
#         logger.info("推送kafka %s 失败" % raw.trackId)
#         logger.error(e.message)


def info_main(account, info_url, track_id):
    """
    简历详情页主方法
    :return: True : 正常入库...  , False : 出现异常
    """
    # info_url = "http://ehire.51job.com/Candidate/ResumeViewFolder.aspx?hidSeqID=9216079958&hidFolder=EMP"
    refer_url = "http://ehire.51job.com/Inbox/InboxRecentEngine.aspx?Style=1"
    info_html = conn_html(account, info_url, 4, refer_url=refer_url, track_id=track_id)
    if 'login' == info_html:
        logger.error("出现登录页面 %s" % account['userName'])
        return 'login'

    if info_html:
        logger.info('获取一条收件箱简历成功!')
        raw = parse_info_html(account, info_html, track_id)
        sql = 'INSERT INTO resume_raw (' \
              'trackId,source,content,createTime,createBy,email,resumeUpdateTime,resumeSubmitTime' \
              ') values(%s, "FIVE_ONE",%s, now(), "python", %s, %s, %s)'
        value = (raw.trackId, raw.content, raw.email, raw.resumeUpdateTime, raw.resumeSubmitTime)
        kafka_data = {
            'trackId': raw.trackId,
            'source': raw.source,
            "channelType": 'WEB',
            'resourceType': 'RESUME_INBOX',
            'resourceDataType': 'RAW',
            'content': raw.to_dict(),
            'protocolType': 'HTTP'
        }
        logger.info('开始保存一份收件箱简历')
        common_utils.save_data(sql, value, kafka_data)
        return True
    else:
        logger.info('获取一条收件箱简历失败!')
        return False


def get_refer_data(resume_ids, __VIEWSTATE, hidEngineCvlogIds):
    chkBox = ''
    for id in resume_ids:
        chkBox += 'chkBox=' + id + '&'
    hidSeqID = ''
    for id in resume_ids:
        hidSeqID += id
        hidSeqID += ','
    hidSeqID = hidSeqID[:-1]

    data = "__EVENTTARGET=btnRecycle%24btnRecycle&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=" + urllib.quote(
        __VIEWSTATE) + "&hidTab=&ctrlSerach%24ddlSearchName=&ctrlSerach%24dropCoid=&ctrlSerach%24dropDivision=&ctrlSerach%24hidSearchID=1%2C2%2C3%2C4%2C5%2C6%2C7%2C8%2C9&ctrlSerach%24KEYWORD=--%E5%8F%AF%E9%80%89%E6%8B%A9%E2%80%9C%E5%B7%A5%E4%BD%9C%E3%80%81%E9%A1%B9%E7%9B%AE%E3%80%81%E8%81%8C%E5%8A%A1%E3%80%81%E5%AD%A6%E6%A0%A1%E2%80%9D%E5%85%B3%E9%94%AE%E5%AD%97--&ctrlSerach%24KEYWORDTYPE=1&ctrlSerach%24AREA%24Text=%E9%80%89%E6%8B%A9%2F%E4%BF%AE%E6%94%B9&ctrlSerach%24AREA%24Value=&ctrlSerach%24SEX=2&ctrlSerach%24TopDegreeFrom=&ctrlSerach%24TopDegreeTo=&ctrlSerach%24WORKFUN1%24Text=%E9%80%89%E6%8B%A9%2F%E4%BF%AE%E6%94%B9&ctrlSerach%24WORKFUN1%24Value=&ctrlSerach%24WORKINDUSTRY1%24Text=%E9%80%89%E6%8B%A9%2F%E4%BF%AE%E6%94%B9&ctrlSerach%24WORKINDUSTRY1%24Value=&ctrlSerach%24WorkYearFrom=0&ctrlSerach%24WorkYearTo=99&ctrlSerach%24TOPMAJOR%24Text=%E9%80%89%E6%8B%A9%2F%E4%BF%AE%E6%94%B9&ctrlSerach%24TOPMAJOR%24Value=&ctrlSerach%24AgeFrom=&ctrlSerach%24AgeTo=&ctrlSerach%24txtUserID=-%E5%A4%9A%E4%B8%AA%E7%AE%80%E5%8E%86ID%E7%94%A8%E7%A9%BA%E6%A0%BC%E9%9A%94%E5%BC%80-&ctrlSerach%24txtMobile=&ctrlSerach%24txtName=&ctrlSerach%24txtMail=&ctrlSerach%24hidTwoValue=&ctrlSerach%24radFandF=0&ctrlSerach%24txtSearchName=&dropRecentResumeRange=14&" + chkBox + "pagerBottom%24txtGO=1&cbxColumns%240=LABELID&cbxColumns%242=AGE&cbxColumns%244=TOPDEGREE&cbxColumns%245=WORKYEAR&cbxColumns%2416=SENDDATE&Keyword1=&1=SortAsc1&Keyword2=&2=SortAsc2&Keyword3=&3=SortAsc3&hidShowCode=0&inboxTypeFlag=5&ShowFrom=1&hidEvents=&hidSeqID=" + hidSeqID + "&hidUserID=&hidFolder=EMP&BAK2INT=&hidJobID=&SubmitValue=&hidDisplayType=0&hidOrderByCol=&hidSearchHidden=&hidBatchBtn=&hidProcessType=&hidEngineCvlogIds=" + urllib.quote(
        hidEngineCvlogIds) + "&hidUserDistinct=0"

    data = {
        '__EVENTTARGET': 'btnRecycle$btnRecycle',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': __VIEWSTATE,
        'hidTab': '',
        'ctrlSerach$ddlSearchName': '',
        'ctrlSerach$dropCoid': '',
        'ctrlSerach$dropDivision': '',
        'ctrlSerach$hidSearchID': '1,2,3,4,5,6,7,8,9',
        'ctrlSerach$KEYWORD': '--可选择“工作、项目、职务、学校”关键字--',
        'ctrlSerach$KEYWORDTYPE': '1',
        'ctrlSerach$AREA$Text': '选择/修改',
        'ctrlSerach$AREA$Value': '',
        'ctrlSerach$SEX': '2',
        'ctrlSerach$TopDegreeFrom': '',
        'ctrlSerach$TopDegreeTo': '',
        'ctrlSerach$WORKFUN1$Text': '选择/修改',
        'ctrlSerach$WORKFUN1$Value': '',
        'ctrlSerach$WORKINDUSTRY1$Text': '选择/修改',
        'ctrlSerach$WORKINDUSTRY1$Value': '',
        'ctrlSerach$WorkYearFrom': '0',
        'ctrlSerach$WorkYearTo': '99',
        'ctrlSerach$TOPMAJOR$Text': '选择/修改',
        'ctrlSerach$TOPMAJOR$Value': '',
        'ctrlSerach$AgeFrom': '',
        'ctrlSerach$AgeTo': '',
        'ctrlSerach$txtUserID': '-多个简历ID用空格隔开-',
        'ctrlSerach$txtMobile': '',
        'ctrlSerach$txtName': '',
        'ctrlSerach$txtMail': '',
        'ctrlSerach$hidTwoValue': '',
        'ctrlSerach$radFandF': '0',
        'ctrlSerach$txtSearchName': '',
        'dropRecentResumeRange': '14',
        'pagerBottom$txtGO': '1',
        'cbxColumns$0': 'LABELID',
        'cbxColumns$2': 'AGE',
        'cbxColumns$4': 'TOPDEGREE',
        'cbxColumns$5': 'WORKYEAR',
        'cbxColumns$16': 'SENDDATE',
        'Keyword1': '',
        '1': 'SortAsc1',
        'Keyword2': '',
        '2': 'SortAsc2',
        'Keyword3': '',
        '3': 'SortAsc3',
        'hidShowCode': '0',
        'inboxTypeFlag': '5',
        'ShowFrom': '1',
        'hidEvents': '',
        'hidSeqID': hidSeqID,
        'hidUserID': '',
        'hidFolder': 'EMP',
        'BAK2INT': '',
        'hidJobID': '',
        'SubmitValue': '',
        'hidDisplayType': '0',
        'hidOrderByCol': '',
        'hidSearchHidden': '',
        'hidBatchBtn': '',
        'hidProcessType': '',
        'hidEngineCvlogIds': hidEngineCvlogIds,
        'hidUserDistinct': '0'
    }

    return data


def refer_list_html(account, data, retry):
    """
    刷新下一页
    :param resume_ids:
    :param retry:
    :return: 刷新后的列表页面
    """
    global proxy
    if retry <= 0:
        return None
    headers = inbox_utils.get_headers('http://ehire.51job.com/Inbox/InboxRecentEngine.aspx?Style=1')
    headers['Cookie'] = account['cookies']
    proxy = common_utils.get_proxy()
    url = 'http://ehire.51job.com/Inbox/InboxRecentEngine.aspx?Style=1'
    r = common_utils.download(url=url, headers=headers, data=data, method='post', cookie=account['cookie'], proxy=proxy)

    if r.get('code') != 0:
        logger.error("列表页面返回不正常 %s" % r.get('data'))
        if r.get('data') and '<a href="/MainLogin.aspx?returl=' in r['data']:
            return 'login'
        proxy = common_utils.get_proxy()
        return refer_list_html(account, data, retry - 1)

    if '<a href="/MainLogin.aspx?returl=' in r['data']:
        return 'login'

    return r.get('data')


def start_one_job(account):
    """开启一个帐号的任务
    :account dict : 帐号,含有cookie
    """
    global proxy
    track_id = str(uuid.uuid1())
    url = "http://ehire.51job.com/Inbox/InboxRecentEngine.aspx?Style=1"
    refer_url = "http://ehire.51job.com/Navigate.aspx?ShowTips=11&PwdComplexity=N"
    proxy = common_utils.get_proxy()
    list_html = conn_html(account, url, 5, refer_url=refer_url, track_id=track_id)
    # list_html = open('text_htl').read()  # 测试
    while True:
        if list_html:
            if 'login' == list_html:
                # 需要登录
                logger.error("出现登录页面 %s" % account['userName'])
                return 'login'
            else:
                hidEngineCvlogIds = common_utils.find(
                    '<input name="hidEngineCvlogIds" type="hidden" id="hidEngineCvlogIds" value="(.*?)" />', list_html)
                __VIEWSTATE = common_utils.find(
                    '<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="(.*?)" />',
                    list_html)
                resume_ids = parse_list_html(list_html, track_id=track_id)
                if 'none' == resume_ids:
                    logger.info("邮箱没有邮件了--%s" % account['userName'])
                    return 'over'
                elif 'refer-login' == resume_ids:
                    logger.error("出现登录页面 %s" % account['userName'])
                    return 'login'

                if resume_ids:
                    ids_for = list(resume_ids)
                    logger.info('简历个数: %s' % len(resume_ids))
                    for id in ids_for:
                        info_url = 'http://ehire.51job.com/Candidate/ResumeViewFolder.aspx?hidSeqID=%s&hidFolder=EMP' % id
                        flag = info_main(account, info_url, track_id)
                        # flag = True
                        if 'login' == flag:
                            logger.error("出现登录页面 %s" % account['userName'])
                            return 'login'
                        if not flag:  # 失败?
                            resume_ids.remove(id)

                    # 测试
                    # resume_ids = ['9229836941', ]
                    data = get_refer_data(resume_ids, __VIEWSTATE, hidEngineCvlogIds)
                    # list_html = refer_list_html(account, data, 4)
                else:  # 解析失败
                    logger.error("页面 未能解析出简历%s" % account['userName'])
                    return 'error'
        else:  # 解析失败
            logger.error("出现错误页面 %s" % account['userName'])
            return 'error'


def get_account():
    """
    连接account模块获取该帐号的cookie
    :return: list: dict{ 帐号,名,公司密码,cookie}
    """
    account = [{
        'userName': '博纳聚荣',
        'accountName': 'bjgssdkj',
        'password': 'sjzx2017',
        'cookies': 'guid=14785878752608960054; EhireGuid=993f234463d34b81a3383e4ec5283fbe; ps=us%3DCjMAalU%252BV38HYwtgBn0GNAw6VmYGLlI2UGUGYlguUWAOMgZlUzdUawdgXzcFY1FqBjQCNlZgBWkFf1I5CkkPZwo7AA8%253D%26%7C%26; slife=lastvisit%3D020000%26%7C%26indexguide%3D1; search=jobarea%7E%60221300%7C%21ord_field%7E%600%7C%21recentSearch0%7E%601%A1%FB%A1%FA221300%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA1109%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA2%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1493002137%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch1%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2536%A1%FB%A1%FA00%A1%FB%A1%FA0%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506721%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch2%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2536%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506718%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch3%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2504%A1%FB%A1%FA00%A1%FB%A1%FA0%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506708%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch4%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2504%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506703%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21collapse_expansion%7E%601%7C%21; nsearch=jobarea%3D%26%7C%26ord_field%3D%26%7C%26recentSearch0%3D%26%7C%26recentSearch1%3D%26%7C%26recentSearch2%3D%26%7C%26recentSearch3%3D%26%7C%26recentSearch4%3D%26%7C%26collapse_expansion%3D; adv=adsnew%3D0%26%7C%26adsresume%3D1%26%7C%26adsfrom%3Dhttp%253A%252F%252Fbzclk.baidu.com%252Fadrc.php%253Ft%253D06KL00c00fAjOKR07edR00uiAs0mNG-m00000rRPIH300000I1hgBc.THYdnyGEm6K85yF9pywd0Znquj9BmyNBPHmsnj01PhcYnfKd5H6kfHuan1TYn1f1Pjm1fRfsrHPDnRc1wH9DPYDkrjbs0ADqI1YhUyPGujYzrjfsn1mYrHm4FMKzUvwGujYkP6K-5y9YIZ0lQzqYTh7Wui3dnyGEmB4WUvYEIZF9mvR8TA9s5v7bTv4dUHYLrjbzn1nhmyGs5y7cRWKWwAqvHjPbnvw4Pj7PNLKvyybdphcznZufn-G4mWcsrN-VwMKpi7uLuyTq5iuo5HK-nHRzPjfzuj9Bm1bdnARdrHuBm1fvnH-WuWbsuhuB0APzm1Ydrjc4n0%2526tpl%253Dtpl_10085_14394_1%2526l%253D1047858661%2526ie%253Dutf-8%2526f%253D3%2526tn%253Dbaidu%2526wd%253D51job%2526rqlang%253Dcn%2526prefixsug%253D51%2526rsp%253D3%2526inputT%253D3067%26%7C%26adsnum%3D789233; 51job=cenglish%3D0; ASP.NET_SessionId=cvswr5b4urvr4jsw0jk1jb3y; AccessKey=8fe582849c68410; HRUSERINFO=CtmID=3242550&DBID=3&MType=02&HRUID=3969707&UserAUTHORITY=1100111010&IsCtmLevle=0&UserName=bjgssdkj&IsStandard=1&LoginTime=04%2f25%2f2017+08%3a58%3a29&ExpireTime=04%2f25%2f2017+15%3a42%3a06&CtmAuthen=0000011000000001000111010000000011100011&BIsAgreed=true&IsResetPwd=0&CtmLiscense=3&AccessKey=73a7307138929556; LangType=Lang=&Flag=1'
    }]
    return account


def process(task):
    """
        根据一个搜索条件开始一项搜索
    """
    global logger
    logger = common_utils.get_logger()
    account_name = task['data'][0]['executeParam']

    result = {'code': 0}
    track_id = str(uuid.uuid1())
    date_time = task['data'][0]['deadline']
    account = inbox_utils.get_account(account_name)
    job_result = None
    try:
        job_result = start_one_job(account=account)
    except Exception, e:
        logger.error(str(traceback.format_exc()))
        pass

    if job_result:
        if 'error' == job_result:
            logger.error("本次任务执行失败失败: param =%s" % account_name)
            result['executeParam'] = account_name
            result['executeResult'] = 'inbox_error'
            result['deadline'] = int(time.mktime(time.strptime(date_time, '%Y-%m-%d %H:%M:%S'))) * 1000
            result['code'] = 1
            return result
        if 'over' == job_result:
            return result
        if 'login' == job_result:
            # cookie失效,不计算该帐号页数,重新调用登录,此任务失败处理
            inbox_utils.invalid_account(account)
            logger.error("本次任务执行失败失败: param =%s" % account_name)
            result['executeParam'] = account_name
            result['executeResult'] = 'to_login_error'
            result['deadline'] = int(time.mktime(time.strptime(date_time, '%Y-%m-%d %H:%M:%S'))) * 1000
            result['code'] = 1
            return result
    else:
        logger.error("本次任务执行失败失败: param =%s" % account_name)
        result['executeParam'] = account_name
        result['executeResult'] = 'inbox_error'
        result['deadline'] = int(time.mktime(time.strptime(date_time, '%Y-%m-%d %H:%M:%S'))) * 1000
        result['code'] = 1
        return result

# parse_list_html(open('test_html').read())
# account = {
#     'userName': '博纳聚荣',
#     'accountName': 'bjgssdkj',
#     'password': 'sjzx2017',
#     'cookies': 'guid=14785878752608960054; EhireGuid=993f234463d34b81a3383e4ec5283fbe; ps=us%3DCjMAalU%252BV38HYwtgBn0GNAw6VmYGLlI2UGUGYlguUWAOMgZlUzdUawdgXzcFY1FqBjQCNlZgBWkFf1I5CkkPZwo7AA8%253D%26%7C%26; slife=lastvisit%3D020000%26%7C%26indexguide%3D1; search=jobarea%7E%60221300%7C%21ord_field%7E%600%7C%21recentSearch0%7E%601%A1%FB%A1%FA221300%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA1109%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA2%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1493002137%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch1%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2536%A1%FB%A1%FA00%A1%FB%A1%FA0%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506721%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch2%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2536%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506718%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch3%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2504%A1%FB%A1%FA00%A1%FB%A1%FA0%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506708%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21recentSearch4%7E%601%A1%FB%A1%FA010000%2C00%A1%FB%A1%FA000000%A1%FB%A1%FA2504%A1%FB%A1%FA00%A1%FB%A1%FA9%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA99%A1%FB%A1%FA%A1%FB%A1%FA1%A1%FB%A1%FA%A1%FB%A1%FA-1%A1%FB%A1%FA1492506703%A1%FB%A1%FA0%A1%FB%A1%FA%A1%FB%A1%FA%7C%21collapse_expansion%7E%601%7C%21; nsearch=jobarea%3D%26%7C%26ord_field%3D%26%7C%26recentSearch0%3D%26%7C%26recentSearch1%3D%26%7C%26recentSearch2%3D%26%7C%26recentSearch3%3D%26%7C%26recentSearch4%3D%26%7C%26collapse_expansion%3D; adv=adsnew%3D0%26%7C%26adsresume%3D1%26%7C%26adsfrom%3Dhttp%253A%252F%252Fbzclk.baidu.com%252Fadrc.php%253Ft%253D06KL00c00fAjOKR07edR00uiAs0mNG-m00000rRPIH300000I1hgBc.THYdnyGEm6K85yF9pywd0Znquj9BmyNBPHmsnj01PhcYnfKd5H6kfHuan1TYn1f1Pjm1fRfsrHPDnRc1wH9DPYDkrjbs0ADqI1YhUyPGujYzrjfsn1mYrHm4FMKzUvwGujYkP6K-5y9YIZ0lQzqYTh7Wui3dnyGEmB4WUvYEIZF9mvR8TA9s5v7bTv4dUHYLrjbzn1nhmyGs5y7cRWKWwAqvHjPbnvw4Pj7PNLKvyybdphcznZufn-G4mWcsrN-VwMKpi7uLuyTq5iuo5HK-nHRzPjfzuj9Bm1bdnARdrHuBm1fvnH-WuWbsuhuB0APzm1Ydrjc4n0%2526tpl%253Dtpl_10085_14394_1%2526l%253D1047858661%2526ie%253Dutf-8%2526f%253D3%2526tn%253Dbaidu%2526wd%253D51job%2526rqlang%253Dcn%2526prefixsug%253D51%2526rsp%253D3%2526inputT%253D3067%26%7C%26adsnum%3D789233; 51job=cenglish%3D0; ASP.NET_SessionId=cvswr5b4urvr4jsw0jk1jb3y; HRUSERINFO=CtmID=3242550&DBID=3&MType=02&HRUID=3969707&UserAUTHORITY=1100111010&IsCtmLevle=0&UserName=bjgssdkj&IsStandard=1&LoginTime=04%2f25%2f2017+08%3a58%3a29&ExpireTime=04%2f25%2f2017+09%3a08%3a29&CtmAuthen=0000011000000001000111010000000011100011&BIsAgreed=true&IsResetPwd=0&CtmLiscense=3&AccessKey=73a7307138929556; AccessKey=8fe582849c68410; LangType=Lang=&Flag=1'
# }
# info_main(account, "http://ehire.51job.com/Candidate/ResumeViewFolder.aspx?hidSeqID=9182950999&hidFolder=EMP",
#           "test_track_id")
