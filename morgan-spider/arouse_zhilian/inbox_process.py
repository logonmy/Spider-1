#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25


# import ganji_jd
import json
import uuid
import requests
import datetime
import time
import traceback
from lxml import etree
import re
import sys

sys.path.append("../common")
import utils

import settings

logger = utils.get_logger

page_size = 20


def process(task):
    data = json.loads(task['data'][0]['executeParam'], encoding="utf-8")
    # flg = ganji_jd.parse_list(data)
    result = {'code': 0}
    # result = parse_list(data)
    # if not flg:
    #     result = {'code': 500}
    return result


def get_page(url, header):
    logger.info('get_page url %s' % url)
    for x in xrange(3):
        try:
            proxy = utils.get_proxy()
            logger.info('get_page[use proxy %s]' % proxy)
            session = requests.session()
            content = session.get(url, headers=header, proxies=proxy, timeout=10).content
            if content:
                logger.info('[the page use proxy %s] ' % proxy)
                if '验证码' in content or '机器人' in content:
                    logger.info('[the page needs input validate code %s]' % url)
                    return None
                else:
                    return {'content': content, 'proxy': proxy}
            else:
                logger.info('[request returns null page %s]' % url)
        except Exception as e:
            logger.error(str(traceback.format_exc()))

    return None


'''
程序入口
'''


def spider_search(data):
    cookie = data['cookie']
    user_name = data['userName']
    # 当前抓取的条目
    page_num = data['pageNum']
    # 最大的条目
    max_page = data['maxPage']
    inbox_url = 'http://rd2.zhaopin.com/RdApply/Resumes/Apply/index'
    header = {
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Host': 'rd2.zhaopin.com',
        'Referer': 'http://rd2.zhaopin.com/s/homepage.asp',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML:like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Cookie': cookie
    }
    page = get_page(inbox_url, header)['content']
    logger.info('first page accessed success %s ' % user_name)
    # 第一次请求的页面
    flg = parse_list(page, page_num, max_page, cookie)
    if flg:
        logger.info('parse next page begin %s ' % user_name)

        parse_next_page(cookie, page_num, max_page)


'''
访问下一页
'''


def parse_next_page(cookie, page_num, max_page):
    post_url = "http://rd2.zhaopin.com/rdapply/resumes/apply/search?SF_1_1_38=2,9&orderBy=CreateTime"
    params = {
        "PageList2": "",
        "DColumn_hidden": "",
        "searchKeyword": "",
        "curSubmitRecord": "1797",
        "curMaxPageNum": "90",
        "buttonAsse": "导入测评系统",
        "buttonInfo": "发通知信",
        "SF_1_1_50": "1",
        "SF_1_1_51": "-1",
        "SF_1_1_45": "",
        "SF_1_1_44": "",
        "SF_1_1_52": "0",
        "SF_1_1_49": "0",
        "IsInvited": "0",
        "position_city": "[%%POSITION_CITY%%]",
        "DColumn_hidden": "",
        "deptName": "",
        "select_unique_id": "",
        "selectedResumeList": "",
        "PageNo": "",
        "PosState": "",
        "MinRowID": "",
        "MaxRowID": "2722819791",
        "RowsCount": "123",
        "PagesCount": "5",
        "PageType": "0",
        "CurrentPageNum": page_num,
        "Position_IDs": "[%%POSITION_IDS%%]",
        "Position_ID": "[%%POSITION_ID%%]",
        "SortType": "0",
        "isCmpSum": "0",
        "SelectIndex_Opt": "0",
        "Resume_count": "0",
        "CID": "44036673",
        "forwardingEmailList": "",
        "click_search_op_type": "-1",
        " X-Requested-With": "XMLHttpRequest",
    }
    headers = {
        "Host": "rd2.zhaopin.com",
        "Accept": "*/*",
        "Origin": "http://rd2.zhaopin.com",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML:like Gecko) Chrome/52.0.2743.116 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://rd2.zhaopin.com/RdApply/Resumes/Apply/index",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Cookie": cookie,
    }
    session = requests.session();
    for x in xrange(3):
        proxy = utils.get_proxy()
        page = session.post(url=post_url, headers=headers, data=params, proxies=proxy, timeout=10).content
        parse_list(page, page_num, max_page, cookie)
    return False


'''
列表解析
'''


def parse_list(page, page_num, max_page, cookie):
    if page:
        tree = etree.HTML(page)
        table = tree.xpath('//div[@id="zpResumeListTable"]')
        if table:
            raws = table.xpath('//tr')
            logger.info('[%s] columns has bean found' % len(raws))
            if raws:
                for raw in raws and page_num <= max_page:
                    if '反馈通' in raw:
                        next_page_url = raw.xpath('//tr/td[3]/a[@href]')
                        print next_page_url
                        submit_time = raw.xpath('//tr/td[23]/text')
                        print submit_time
                        flg = parse_detail_page(next_page_url, submit_time, cookie)
                        if flg:
                            page_num += 1
                        else:
                            logger.error('parse detail page return false %s ' % next_page_url)
                return True
        else:
            logger.error('table zpResumeListTable has no column ')
    else:
        logger.error('page access failed ')
    return False


