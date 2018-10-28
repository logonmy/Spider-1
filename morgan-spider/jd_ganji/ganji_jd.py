# coding=utf-8
import requests
from lxml import etree
import re
import MySQLdb
import settings
import uuid
import datetime
import time
import traceback
sys.path.append("../common")
import utils


"""
@version: python2.7
@author: huangyee
@contact: 1173842904@qq.com
@software: PyCharm
@file: ganji_jd.py
@time: 2017/4/7 15:28
"""

'''
请求列表页面
'''


def get_page(url):
    utils.get_logger().info('get_page url %s' % url)
    for x in xrange(3):
        try:
            proxy = utils.get_proxy()
            utils.get_logger().error('get_page[use proxy %s]' % proxy)
            session = requests.session()
            content = session.get(url, headers={
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0(Windows NT 10.0; WOW64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                'Accept': 'text/html, application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
            }, proxies=proxy, timeout=10).content
            if content:
                utils.get_logger().info('[the page use proxy %s] ' % proxy)
                if '验证码' in content:
                    utils.get_logger().info('[the page needs input validate code %s]' % url)
                else:
                    return {'content': content, 'proxy': proxy}
            else:
                utils.get_logger().info('[request returns null page %s]' % url)
        except Exception as e:
            utils.get_logger().error(str(traceback.format_exc()))

    return None


'''
分页解析
'''


def parse_list(data):
    # 入口页面解析
    page_num = 1
    url = data['url']
    page = get_page(url)
    if not page:
        utils.get_logger().error('[entrance url request failed %s]' % url)
        return False
    content = page['content']
    parse_list_page(page_num, content, data)
    flg = False
    while flg:
        try:
            time.sleep(2)
            # print page
            ul_element = re.search('<ul class="pageLink clearfix">([\\s\\S]*?)</ul>', content)
            if ul_element:
                # print ul_element.group(1)
                next_page_url = re.search(
                    '<a class="c linkOn"><span>{0}</span></a></li><li><a href="([\\s\\S]*?)" >'.format(page_num),
                    ul_element.group(1))
                page_num += 1
                if next_page_url:
                    detail_page_url = 'http://bj.ganji.com' + next_page_url.group(1)
                    detail_page = get_page(detail_page_url)['content']
                    parse_list_page(page_num, detail_page, data=data)
                else:
                    utils.get_logger().error('[next_page_url not found %s]' % url)
            else:
                utils.get_logger().info('[no next page url was found %s]' % url)
                break
        except Exception as e:
            utils.get_logger().error(str(traceback.format_exc()))
            flg = False
    return flg


'''
列表页解析详情页面链接
'''


def parse_list_page(page_num, page, data):
    try:
        document = etree.HTML(page)
        list_div = document.xpath('//div[@class="new-dl-wrapper"]/div')
        if list_div:
            items = list_div[0].xpath('//dl[@class="list-noimg job-list clearfix new-dl"]')
            if items:
                utils.get_logger().info('there %s columns has bean found ' % len(items))
                page_index = 0
                for item in items:
                    time.sleep(2)
                    page_index += 1
                    detail_url = item.xpath('dt/a/@href')
                    if detail_url:
                        get_detail_page(page_index, page_num, detail_url[0], data['jobCity'].encode('utf-8'))
                    else:
                        utils.get_logger().error('[detail page url not found %s]' % item)
                        break
                    break
            else:
                utils.get_logger().error(
                    '[the page has no div with class attribute list-noimg job-list clearfix new-dl]')
        else:
            utils.get_logger().error('the page has no column table \n %s' % page)
    except Exception, e:
        utils.get_logger().error(str(traceback.format_exc()))


'''
请求详情页面
'''


def get_detail_page(page_index, page_num, page_url, city_name):
    content = get_page(page_url)
    if content and '验证码' not in content['content']:
        # print content
        save_db(page_index, page_num, content['content'], page_url, city_name, content['proxy'])
    else:
        utils.get_logger().error(
            '[the detail page  %s was not found ,or return an error page \n %s]' % (page_url, content))


'''
保存原文到数据库
'''


def save_db(page_index, page_num, page_content, page_url, city_name, proxy=None):
    # print page_content
    try:
        conn = MySQLdb.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PASSWD,
            db=settings.MYSQL_DB, charset='utf8',
        )
        cur = conn.cursor()
        cur.execute(
            'insert into jd_raw(trackId,source,content,createTime,createBy,ip,pageNum,pageIndex,pageUrl,jobCity)values(%s,"GJ_HR",%s,now(),"python",%s,%s,%s,%s,%s)',
            (
                uuid.uuid1(), page_content, proxy['http'].replace('http://', ''), page_num, page_index, page_url,
                city_name
            ))
        conn.commit()
        conn.close()
        utils.get_logger().info('save db success')
    except Exception:
        utils.get_logger().error('save db error \n %s' % page_content)
        utils.get_logger().error(str(traceback.format_exc()))

