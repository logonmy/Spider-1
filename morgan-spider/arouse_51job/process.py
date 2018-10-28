#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import sys
import uuid

import datetime

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
"""
@version: python2.7
@author: 王增帅
@contact: 549409587@qq.com
@software: PyCharm
@file: process.py
@time: 2017/05/05 13:40
"""

import time
import lxml.html as xmlh
import utils
import arouse_utils

logger = None
proxy = None


def get_before_list_html(param, cookie, retry):
    """
    连接前置页面
    :param cookie:
    :return: html,
    """
    # global viewstate
    viewstate = go_to_search_html(cookie, retry)
    if 'login' == viewstate:
        return 'login'
    if viewstate:
        return go_to_list_html(param, cookie, viewstate, retry)
    else:
        return None


def go_to_list_html(param, cookie, viewstate, retry):
    global proxy
    logger.info('搜索前置页面-开始初始搜索------ %s' % retry)
    if retry <= 0:
        return None
    url = 'http://ehire.51job.com/Candidate/SearchResumeNew.aspx'
    # param = {"function_code": "0107", "functionName": "软件工程师", "region_code": "010000",
    #          "regionName": "北京"}
    data = arouse_utils.get_frist_post_headers(viewstate, param=param)

    logger.info(proxy)
    result = utils.download(url=url, data=data, proxy=proxy, cookie=cookie, method='post')
    if result['code'] != 0:
        logger.error("连接页面异常 ,重试: retry= %s" % retry)
        proxy = utils.get_proxy()
        return go_to_list_html(param, cookie, viewstate, retry - 1)
    elif '用户数不够' in result['data'] or len(result['data']) < 1000:
        logger.error("代理异常,重试: retry= %s" % retry)
        proxy = utils.get_proxy()
        return go_to_list_html(cookie, viewstate, retry - 1)
    if '您的操作过于频繁，请注意劳逸结合' in result['data']:
        return None
    return result['data']


def go_to_search_html(cookie, retry):
    global proxy
    if retry <= 0:
        return None
    logger.info('跳转搜索前置页面中------%s '% retry)
    url = 'http://ehire.51job.com/Candidate/SearchResumeIndexNew.aspx'
    headers = arouse_utils.get_get_headers('http://ehire.51job.com/Navigate.aspx')
    if not proxy:
        proxy = utils.get_proxy()
    logger.info(proxy)
    utils_download = utils.download(url=url, headers=headers, proxy=proxy, cookie=cookie)

    if utils_download['code'] != 0:
        logger.error('搜索页面出错:%s %s' % (url, retry))
        if utils_download.get('data') and '<a href="/MainLogin.aspx?returl=' in utils_download['data']:
            return 'login'
        proxy = utils.get_proxy()
        return go_to_search_html(cookie, retry - 1)

    if '<a href="/MainLogin.aspx?returl=' in utils_download['data']:
        return 'login'
    viewstate = arouse_utils.find('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="(.*?)" />',
                                  utils_download['data'])
    if not viewstate:
        proxy = utils.get_proxy()
        go_to_search_html(cookie, retry - 1)
    return viewstate


