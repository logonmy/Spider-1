# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DoctorItem(scrapy.Item):
    # 医生姓名
    name = scrapy.Field()
    # 医生级别
    level = scrapy.Field()
    # 工作单位
    company = scrapy.Field()
    # 擅长的领域
    good = scrapy.Field()
    # 回答答案
    detail = scrapy.Field()
    # 回答时间
    time = scrapy.Field()
    # 问题链接
    link = scrapy.Field()
