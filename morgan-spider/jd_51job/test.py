# coding:utf8
import json
import uuid

import MySQLdb
import datetime
import oss2
import time

import requests
from pykafka import KafkaClient

import spider_utils

# result = spider_utils.trim(content)
# print result

# content = 'http://%s' % ('192.168.1.1:1100',)
# proxy = spider_utils.find('.*?(\d+\.\d+\.\d+\.\d+:\d+)', content)
# print proxy
from jd_51job.five_one_module import JdRaw, ResourceData

index = 0


def test_find():
    html = open('test_html').read()
    result = spider_utils.find(
        '投递时间：<span class="blue_txt">(.*?)</span>', html)

    if result:
        print result


# test_find()

def test_oss():
    """
    测试oss下载
    :return:
    """
    auth = oss2.Auth('LTAIa3y58SBV0Kyn', 'yBZcBKhQTgtf4cV55ljpnNCSk1XWaI')
    bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'ocr-img')
    oss_addr = 'spider/FIVE_EIGHT/JD_SEARCH/NEW/697c34e0-7222-11e7-b245-00163e036218.jpg'
    acl = bucket.get_object_to_file(oss_addr, 'aa.jpg')
    print acl


test_oss()


def sel():
    db = MySQLdb.connect("rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com", "spider_admin", "n4UZknFH6F", "spider",
                         charset='utf8')
    cursor = db.cursor()

    sql = "SELECT * FROM jd_raw where id in (43176613, 43176713, 43177485, 43182861, 43184172)"
    cursor.execute(sql)
    db.commit()
    jd_list = cursor.fetchall()
    list = []
    for jd in jd_list:
        raw = JdRaw()
        raw.id = jd[0]
        raw.source = jd[2].encode()
        raw.createTime = str(jd[8])
        raw.content = jd[3].encode()
        raw.createBy = jd[9].encode()
        raw.trackId = jd[1].encode()
        raw.pageUrl = jd[14].encode()
        raw.jobCity = jd[15].encode()
        raw.searchConditions = jd[18].encode()
        list.append(raw)
    return list


def send_kafka():
    list = sel()
    client = KafkaClient(hosts='172.16.25.35:19092')  # 可接受多个Client
    topics = client.topics
    print topics
    topic = client.topics['morgan-data-raw']
    producer = topic.get_producer()
    for raw in list:
        raw_data = json.dumps(raw, ensure_ascii=False, default=spider_utils.serialize_instance)
        data = ResourceData(raw.trackId, raw_data)
        kafka_data = json.dumps(data, ensure_ascii=False, default=spider_utils.serialize_instance)
        producer.produce(kafka_data)
        print '发送一条数据至kafka---'
        time.sleep(0.5)


# send_kafka()
import lxml.html as hxml


def check_proxy():
    global index
    print index
    url = 'http://jobs.51job.com/shanghai-pdxq/89978367.html?s=01&t=0'
    proxies_ = {'http': 'http://%s' % '180.115.15.14:48952', 'https': 'https://%s' % '180.115.15.14:48952'}
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "zh-CN,zh;q=0.8"
    }
    while True:
        try:
            get = requests.get(url, headers=headers, proxies=proxies_, timeout=8)
        except Exception as e:
            print e

        text = get.content
        tree = hxml.document_fromstring(text)

        xpaths = tree.xpath('//div[@class="cn"]/h1')
        if xpaths:
            index += 1
            print index
        else:
            print "页面不正常"
            print text


import logging