def parse_list_html(before_list_html):
    """
    解析出列表页面,并唤醒
    :param before_list_html:
    :return:
    """
    viewstate = None
    hidCheckUserIds = None
    hidCheckKey = None

    tree = xmlh.document_fromstring(before_list_html)
    try:
        viewstate = tree.xpath('//input[@id="__VIEWSTATE"]')[0].attrib.get("value")
        hidCheckUserIds = tree.xpath('//input[@id="hidCheckUserIds"]')[0].attrib.get("value")
        hidCheckKey = tree.xpath('//input[@id="hidCheckKey"]')[0].attrib.get("value")
    except:
        logger.error("搜索到的列表页面错误")
        return 'error'

    if '对不起，没有找到符合你条件的职位' in before_list_html or '抱歉，没有搜到您想找的简历' in before_list_html:
        return 'over'
    lines = tree.xpath('//tr[starts-with(@id, "trBaseInfo_")]')
    info_ids = []
    for line in lines:
        xpath_list = line.xpath('td/text()')
        info_time = None
        for text_ in xpath_list:
            info_time = arouse_utils.find("(\\d{4}-\\d{2}-\\d{2})", text_)
        three_day_ago = int(time.mktime((datetime.date.today() + datetime.timedelta(days=-3)).timetuple()))
        if not info_time:
            arouse_utils.resumeArouse(info_ids)
            return 'over'
        info_time = int(time.mktime(time.strptime(info_time, '%Y-%m-%d')))
        if info_time <= three_day_ago:
            arouse_utils.resumeArouse(info_ids)
            return 'over'
        else:
            try:
                info_id = line.xpath('td[@class="Common_list_table-id-text"]/span/a/text()')[0]
                info_ids.append(str(info_id))
            except:
                pass
    if info_ids:
        arouse_utils.resumeArouse(info_ids)
        return [viewstate, hidCheckUserIds, hidCheckKey]
    else:
        return 'over'


def get_post_data(param, parse_result):
    data = {
        '__EVENTTARGET': 'pagerBottomNew$nextButton',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': parse_result[0],
        'ctrlSerach$search_keyword_txt': '',
        'ctrlSerach$search_company_txt': '',
        'ctrlSerach$search_area_input': '',
        'ctrlSerach$search_area_hid': '',
        # 'ctrlSerach$btnSearch_submit': '',
        'ctrlSerach$search_funtype_hid': param.get('function_name', '') + "|" + param.get('function_code', ''),
        'ctrlSerach$search_expectsalaryf_input': '不限',
        'ctrlSerach$search_expectsalaryt_input': '不限',
        'ctrlSerach$search_industry_hid': '',
        'ctrlSerach$search_wyf_input': '不限',
        'ctrlSerach$search_wyt_input': '不限',
        'ctrlSerach$search_df_input': '大专',
        'ctrlSerach$search_dt_input': '及以上',
        'ctrlSerach$search_cursalaryf_input': '不限',
        'ctrlSerach$search_cursalaryt_input': '不限',
        'ctrlSerach$search_age_input': '年龄:20-30',
        'ctrlSerach$search_agef_input': '',
        'ctrlSerach$search_aget_input': '',
        'ctrlSerach$search_expjobarea_input': param.get('region_name', ''),
        'ctrlSerach$search_expjobarea_hid': param.get('region_name', '') + '|' + param.get('region_code', ''),
        'ctrlSerach$search_forlang_input': '语言',
        'ctrlSerach$search_fl_input': '不限',
        'ctrlSerach$search_fllsabilityll_input': '不限',
        'ctrlSerach$search_englishlevel_input': '英语等级',
        'ctrlSerach$search_sex_input': '性别',
        'ctrlSerach$search_major_input': '专业',
        'ctrlSerach$search_major_hid': '',
        'ctrlSerach$search_hukou_input': '户口',
        'ctrlSerach$search_hukou_hid': '',
        'ctrlSerach$search_rsmupdate_input': '近1周',
        'ctrlSerach$search_jobstatus_input': '求职状态',
        'send_cycle': '1',
        'send_time': '7',
        'send_sum': '10',
        'ctrlSerach$hidSearchValue': "##0#" + param.get('function_name', '') + '|' +
                                     param.get('function_code', '') + "###################近1周|1##1#0##" +
                                     param.get('region_name', '') + '|' + param.get('region_code', '') + "#0#0#0",
        'ctrlSerach$hidKeyWordMind': '',
        'ctrlSerach$hidRecommend': '#####',
        'ctrlSerach$hidWorkYearArea': '',
        'ctrlSerach$hidDegreeArea': '',
        'ctrlSerach$hidSalaryArea': '',
        'ctrlSerach$hidCurSalaryArea': '',
        'ctrlSerach$hidIsRecDisplay': '1',
        'showselected': '',
        'pagerTopNew$ctl06': '50',
        'cbxColumns$0': 'AGE',
        'cbxColumns$1': 'WORKYEAR',
        'cbxColumns$2': 'SEX',
        'cbxColumns$3': 'AREA',
        'cbxColumns$5': 'TOPDEGREE',
        'cbxColumns$6': 'LASTUPDATE',
        'cbxColumns$4': 'WORKFUNC',
        'hidDisplayType': '0',
        'hidEhireDemo': '',
        'hidUserID': '',
        'hidCheckUserIds': parse_result[1],
        'hidCheckKey': parse_result[2],
        'hidEvents': '',
        'hidNoSearchIDs': '',
        'hidBtnType': '',
        'hidKeywordCookie': '',
        'showGuide': '',
        'hideMarkid': '',
        'hidStrAuthority': '0',
        'hidShowCode': '0',
    }
    return data


