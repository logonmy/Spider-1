# -*- coding: utf-8 -*-
import re

import lxml.html as xmlh
from pykafka import KafkaClient


def test_parse():
    html = open('html')
    hh = html.read()
    tree = xmlh.document_fromstring(hh)
    result = tree.xpath('//p[@class="comp_baseInfo_title"]/a')

    company_link = result[0]
    att = company_link.attrib.get('href')
    print company_link


def test_oss():
    pass


def kafka_consumer_test():
    """
    测试通过的kafka消费端
    :return:
    """
    client = KafkaClient(hosts="10.0.3.70:9092, 10.0.3.137:9092, 10.0.3.179:9092")
    topics = client.topics
    topic = topics['resume-pick']
    # consumer = topic.get_balanced_consumer(consumer_group='module-test', auto_commit_enable=True,
    #                                        zookeeper_connect='172.16.25.35:2121')
    consumer = topic.get_simple_consumer(consumer_group='group-morgan-test')
    for msg in consumer:
        print msg.value, msg.offset


kafka_consumer_test()