'''
访问详情页面
'''


def parse_detail_page(next_page_url, submit_time, cookie):
    # detail_page = session.get(url=next_page_url, , proxyes=utils.get_proxy()).content
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Referer': 'http://rd2.zhaopin.com/RdApply/Resumes/Apply/index',
        'Host': 'rd.zhaopin.com',
        'Cookie': cookie,
    }
    detail_page = get_page(next_page_url, header)['content']
    if '应聘机构' in detail_page:
        logger.info('detail page access success')
        trace_uuid = uuid.uuid4()
        sql = 'insert into resume_raw (source, content, createBy, trackId, createtime,  resumeSubmitTime,rdCreateTime) values ("ZHI_LIAN", %s, "python", %s, now(), %s,now())'
        sql_val = {'content': detail_page, 'trackId': trace_uuid,
                   'resumeSubmitTime': submit_time}
        kafka_data = {
            "channelType": "WEB",
            "content": {
                "content": detail_page,
                "id": '',
                "createBy": "python",
                "createTime": int(time.time() * 1000),
                "resumeSubmitTime": submit_time,
                "source": settings.project_settings['SOURCE'],
                "trackId": str(trace_uuid),
            },
            "interfaceType": "PARSE",
            "resourceDataType": "RAW",
            "resourceType": "RESUME_SEARCH",
            'protocolType': 'HTTP',
            "source": settings.project_settings['SOURCE'],
            "trackId": str(trace_uuid),
        }
        utils.save_data(sql, sql_val, kafka_data)
        logger.info('push success!')
        return True
    else:
        logger.error('detail page return error page \n %s' % detail_page)
        return False


if __name__ == '__main__':
    data = {
        'pageNum': 50,
        'userName': 'ykbc48066748',
        'password': 'sjzx2017',
        'cookie': 'rd_apply_lastsearchcondition=11%3B12%3B13%3B14%3B15%3B16; ylpop=1; urlfrom=121126445; urlfrom2=121126445; adfcid=none; adfcid2=none; adfbid=0; adfbid2=0; LastCity=%e5%8c%97%e4%ba%ac; LastCity%5Fid=530; dywez=95841923.1493964889.3.2.dywecsr=rd2.zhaopin.com|dyweccn=(referral)|dywecmd=referral|dywectr=undefined|dywecct=/s/homepage.asp; __utmt=1; Hm_lvt_38ba284938d5eddca645bb5e02a02006=1492606552,1492998591,1493003205,1493962350; Hm_lpvt_38ba284938d5eddca645bb5e02a02006=1493964890; JsOrglogin=2073713048; at=5bd34ffd06e9438e8f42a0d47870d5f3; Token=5bd34ffd06e9438e8f42a0d47870d5f3; rt=ab4cd65a04eb45a2a4729b4293f9c41d; uiioit=3D753D68496842645C380864416846795F745E745C650A395F732A753D68496840645D380964456843795F745C745C6503394; xychkcontr=48066748%2c0; lastchannelurl=https%3A//passport.zhaopin.com/org/login; __utma=269921210.2084991376.1493024019.1493962350.1493964889.3; __utmb=269921210.6.9.1493964905696; __utmc=269921210; __utmz=269921210.1493964889.3.2.utmcsr=rd2.zhaopin.com|utmccn=(referral)|utmcmd=referral|utmcct=/s/homepage.asp; NewPinUserInfo=; NewPinLoginInfo=; cgmark=2; JsNewlogin=691237682; RDpUserInfo=; isNewUser=1; ihrtkn=; utype=691237682; RDsUserInfo=236A2D6B566A5C64516958755772567346765C69536B586A5F6825693B654F650A711D6A0B6B086A5E64506959755372537346765E69536B516A316827694865A3F54871346A2D6B566A5E64506959755372537346765E69536B516A2668276948656536DF3FCF0F33382FE7293589260615B40BE51178113AFF073A92395F683D6938654F654871336A246B566A59645B695F755672557348765C695B6B5D6A52682969046503655D71156A066B066A51643B693D75587254734A762B693F6B576A51684469406552654271426A536B5A6A5E6453692D7521725873457652695B6B5C6A52685E6941654A654871326A276B566A7D37C427D0103F2121FE32278B26040BBB13E40A600E25F31E348B224D6A256B266A576458695975557254734A7629692F6B576A51685A69456549652671226A546B5A6A5A6459695275267224734C762969286B5E6A5C685969436544654471426A516B5D6A51642C6928755872267332765E69536B5A6A52685F69426546654B71406A526B2F6A2964556959755E72367338765769586B516A2D683969486540654771446A476B5A6A5B6459695275247229734C765A69506B2; dywea=95841923.2500264059289112000.1493024019.1493962350.1493964889.3; dywec=95841923; dyweb=95841923.7.9.1493964905693; getMessageCookie=1'}
    spider_search(data)