def next_html(account_cookies, data, retry):
    logger.info('开始进行下一页 %s %s'% (account_cookies.get('userName', ''), retry,))
    global proxy
    if retry <= 0:
        return None
    cookie = account_cookies.get('cookie')
    headers = arouse_utils.get_get_headers()
    url = 'http://ehire.51job.com/Candidate/SearchResumeNew.aspx'
    logger.info(proxy)

    result = utils.download(url=url, data=data, proxy=proxy, cookie=cookie, headers=headers, method='post')

    if result['code'] != 0:
        logger.error("连接页面异常 ,重试: retry= %s" % retry)
        proxy = utils.get_proxy()
        return next_html(cookie, data, retry - 1)
    elif '用户数不够' in result['data'] or len(result['data']) < 1000:
        logger.error("代理异常,重试: retry= %s" % retry)
        proxy = utils.get_proxy()
        return next_html(cookie, data, retry - 1)
    if '您的操作过于频繁，请注意劳逸结合' in result['data']:
        return None
    return result['data']


def start_one_task(param, date_time):
    """
    开始一个搜索任务
    :param account_cookies:含有cookie的帐号
    :param param: 搜索任务参数
    :return: 任务执行结果
    """
    account_cookies = arouse_utils.get_one_cookies(param.get('userName'))
    if not account_cookies:
        return 'error'
    # task_count = arouse_utils.redis_get(redis_key)

    cookie = account_cookies.get('cookie')
    list_html = get_before_list_html(param, cookie, 5)
    task_count = 0
    page_num = param.get('page_num')
    while True:

        if not list_html:
            #  任务失败,
            return 'error'
        if list_html == 'login':
            # cookie失效,不计算该帐号页数,重新调用登录,此任务失败处理
            arouse_utils.invalid_account(account_cookies)
            return 'error'

        parse_result = parse_list_html(list_html)

        if 'error' == parse_result:
            #  任务失败,
            return 'error'

        if 'over' == parse_result:
            #  任务完成 or 帐号到达限制次数了
            return 'over'
        else:
            # task_count = arouse_utils.redis_incr(redis_key)
            # if task_count >= page_num - 1:
            #     arouse_utils.redis_delete(redis_key)
            #     return 'over'
            data = get_post_data(param, parse_result)
            list_html = next_html(account_cookies, data, 3)


def process(task):
    """
        根据一个搜索条件开始一项搜索
        :return:
    """
    global logger
    logger = utils.get_logger()
    logger.info("开始一个任务的执行 参数: %s"% task['data'][0]['executeParam'].encode())
    param = json.loads(task['data'][0]['executeParam'], encoding="utf-8")

    result = {'code': 0}
    track_id = str(uuid.uuid1())
    date_time = task['data'][0]['deadline']
    task_result = start_one_task(param, date_time)
    logger.info('本次任务执行完毕 结果 :%s' % task_result)
    if 'over' == task_result:
        return result
    if 'error' == task_result:
        logger.error("本次任务执行失败失败: param =%s" % str(param))
        result['executeParam'] = json.dumps(param, ensure_ascii=False)
        result['executeResult'] = 'list_html_error'
        result['deadline'] = int(time.mktime(time.strptime(date_time, '%Y-%m-%d %H:%M:%S'))) * 1000
        result['code'] = 1
        return result


# parse_list_html(open("list_html").read())